---
id: LG-016
title: Startup privacy guard and network canary test
status: todo
priority: P1
milestone: M0 Foundation
mode: guided
labels: [privacy, security, testing]
depends: [LG-003]
---

## 🧭 The problem, in plain words

LG-002 proved LangGraph/LangChain stay quiet *by default*, but one stray env var (`LANGSMITH_TRACING=true`,
`LANGSMITH_GATEWAY=true`) would send my conversations to LangChain's servers. I want the app to lock that door
itself at startup, and a test that fails loudly if anything ever tries to connect somewhere it shouldn't.

## ✅ Done when

- [ ] `lango/privacy.py` → `enforce_privacy()` runs first in app startup (FastAPI lifespan), before any graph/model is built:
  - [ ] `langsmith.configure(enabled=False)`
  - [ ] removes tracing / endpoint / gateway / Anthropic-routing env vars (full list in LG-002 "Enforcement rules"),
        logging only the *names* removed
  - [ ] checks `langsmith.utils.tracing_is_enabled()` is falsy and **raises** otherwise (use `raise`, not `assert`,
        because asserts disappear under `python -O`)
- [ ] `ChatAnthropic` is always built with explicit `base_url` + `api_key` from settings (LG-003), never from env
- [ ] **Canary test:** hostile env (`LANGSMITH_TRACING=true`, `LANGSMITH_GATEWAY=true`, `ANTHROPIC_BASE_URL=…`),
      sockets patched to record + block, run startup + a graph with a fake model → **zero** connection attempts
- [ ] Ruff `flake8-tidy-imports` banned-api for `LangChainTracer`, `tracing_v2_enabled`, `langsmith.traceable`,
      `langsmith.Client`, `RemoteGraph` (and a grep test for `draw_mermaid_png`)
- [ ] Security agent verdict: PASS

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

## 🛠️ Approach

## 🧑‍💻 Session plan

## 📝 What I learned
