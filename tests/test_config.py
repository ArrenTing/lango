import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from lango.config import (
    ANTHROPIC_BASE_URL,
    Settings,
    SettingsError,
    get_settings,
    load_settings,
)

FAKE_KEY = "sk-ant-test-0000"


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    for name in list(os.environ):
        if name.startswith("LANGO_"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def valid_key(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    return FAKE_KEY


def test_valid_env_loads_settings_with_secret_key_and_defaults(valid_key: str) -> None:
    settings = Settings()
    assert isinstance(settings.anthropic_api_key, SecretStr)
    assert settings.anthropic_api_key.get_secret_value() == valid_key
    assert valid_key not in str(settings), "the API key must not appear when settings are printed"
    assert valid_key not in repr(settings), "the API key must not appear in repr (e.g. in logs)"

    assert settings.model == "claude-sonnet-5"
    assert settings.my_language == "en"
    assert settings.their_language == "vi"


@pytest.mark.usefixtures("valid_key")
def test_haiku_model_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGO_MODEL", "claude-haiku-4-5-20251001")
    settings = Settings()
    assert settings.model == "claude-haiku-4-5-20251001"


def test_env_file_in_working_directory_is_read(tmp_path: Path) -> None:
    # Arrange: no env vars are set (see `isolated_env`); the values exist only in a .env file
    # inside the temp folder we are running from.
    env_file = tmp_path / ".env"
    env_file.write_text(
        "ANTHROPIC_API_KEY=sk-ant-test-from-dotenv\nLANGO_MODEL=claude-haiku-4-5-20251001\n",
        encoding="utf-8",
    )
    assert "ANTHROPIC_API_KEY" not in os.environ

    # Act
    settings = Settings()

    # Assert
    assert settings.anthropic_api_key.get_secret_value() == "sk-ant-test-from-dotenv"
    assert settings.model == "claude-haiku-4-5-20251001"


# ── Failing fast on bad input ───────────────────────────────────────────────


def test_missing_api_key_raises_validation_error_naming_the_key() -> None:

    # Act
    with pytest.raises(ValidationError) as exc_info:
        Settings()

    # Assert: the error points at the API key, so the fix is obvious.
    error_locations = [
        str(part).lower() for error in exc_info.value.errors() for part in error["loc"]
    ]
    assert "anthropic_api_key" in error_locations


def test_malformed_api_key_is_rejected_without_leaking_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: a key that doesn't start with "sk-ant-", containing a canary we can search for.
    canary = "SECRET-canary-123"
    monkeypatch.setenv("ANTHROPIC_API_KEY", f"not-a-real-key-{canary}")

    # Act
    with pytest.raises(ValidationError) as exc_info:
        Settings()

    # Assert
    assert canary not in str(exc_info.value), (
        "The rejected key leaked into the error message. Startup errors end up in terminals, "
        "logs, and CI output, so a real key typed slightly wrong would be exposed. "
        "Check `hide_input_in_errors=True` in model_config and that the validator's "
        "message doesn't include the value."
    )


def test_key_that_is_only_the_prefix_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-")

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.usefixtures("valid_key")
def test_unsupported_model_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGO_MODEL", "gpt-4o")

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.usefixtures("valid_key")
def test_unsupported_language_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGO_THEIR_LANGUAGE", "fr")

    with pytest.raises(ValidationError):
        Settings()


# ── The Anthropic endpoint is pinned in code ────────────────────────────────


@pytest.mark.usefixtures("valid_key")
def test_anthropic_base_url_env_var_cannot_reroute_traffic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://proxy.invalid.example")

    # Act
    settings = Settings()

    assert ANTHROPIC_BASE_URL == "https://api.anthropic.com"
    assert "anthropic_base_url" not in Settings.model_fields
    assert not [name for name in Settings.model_fields if "url" in name.lower()]
    assert "proxy.invalid.example" not in repr(settings)


# ── One shared instance ─────────────────────────────────────────────────────


@pytest.mark.usefixtures("valid_key")
def test_get_settings_returns_the_same_cached_object() -> None:
    first = get_settings()
    second = get_settings()

    assert first is second


# ── load_settings: key-free startup errors (LG-016) ─────────────────────────


@pytest.mark.usefixtures("valid_key")
def test_load_settings_returns_settings_for_a_valid_env() -> None:
    settings = load_settings()

    assert isinstance(settings, Settings)
    assert settings.anthropic_api_key.get_secret_value() == FAKE_KEY


def test_load_settings_error_names_the_key_but_never_contains_its_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: a malformed key containing a canary. pydantic's `exc.errors()` still includes the
    # input (LG-003 security note), so load_settings must build its message without it.
    canary = "SECRET-canary-456"
    monkeypatch.setenv("ANTHROPIC_API_KEY", f"not-a-real-key-{canary}")

    # Act
    with pytest.raises(SettingsError) as exc_info:
        load_settings()

    # Assert: the message is useful...
    error = exc_info.value
    assert "anthropic_api_key" in str(error).lower()
    # ...and the key can't leak through the message, repr, args, or a chained ValidationError.
    assert canary not in str(error)
    assert canary not in repr(error)
    assert all(canary not in str(arg) for arg in error.args)
    assert error.__cause__ is None
    assert error.__context__ is None, (
        "the original ValidationError is still attached as __context__, and its .errors() "
        "contains the raw key; raise SettingsError outside the except block"
    )


def test_load_settings_error_for_missing_key_is_a_settings_error() -> None:
    with pytest.raises(SettingsError):
        load_settings()
