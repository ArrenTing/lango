"""🐤 Zero egress under a hostile environment (LG-016).

The headline privacy test: with every env var that could leak data set (see `hostile_env`), app
startup plus a LangGraph run must not try to connect anywhere. The control test proves the canary
really catches a leak, so a passing headline test means something.
"""

import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import TypedDict

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from conftest import HOSTILE_ENV, TRACING_AND_ROUTING_ENV_VARS, NetworkCanary
from lango.main import app

CONTROL_TIMEOUT_SECONDS = 60


class TranslationState(TypedDict, total=False):
    text: str
    translation: str


def build_fake_translation_graph() -> CompiledStateGraph[TranslationState]:
    """A one-node graph shaped like lango's real one, with a fake model (no API calls)."""
    model = GenericFakeChatModel(messages=iter(["Xin chào (fake 1)", "Xin chào (fake 2)"]))

    def translate(state: TranslationState) -> TranslationState:
        reply = model.invoke(state["text"])
        return {"translation": str(reply.content)}

    graph = StateGraph(TranslationState)
    graph.add_node("translate", translate)
    graph.add_edge(START, "translate")
    graph.add_edge("translate", END)
    return graph.compile()


def flush_langsmith_tracers() -> None:
    # Imported here, not at module level: tracer APIs are banned in src/ (LG-016). A test may use
    # this one to flush any pending trace uploads so the canary sees them.
    from langchain_core.tracers.langchain import wait_for_all_tracers  # noqa: PLC0415

    wait_for_all_tracers()


@pytest.mark.asyncio
@pytest.mark.usefixtures("hostile_env")
async def test_startup_and_graph_run_make_zero_connection_attempts_under_hostile_env(
    network_canary: NetworkCanary,
) -> None:
    # Arrange + Act 1: app startup (the lifespan runs enforce_privacy, then load_settings).
    with TestClient(app):
        pass

    # Act 2: a graph run, both sync and async, then flush anything a tracer queued.
    graph = build_fake_translation_graph()
    sync_result = graph.invoke({"text": "placeholder hello"})
    async_result = await graph.ainvoke({"text": "placeholder hello again"})
    flush_langsmith_tracers()

    # Assert
    assert sync_result["translation"] == "Xin chào (fake 1)"
    assert async_result["translation"] == "Xin chào (fake 2)"
    assert network_canary.attempts == [], (
        f"something tried to connect out: {network_canary.attempts}. Check enforce_privacy() "
        "runs first in the lifespan and that tracing / gateway env vars are removed."
    )


# ── Control: the canary catches a real leak ─────────────────────────────────

# Runs in a fresh interpreter because LangSmith keeps process-wide state (configure(), cached env
# lookups, a cached client) that the in-process tests change. Same record-and-block idea as
# `network_canary` in conftest.py (the DNS/connect helpers LangSmith's HTTP client goes through),
# same hostile env, but NO enforce_privacy().
CONTROL_SCRIPT = textwrap.dedent(
    """
    import json, os, socket, sys, time
    from typing import TypedDict

    attempts = []

    def blocked(host, port):
        if isinstance(host, bytes):
            host = host.decode()
        attempts.append([str(host), port if isinstance(port, int) else None])
        return OSError("network blocked by lango test canary")

    def fake_getaddrinfo(host, port, *args, **kwargs):
        raise blocked(host, port)

    def fake_create_connection(address, *args, **kwargs):
        raise blocked(address[0], address[1])

    socket.getaddrinfo = fake_getaddrinfo
    socket.create_connection = fake_create_connection

    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langgraph.graph import END, START, StateGraph

    class State(TypedDict, total=False):
        text: str
        translation: str

    model = GenericFakeChatModel(messages=iter(["fake reply"]))

    def translate(state):
        return {"translation": str(model.invoke(state["text"]).content)}

    graph = StateGraph(State)
    graph.add_node("translate", translate)
    graph.add_edge(START, "translate")
    graph.add_edge("translate", END)
    graph.compile().invoke({"text": "placeholder hello"})

    # The tracer uploads from a background thread. Wait for its first (blocked) attempt rather
    # than wait_for_all_tracers(): that retries with backoff and takes ~12 s against a blocked
    # network. os._exit skips LangSmith's atexit flush for the same reason.
    deadline = time.monotonic() + 20
    while not attempts and time.monotonic() < deadline:
        time.sleep(0.05)

    sys.stdout.write("CANARY_ATTEMPTS=" + json.dumps(attempts) + "\\n")
    sys.stdout.flush()
    os._exit(0)
    """
)


def test_control_canary_catches_langsmith_upload_when_privacy_is_not_enforced(
    tmp_path: Path,
) -> None:
    # Arrange: a clean copy of the env (nothing from the developer's shell) plus the hostile vars.
    blocked = {name.upper() for name in TRACING_AND_ROUTING_ENV_VARS}
    env = {name: value for name, value in os.environ.items() if name.upper() not in blocked}
    env.update(HOSTILE_ENV)
    env["PYTHONIOENCODING"] = "utf-8"

    # Act
    started = time.monotonic()
    completed = subprocess.run(  # noqa: S603 - fixed script, our own interpreter
        [sys.executable, "-c", CONTROL_SCRIPT],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=CONTROL_TIMEOUT_SECONDS,
        check=False,
    )
    elapsed = time.monotonic() - started

    # Assert
    assert completed.returncode == 0, completed.stderr[-2000:]
    line = next(
        (ln for ln in completed.stdout.splitlines() if ln.startswith("CANARY_ATTEMPTS=")), None
    )
    assert line is not None, f"control script printed no result; stderr: {completed.stderr[-2000:]}"
    hosts = {host for host, _port in json.loads(line.removeprefix("CANARY_ATTEMPTS="))}
    assert any(host.endswith("langchain.com") for host in hosts), (
        f"expected a blocked attempt to a LangSmith host, got {hosts!r} after {elapsed:.1f}s. "
        "If this fails, the canary no longer catches tracing uploads and the headline test "
        "proves nothing."
    )
