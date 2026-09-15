---
id: LG-016
title: Startup privacy guard and network canary test
status: done
priority: P1
milestone: M0 Foundation
mode: fast
labels: [privacy, security, testing]
depends: [LG-003]
---

## 🧭 The problem, in plain words

LG-002 proved LangGraph/LangChain stay quiet *by default*, but one stray env var (`LANGSMITH_TRACING=true`,
`LANGSMITH_GATEWAY=true`) would send my conversations to LangChain's servers. I want the app to lock that door
itself at startup, and a test that fails loudly if anything ever tries to connect somewhere it shouldn't.

## ✅ Done when

- [x] `lango/privacy.py` → `enforce_privacy()` runs first in app startup (FastAPI lifespan), before any graph/model is built:
  - [x] `langsmith.configure(enabled=False)`
  - [x] removes tracing / endpoint / gateway / Anthropic-routing env vars (full list in LG-002 "Enforcement rules"),
        logging only the *names* removed
  - [x] checks `langsmith.utils.tracing_is_enabled()` is falsy and **raises** otherwise (use `raise`, not `assert`,
        because asserts disappear under `python -O`)
- [x] `ChatAnthropic` is always built with explicit `base_url` + `api_key` from settings (LG-003), never from env
- [x] **Canary test:** hostile env (`LANGSMITH_TRACING=true`, `LANGSMITH_GATEWAY=true`, `ANTHROPIC_BASE_URL=…`),
      sockets patched to record + block, run startup + a graph with a fake model → **zero** connection attempts
- [x] Ruff `flake8-tidy-imports` banned-api for `LangChainTracer`, `tracing_v2_enabled`, `langsmith.traceable`,
      `langsmith.Client`, `RemoteGraph` (and a grep test for `draw_mermaid_png`)
- [x] Security agent verdict: PASS

## 📎 Notes from LG-003 security review

- `hide_input_in_errors=True` hides the key in `str(exc)` and tracebacks, **but `exc.errors()` and `exc.json()` still
  contain `input`** (verified). If startup catches a settings `ValidationError` to log or report it, use
  `exc.errors(include_input=False)` and add a test asserting a canary key isn't in the logged output.
- Never pickle or serialize `Settings`, because `pickle.dumps` contains the plaintext key. Pass only the fields needed.

## 📎 Notes from LG-002

- Evidence and canary design: see LG-002 → 🔬 Findings (`langsmith/utils.py:121-142`, `run_trees.py:235-316`).
- The findings suggested `assert not model._uses_gateway`. That's a **private** attribute that may change between
  versions, so prefer testing the behaviour (the canary) over poking internals.

## 🔍 Breakdown

Like a shop: before opening each morning, the owner locks the back doors, and a burglar alarm checks nobody sneaks out.

```
 uvicorn starts ──▶ lifespan() ──▶ 1. enforce_privacy()   lock the back doors (tracing off, risky env vars removed)
                                   2. load_settings()     check the ID card, fail with a key-free message
                                   3. yield → serve       only now can graphs / models be built
                                                │
                    build_chat_model(settings) ─┘ always ChatAnthropic(base_url=ANTHROPIC_BASE_URL, api_key=…)

 tests: 🐤 network canary = sockets patched to record + block ─▶ hostile env + startup + graph ─▶ 0 attempts
```

1. **Startup hook.** FastAPI `lifespan` runs code once, before the first request.
   📚 [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/)
2. **Global kill switch.** `langsmith.configure(enabled=False)` beats every tracing env var (LG-002 Q3).
3. **Env scrubbing.** Remove the LangSmith / gateway / Anthropic-routing vars from `os.environ`, logging names only.
4. **Safe settings errors.** Catch `ValidationError` and re-raise with `errors(include_input=False)` and `from None`,
   so the key can't ride along in the exception chain (LG-003 security finding).
