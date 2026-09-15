"""Tests for the one model factory (LG-016): `lango.llm.build_chat_model`.

The factory calls `enforce_privacy()` itself. Most tests below replace that call with a no-op, so
they prove the factory pins the endpoint, key, and proxy *on its own*, even if a hostile env var
slipped past the guard.
"""

import anthropic
import langsmith
import pytest
from langchain_anthropic import ChatAnthropic

from conftest import NetworkCanary
from lango.config import ANTHROPIC_BASE_URL, Settings
from lango.llm import build_chat_model

FAKE_KEY = "sk-ant-test-0000"  # matches `hostile_env` in conftest.py


@pytest.fixture
def settings(
    hostile_env: dict[str, str],  # noqa: ARG001 - requested for its env vars
    monkeypatch: pytest.MonkeyPatch,
) -> Settings:
    monkeypatch.setenv("ANTHROPIC_PROXY", "http://proxy.invalid.example:8080")
    # Disable the guard inside the factory so the hostile env stays in place for these tests.
    monkeypatch.setattr("lango.llm.enforce_privacy", lambda: [])
    return Settings()


def test_model_uses_the_pinned_anthropic_url_despite_hostile_env(settings: Settings) -> None:
    model = build_chat_model(settings)

    assert isinstance(model, ChatAnthropic)
    assert model.anthropic_api_url == ANTHROPIC_BASE_URL == "https://api.anthropic.com"


def test_model_ignores_anthropic_proxy_env_var(settings: Settings) -> None:
    model = build_chat_model(settings)

    assert model.anthropic_proxy is None


def test_factory_runs_the_privacy_guard(
    hostile_env: dict[str, str],  # noqa: ARG001 - requested for its env vars
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: record calls instead of disabling the guard.
    calls: list[str] = []
    monkeypatch.setattr("lango.llm.enforce_privacy", lambda: calls.append("called") or [])

    # Act
    build_chat_model(Settings())

    # Assert: a model built outside the FastAPI lifespan is still guarded.
    assert calls == ["called"]


def test_model_takes_api_key_and_model_name_from_settings(settings: Settings) -> None:
    model = build_chat_model(settings)

    assert model.anthropic_api_key.get_secret_value() == FAKE_KEY
    assert model.model == settings.model


def test_retries_and_timeout_are_passed_through(settings: Settings) -> None:
    model = build_chat_model(settings, max_retries=0, timeout=5.0)

    assert model.max_retries == 0
    assert model.default_request_timeout == 5.0


def test_sync_request_only_tries_to_reach_api_anthropic_com(
    settings: Settings, network_canary: NetworkCanary
) -> None:
    # Arrange: hostile env has LANGSMITH_GATEWAY=true and ANTHROPIC_BASE_URL=proxy.invalid.example.
    model = build_chat_model(settings, max_retries=0)

    # Act: the canary blocks the socket, so the request fails fast with a connection error.
    # Tracing is switched off here only so this test isolates *model routing*; tracing is
    # covered by test_privacy.py and test_network_canary.py.
    with langsmith.tracing_context(enabled=False), pytest.raises(anthropic.APIConnectionError):
        model.invoke("placeholder text")

    # Assert
    assert network_canary.attempts, "expected a (blocked) connection attempt"
    assert network_canary.hosts == {"api.anthropic.com"}


@pytest.mark.asyncio
async def test_async_request_only_tries_to_reach_api_anthropic_com(
    settings: Settings, network_canary: NetworkCanary
) -> None:
    model = build_chat_model(settings, max_retries=0)

    with langsmith.tracing_context(enabled=False), pytest.raises(anthropic.APIConnectionError):
        await model.ainvoke("placeholder text")

    assert network_canary.attempts, "expected a (blocked) connection attempt"
    assert network_canary.hosts == {"api.anthropic.com"}
