"""Shared test fixtures for lango.

Two fixtures matter for privacy work (LG-016) and are meant to be reused from LG-004 onwards:

- `network_canary`: blocks and records every outbound connection attempt, so a test can prove
  that nothing tried to leave the machine (or that the only destination was the Anthropic API).
- `hostile_env`: sets the env vars that would send data to LangSmith or reroute model traffic,
  so a test can prove lango ignores them.

An autouse fixture (`known_baseline`) also runs for every test so they start from the same state
no matter what order they run in or what is set in the developer's shell.
"""

import asyncio
import ipaddress
import os
import socket
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import langsmith
import langsmith.utils
import pytest

from lango.config import get_settings

CANARY_MESSAGE = "network blocked by lango test canary"

# Mirrors the LG-002 "Enforcement rules" list. It is duplicated here on purpose: conftest must not
# import `lango.privacy`, so every other test still runs if that module is broken.
TRACING_AND_ROUTING_ENV_VARS = (
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
    "LANGSMITH_PROJECT",
    "LANGCHAIN_PROJECT",
    "ANTHROPIC_API_URL",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_PROXY",
    "ANTHROPIC_CUSTOM_HEADERS",
    "ANTHROPIC_LOG",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "SSLKEYLOGFILE",
    # A proxy from the developer's shell would change which host httpx connects to first.
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)

HOSTILE_ENV: dict[str, str] = {
    "LANGSMITH_TRACING": "true",
    "LANGCHAIN_TRACING_V2": "true",
    "LANGSMITH_API_KEY": "lsv2_fake",
    "LANGSMITH_GATEWAY": "true",
    "ANTHROPIC_BASE_URL": "https://proxy.invalid.example",
    "ANTHROPIC_API_KEY": "sk-ant-test-0000",
}


# ── Known starting state ────────────────────────────────────────────────────


def reset_langsmith_state() -> None:
    """Put LangSmith back to "decide from env vars", as if nothing had configured it.

    `enforce_privacy()` calls `langsmith.configure(enabled=False)`, which sets a process-wide
    global and a context var. `configure(enabled=None)` clears both (langsmith 0.12.5,
    `run_trees.py` `configure`). `get_env_var` is `lru_cache`d (`utils.py:418`), so a value read
    while one test had `LANGSMITH_TRACING=true` would otherwise leak into the next test.
    """
    langsmith.configure(enabled=None)
    langsmith.utils.get_env_var.cache_clear()


@pytest.fixture(autouse=True)
def known_baseline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Every test: no tracing/routing env vars, no real `.env`, fresh settings + LangSmith state."""
    blocked = {name.upper() for name in TRACING_AND_ROUTING_ENV_VARS}
    for name in list(os.environ):  # case-insensitive, so a lowercase shell var is removed too
        if name.upper() in blocked:
            monkeypatch.delenv(name, raising=False)
    # Settings read `.env` from the working directory; a temp dir keeps the real one unreadable.
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    reset_langsmith_state()
    yield
    reset_langsmith_state()
    get_settings.cache_clear()


@pytest.fixture
def hostile_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Set env vars that would leak data to LangSmith or reroute the model, plus a fake API key.

    - `LANGSMITH_TRACING` / `LANGCHAIN_TRACING_V2`: send every run's inputs/outputs to LangSmith.
    - `LANGSMITH_GATEWAY` + `LANGSMITH_API_KEY`: send model requests via LangChain's proxy.
    - `ANTHROPIC_BASE_URL`: send the model request to another host.

    `ANTHROPIC_API_KEY` is a fake, correctly shaped key so `Settings` loads. Returns the values set.
    """
    for name, value in HOSTILE_ENV.items():
        monkeypatch.setenv(name, value)
    return dict(HOSTILE_ENV)


# ── Network canary ──────────────────────────────────────────────────────────


@dataclass
class NetworkCanary:
    """What the `network_canary` fixture hands to a test.

    `attempts` lists every blocked attempt as `(host, port)`, in order. `port` is `None` when the
    call didn't include one (e.g. `getaddrinfo(host, None)`). Hosts are what the caller asked
    for, usually a DNS name such as `"api.anthropic.com"`, sometimes an IP address.
    """

    attempts: list[tuple[str, int | None]] = field(default_factory=list)

    @property
    def hosts(self) -> set[str]:
        """The distinct hosts something tried to reach."""
        return {host for host, _port in self.attempts}

    def record_and_block(self, host: object, port: object) -> OSError:
        """Record one attempt and return the error the patched function should raise."""
        self.attempts.append((_as_host(host), _as_port(port)))
        return OSError(CANARY_MESSAGE)


