"""Startup privacy guard (LG-016).

LG-002 found that LangGraph/LangChain stay quiet by default, but a single stray env var
(`LANGSMITH_TRACING=true`, `LANGSMITH_GATEWAY=true`, `ANTHROPIC_BASE_URL=...`) would send
conversations to LangSmith or reroute model traffic. `enforce_privacy()` locks those doors in
code at startup instead of trusting `.env`: it strips the risky env vars, turns LangSmith
tracing off globally, and fails loudly if tracing is somehow still on.
"""

import logging
import os
from typing import Final

import langsmith
import langsmith.utils

logger = logging.getLogger(__name__)


class PrivacyError(RuntimeError):
    """Startup could not guarantee that conversation data stays private."""


BLOCKED_ENV_VARS: Final[frozenset[str]] = frozenset(
    {
        # LangSmith tracing switches
        "LANGSMITH_TRACING",
        "LANGSMITH_TRACING_V2",
        "LANGCHAIN_TRACING",
        "LANGCHAIN_TRACING_V2",
        # LangSmith credentials and endpoints
        "LANGSMITH_API_KEY",
        "LANGCHAIN_API_KEY",
        "LANGSMITH_ENDPOINT",
        "LANGCHAIN_ENDPOINT",
        "LANGSMITH_RUNS_ENDPOINTS",
        # langsmith reads RUNS_ENDPOINTS / OTEL_* / TRACING_MODE from both namespaces
        "LANGCHAIN_RUNS_ENDPOINTS",
        # OpenTelemetry export paths for traces
        "LANGSMITH_OTEL_ENABLED",
        "LANGCHAIN_OTEL_ENABLED",
        "LANGSMITH_OTEL_ONLY",
        "LANGCHAIN_OTEL_ONLY",
        "LANGSMITH_TRACING_MODE",
        "LANGCHAIN_TRACING_MODE",
        # LangSmith LLM gateway (reroutes model calls through LangChain's servers)
        "LANGSMITH_GATEWAY",
        "LANGSMITH_GATEWAY_API_KEY",
        # Anthropic routing
        "ANTHROPIC_API_URL",
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_PROXY",
        "ANTHROPIC_CUSTOM_HEADERS",
        # Anthropic SDK debug logging dumps full request bodies (conversation text) to stderr
        "ANTHROPIC_LOG",
        # HTTP transport: a proxy plus a custom CA bundle (or TLS key log) would expose traffic.
        # OS-level proxies (Windows registry, macOS settings) can't be stripped here; see LG-008.
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "SSLKEYLOGFILE",
    }
)

# Loggers that ANTHROPIC_LOG=debug switches on at import time (before startup runs). At DEBUG they
# log request options, including message bodies, so they're forced back above DEBUG.
_SDK_LOGGERS: Final[tuple[str, ...]] = ("anthropic", "httpx", "httpx2", "httpcore", "httpcore2")

# lru_caches that remember env reads; cleared so a var removed above can't linger.
_ENV_CACHES: Final[tuple[str, ...]] = ("get_env_var", "get_tracer_project")


def _remove_blocked_env_vars() -> list[str]:
    """Delete blocked vars from `os.environ`, matching names case-insensitively."""
    removed = [name for name in list(os.environ) if name.upper() in BLOCKED_ENV_VARS]
    for name in removed:
        os.environ.pop(name, None)
    return sorted(removed)


def _clear_env_caches() -> None:
    """Clear langsmith's cached env lookups, skipping any that don't exist in this version."""
    for attr in _ENV_CACHES:
        cache_clear = getattr(getattr(langsmith.utils, attr, None), "cache_clear", None)
        if callable(cache_clear):
            cache_clear()


def enforce_privacy() -> list[str]:
    """Strip tracing/routing env vars and force LangSmith tracing off.

    Safe to call many times. Logs only the *names* of removed vars, never their values.

    Returns:
        The sorted names of the env vars that were removed, as they appeared in the environment.

    Raises:
        PrivacyError: If LangSmith still reports tracing as enabled afterwards.
    """
    removed = _remove_blocked_env_vars()
    langsmith.configure(enabled=False)
    _clear_env_caches()
    for name in _SDK_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    if langsmith.utils.tracing_is_enabled():
        raise PrivacyError("LangSmith tracing is still enabled after enforce_privacy()")

    if removed:
        logger.warning("Removed privacy-sensitive env vars: %s", ", ".join(removed))
    return removed
