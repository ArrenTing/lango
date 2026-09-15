"""Tests for the startup privacy guard (LG-016): `lango.privacy.enforce_privacy`."""

import logging
import os
import sys

import langsmith.utils
import pytest

from lango import privacy
from lango.privacy import BLOCKED_ENV_VARS, PrivacyError, enforce_privacy

REQUIRED_BLOCKED_ENV_VARS = frozenset(
    {
        "LANGSMITH_TRACING",
        "LANGSMITH_TRACING_V2",
        "LANGCHAIN_TRACING",
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_API_KEY",
        "LANGCHAIN_API_KEY",
        "LANGSMITH_ENDPOINT",
        "LANGCHAIN_ENDPOINT",
        "LANGSMITH_RUNS_ENDPOINTS",
        "LANGSMITH_OTEL_ENABLED",
        "LANGSMITH_GATEWAY",
        "LANGSMITH_GATEWAY_API_KEY",
        "ANTHROPIC_API_URL",
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_PROXY",
        "ANTHROPIC_CUSTOM_HEADERS",
        "ANTHROPIC_LOG",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "SSLKEYLOGFILE",
    }
)

ON_WINDOWS = sys.platform == "win32"


def test_blocked_list_covers_every_tracing_endpoint_gateway_and_routing_var() -> None:
    missing = REQUIRED_BLOCKED_ENV_VARS - BLOCKED_ENV_VARS
    assert not missing, f"BLOCKED_ENV_VARS is missing: {sorted(missing)}"


@pytest.mark.parametrize("logger_name", ["anthropic", "httpx", "httpcore"])
def test_sdk_debug_logging_is_turned_back_off(logger_name: str) -> None:
    # Arrange: ANTHROPIC_LOG=debug sets this at import time, before startup can strip the env var.
    # At DEBUG, the Anthropic SDK logs full request bodies, i.e. conversation text.
    logger = logging.getLogger(logger_name)
    original = logger.level
    logger.setLevel(logging.DEBUG)
    try:
        # Act
        enforce_privacy()

        # Assert
        assert logger.getEffectiveLevel() > logging.DEBUG
    finally:
        logger.setLevel(original)


def test_blocked_list_never_includes_the_anthropic_api_key() -> None:
    # Removing the key would stop lango from working; it's a secret, not a routing switch.
    assert "ANTHROPIC_API_KEY" not in BLOCKED_ENV_VARS


# ── Removing env vars ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "name",
    [
        "LANGSMITH_TRACING",
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_API_KEY",
        "LANGSMITH_ENDPOINT",
        "LANGSMITH_GATEWAY",
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_PROXY",
        pytest.param(
            "langsmith_tracing",
            marks=pytest.mark.skipif(
                ON_WINDOWS,
                reason="Windows env var names are case-insensitive, so lowercase is the same var",
            ),
        ),
    ],
)
def test_blocked_env_var_is_removed_and_its_name_returned(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    # Arrange
    monkeypatch.setenv(name, "placeholder-value")

    # Act
    removed = enforce_privacy()

    # Assert
    assert removed == [name]
    assert name not in os.environ


def test_several_removed_names_are_returned_sorted(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LANGSMITH_TRACING", "ANTHROPIC_BASE_URL", "LANGSMITH_GATEWAY"):
        monkeypatch.setenv(name, "true")

    removed = enforce_privacy()

    assert removed == ["ANTHROPIC_BASE_URL", "LANGSMITH_GATEWAY", "LANGSMITH_TRACING"]


def test_anthropic_api_key_and_lango_settings_are_left_alone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-0000")
    monkeypatch.setenv("LANGO_MODEL", "claude-haiku-4-5-20251001")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")

    enforce_privacy()

    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-test-0000"
    assert os.environ["LANGO_MODEL"] == "claude-haiku-4-5-20251001"


def test_nothing_to_remove_returns_empty_list_and_logs_nothing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange: `known_baseline` (conftest.py) already removed every blocked var.
    caplog.set_level(logging.WARNING, logger="lango.privacy")

    # Act
    removed = enforce_privacy()

    # Assert
    assert removed == []
    assert [r for r in caplog.records if r.name == "lango.privacy"] == []


# ── Logging names, never values ─────────────────────────────────────────────


def test_removed_names_are_logged_as_a_warning_but_values_never_are(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    # Arrange: values that look like secrets, each containing a canary we can search for.
    canary = "VALUE-canary-7f3a"
    monkeypatch.setenv("LANGSMITH_API_KEY", f"lsv2_fake_{canary}")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", f"https://{canary}.invalid.example")
    caplog.set_level(logging.DEBUG, logger="lango.privacy")

    # Act
    enforce_privacy()

    # Assert
    warnings = [
        r for r in caplog.records if r.name == "lango.privacy" and r.levelno == logging.WARNING
    ]
    assert warnings, "expected a WARNING from lango.privacy naming the removed env vars"
    logged = "\n".join(r.getMessage() for r in warnings)
    assert "LANGSMITH_API_KEY" in logged
    assert "ANTHROPIC_BASE_URL" in logged
    assert canary not in caplog.text, "an env var VALUE was logged; log names only"
    assert canary not in logged


# ── Tracing is forced off ───────────────────────────────────────────────────


@pytest.mark.usefixtures("hostile_env")
def test_tracing_is_off_after_enforcing_privacy_under_hostile_env() -> None:
    enforce_privacy()

    assert not langsmith.utils.tracing_is_enabled()


def test_raises_privacy_error_when_tracing_is_still_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: pretend something keeps tracing on despite configure(enabled=False).
    # Assumption: privacy.py calls either `langsmith.utils.tracing_is_enabled()` (module
    # attribute, patched below) or a name it imported with `from langsmith.utils import
    # tracing_is_enabled` (patched on `lango.privacy` itself). Both are covered.
    def always_on(*_args: object, **_kwargs: object) -> bool:
        return True

    monkeypatch.setattr(langsmith.utils, "tracing_is_enabled", always_on)
    monkeypatch.setattr(privacy, "tracing_is_enabled", always_on, raising=False)

    # Act / Assert
    with pytest.raises(PrivacyError):
        enforce_privacy()


def test_privacy_error_is_a_runtime_error_so_it_survives_python_dash_o() -> None:
    # `assert` statements vanish under `python -O`; a real exception does not.
    assert issubclass(PrivacyError, RuntimeError)


def test_enforcing_privacy_twice_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "true")

    first = enforce_privacy()
    second = enforce_privacy()

    assert first == ["LANGSMITH_TRACING"]
    assert second == []
    assert not langsmith.utils.tracing_is_enabled()