def _as_host(host: object) -> str:
    if isinstance(host, bytes):
        return host.decode("ascii", errors="replace")
    return str(host)


def _as_port(port: object) -> int | None:
    if port is None:
        return None
    try:
        return int(str(port))
    except ValueError:  # a service name such as "https"
        return None


def _split_address(address: Any) -> tuple[object, object]:
    """Split an AF_INET/AF_INET6 `(host, port, ...)` tuple; anything else is treated as the host."""
    if isinstance(address, tuple) and len(address) >= 2:
        return address[0], address[1]
    return address, None


def _is_loopback_ip(host: object) -> bool:
    try:
        return ipaddress.ip_address(_as_host(host)).is_loopback
    except ValueError:
        return False


@pytest.fixture
def network_canary(monkeypatch: pytest.MonkeyPatch) -> NetworkCanary:
    """Block all outbound network access for one test and record what tried to connect.

    Every patched function records `(host, port)` in `canary.attempts` and raises
    `OSError("network blocked by lango test canary")`. HTTP clients turn that into their own
    connection error (e.g. `anthropic.APIConnectionError`), so code under test fails fast instead
    of reaching the internet.

    Patched (checked against httpx/httpcore, anyio, urllib3/requests and asyncio on Python 3.14):

    - `socket.getaddrinfo`: DNS lookup. urllib3 (LangSmith client), anyio (async httpx) and
      `asyncio` loops (via their executor) all resolve names through it, so this is usually
      where an attempt is caught.
    - `socket.create_connection`: sync httpx/httpcore connects through it.
    - `socket.socket.connect` / `connect_ex`: raw sockets that skip the helpers above.
    - `asyncio.BaseEventLoop.getaddrinfo` / `create_connection`: async paths. On Windows the
      proactor loop connects with `ConnectEx`, which never calls `socket.socket.connect`.

    Exception: `connect`/`connect_ex` to a loopback **IP literal** (127.0.0.1, ::1) is allowed and
    not recorded. On Windows every asyncio event loop builds its wake-up channel with
    `socket.socketpair()`, which connects to 127.0.0.1; blocking that would break every async test.
    Loopback isn't egress. Names (even `"localhost"`) are still blocked at `getaddrinfo`.

    Usage:

        def test_nothing_leaves(network_canary: NetworkCanary) -> None:
            run_the_thing()
            assert network_canary.attempts == []

        def test_only_anthropic(network_canary: NetworkCanary) -> None:
            with pytest.raises(anthropic.APIConnectionError):
                model.invoke("hi")
            assert network_canary.hosts == {"api.anthropic.com"}
    """
    canary = NetworkCanary()
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def fake_getaddrinfo(host: object, port: object, *_args: object, **_kwargs: object) -> Any:
        raise canary.record_and_block(host, port)

    def fake_create_connection(address: Any, *_args: object, **_kwargs: object) -> Any:
        raise canary.record_and_block(*_split_address(address))

    def fake_connect(self: socket.socket, address: Any) -> None:
        host, port = _split_address(address)
        if _is_loopback_ip(host):
            real_connect(self, address)
            return
        raise canary.record_and_block(host, port)

    def fake_connect_ex(self: socket.socket, address: Any) -> int:
        host, port = _split_address(address)
        if _is_loopback_ip(host):
            return real_connect_ex(self, address)
        raise canary.record_and_block(host, port)

    async def fake_loop_getaddrinfo(
        _loop: asyncio.AbstractEventLoop, host: object, port: object, **_kwargs: object
    ) -> Any:
        raise canary.record_and_block(host, port)

    async def fake_loop_create_connection(
        _loop: asyncio.AbstractEventLoop,
        _protocol_factory: object,
        host: object = None,
        port: object = None,
        **_kwargs: object,
    ) -> Any:
        raise canary.record_and_block(host, port)

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(socket, "create_connection", fake_create_connection)
    monkeypatch.setattr(socket.socket, "connect", fake_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", fake_connect_ex)
    monkeypatch.setattr(asyncio.BaseEventLoop, "getaddrinfo", fake_loop_getaddrinfo)
    monkeypatch.setattr(asyncio.BaseEventLoop, "create_connection", fake_loop_create_connection)
    return canary