5. **One model factory.** `build_chat_model(settings)` is the only place `ChatAnthropic` is built.
6. **Network canary.** Monkeypatch `socket.getaddrinfo`, `socket.create_connection` and `socket.socket.connect` to record
   and block, then prove nothing tries to leave.
   📚 [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
7. **Ban risky APIs.** Ruff `flake8-tidy-imports` banned-api, so importing a tracer fails lint.
   📚 [ruff banned-api](https://docs.astral.sh/ruff/settings/#lint_flake8-tidy-imports_banned-api)

## 🛠️ Approach

| Option | Trade-off |
|---|---|
| A. Only set `LANGSMITH_TRACING=false` in `.env` | Nothing enforces it; one shell var overrides it |
| B. Guard at startup + canary tests + lint ban | Enforced in code, proven by tests, stopped at lint time. A bit more code |
| C. B + OS-level egress firewall on the host | Strongest, but it's a hosting concern → decide in LG-008 |

**Recommendation: B**, with C noted for LG-008.

**Interface:**
- `lango/privacy.py`:
  - `PrivacyError(RuntimeError)`
  - `BLOCKED_ENV_VARS: Final[frozenset[str]]` (the LG-002 list)
  - `enforce_privacy() -> list[str]`: returns sorted removed names; raises `PrivacyError` if `tracing_is_enabled()` is still truthy
- `lango/config.py`: `SettingsError(RuntimeError)` + `load_settings() -> Settings`, which wraps `get_settings()` with key-free errors
- `lango/llm.py`: `build_chat_model(settings, *, max_retries=2, timeout=30.0) -> ChatAnthropic`
- `lango/main.py`: `lifespan` calls `enforce_privacy()` then `load_settings()`
- `tests/conftest.py`: reusable `network_canary` fixture (LG-004 onwards reuses it)

## 🧑‍💻 Session plan

**Mode: fast** (Arren asked to have it coded automatically). The `coding` agent implements `src/` and `pyproject.toml`;
the `testing` agent writes tests in parallel against the interface above; Claude integrates and runs all checks; the
`security` agent reviews. Arren reviews the result.

## 🛬 Post-flight review (2026-09-15)

**Built (fast mode):**
- `src/lango/privacy.py`: `enforce_privacy()` strips 30 env vars, forces LangSmith off, resets SDK debug loggers, raises
  `PrivacyError` if tracing is still on
- `src/lango/config.py`: `load_settings()` / `SettingsError`
- `src/lango/llm.py`: `build_chat_model()`, the only way to get a `ChatAnthropic`, runs the guard itself
- `src/lango/main.py`: `lifespan`
- `pyproject.toml`: ruff TID banned-api
- `tests/conftest.py`: reusable `network_canary` + `hostile_env` fixtures

**Testing:** 51 passed, 1 skipped (lowercase env var case, Linux only), coverage 99%.
- Headline test: hostile env + startup + LangGraph `invoke`/`ainvoke` + tracer flush → **0 connection attempts**.
- A subprocess control test proves the canary does catch a LangSmith upload when the guard is off.
- Verified the tests fail when they should: with the guard replaced by a no-op, the canary sees `api.smith.langchain.com`;
  with an unpinned model, it sees `proxy.invalid.example`.

**Security agent: PASS with Mediums → all fixed:**
- **Med, fixed:** `ANTHROPIC_LOG=debug` makes the Anthropic SDK log **full request bodies (conversation text)**, and it's
  applied at `import anthropic`, before startup. `ANTHROPIC_LOG` is now blocked, and the guard resets the SDK/httpx loggers above DEBUG.
- Low, fixed: `ANTHROPIC_PROXY` was read when the model is built → `anthropic_proxy=None` explicitly, and the factory runs the guard
  (covers `--lifespan off`, scripts, module-level models).
- Low, fixed: proxy / CA bundle / TLS key log / custom header env vars blocked (`HTTP(S)_PROXY`, `ALL_PROXY`, `SSL_CERT_FILE`,
  `SSL_CERT_DIR`, `SSLKEYLOGFILE`, `ANTHROPIC_CUSTOM_HEADERS`).
- Low, fixed: `SettingsError` no longer keeps the `ValidationError` as `__context__` (its `.errors()` held the key).
- Low, fixed: `langsmith.tracing_context` and `langsmith.configure` are banned by lint outside `privacy.py`.
- Low, fixed: `.env.example` no longer sets tracing vars (they were no-ops that caused a startup warning).
- Low, open: canary blind spots (Windows `loop.sock_connect`, UDP `sendto`) that nothing uses today → LG-017.
- Note for LG-008: OS-level proxies (Windows registry / macOS settings) can't be stripped from env. Stripping
  `HTTPS_PROXY` would also break a real corporate proxy. Consider an egress firewall on the host.

## 📝 What I learned
