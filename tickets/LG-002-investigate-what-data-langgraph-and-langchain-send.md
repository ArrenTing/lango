---
id: LG-002
title: Investigate what data LangGraph and LangChain send anywhere
status: done
priority: P1
milestone: M0 Foundation
mode: guided
labels: [investigation, privacy]
depends: []
---

## 🧭 The problem, in plain words

My conversations with family are private. I want LangGraph and LangChain for orchestration, but I need proof,
not a hunch, that they don't quietly send my messages anywhere besides Anthropic (tracing, telemetry, analytics).

## ❓ Questions for the investigation agent

1. Does `langgraph` or `langchain-core` make any network call on import or at runtime besides the model provider?
2. Exactly which env vars / settings turn LangSmith tracing on, and is it off by default in the installed versions?
3. Can we force tracing off in code so a stray env var can't turn it on? What's the cleanest way?
4. Does `langchain-anthropic` send anything extra to Anthropic (metadata, user IDs) we should know about?
5. What does Anthropic do with API inputs by default (retention, training)? Load the `claude-api` skill and cite official docs.

## ✅ Done when

- [x] Findings with file:line / doc evidence written into this ticket
- [x] A one-paragraph privacy statement I agree with, ready for the README (approved by Arren and published in README → Privacy)
- [x] Follow-up tickets created for anything we need to enforce in code: LG-003 updated, LG-016, LG-017

## 🔍 Breakdown

Think of lango's data like a letter. We know it has to go to one post office (Anthropic). This ticket checks
every place the letter *could* be copied along the way.

```
 my phone ──▶ lango server ──▶ LangGraph ──▶ langchain-anthropic ──▶ Anthropic API ✅
                                  │                 │
                                  └──▶ LangSmith? ◀─┘   ❓ tracing (a hosted "flight recorder")
                                  └──▶ telemetry? ❓     analytics pings on import / run
```

1. **Map the libraries.** Which packages are installed, and who pulled them in? Heads-up: `langsmith 0.12.5` is
   already in `.venv` as a transitive dependency, so the tracing client is present even though we never asked for it.
   📚 Concept: *transitive dependencies* ([`uv tree`](https://docs.astral.sh/uv/concepts/projects/layout/)).
2. **Find every door out.** Search the installed source for HTTP clients and telemetry, and check each hit against
   "does this only run when switched on?"
   📚 Concept: *callbacks and tracers* in LangChain ([tracing with LangChain](https://docs.langchain.com/langsmith/trace-with-langchain)).
3. **Find the switches.** Which env vars or settings turn tracing on (`LANGSMITH_TRACING`, `LANGCHAIN_TRACING_V2`, API keys,
   project names), and what's the default?
   📚 Concept: *config through environment variables* ([LangSmith tracing](https://docs.langchain.com/langsmith/observability)).
4. **Lock the door from the inside.** Is there a code-level way to force tracing off that beats a stray env var?
   This feeds LG-003.
5. **Check the post office.** What `langchain-anthropic` sends with each request (headers, metadata) and what Anthropic does
   with API data by default (retention, training), from official docs.
6. **Write it down.** A plain-English privacy statement for the README, plus follow-up tickets for anything we must enforce.

## 🛠️ Approach

| Option | Trade-off |
|---|---|
| A. Trust the docs | Fast, but docs describe intent, not what the installed code actually does |
| B. Read the installed source + official docs | Evidence tied to our exact versions (file:line); a bit slower |
| C. B + a network "canary" run | Strongest proof: run a graph with a fake model and watch for any outbound connection |

**Recommendation: C, kept small.** The investigation agent reads the installed source and official docs, then runs a
throwaway script in its scratchpad (fake chat model, no API key, outbound sockets blocked) to prove nothing tries to
phone home. The permanent version of that canary becomes a real test in LG-003.

## 🧑‍💻 Session plan

This is a research ticket, so there's no `YOUR TURN` code in the repo.

| Claude Code does (pre-flight) | Arren does |
|---|---|
| Runs the `investigation` agent and appends `🔬 Findings` with evidence | Reads the findings. Anything unclear → ask in Cursor or here |
| Drafts the privacy statement and follow-up tickets | Edits the privacy statement until he agrees with every sentence |
| Updates LG-003's "Done when" with the enforcement rules found | **Try it yourself (optional, ~10 min in Cursor):** open `.venv/Lib/site-packages/langsmith/` and find where tracing checks its env var. Compare with what the agent found |
|  | Writes 📝 What I learned, then says "review LG-002" |

## 🔬 Findings

_Investigation agent, 2026-09-15. Versions checked: langgraph 1.2.11, langchain-core 1.6.3, langchain-anthropic 1.7.2,
langsmith 0.12.5, anthropic 1.6.0. Paths below are relative to `.venv/Lib/site-packages/`._

**Who pulls in langsmith:** `uv tree` shows `langchain-core 1.6.3 → langsmith 0.12.5`. It's a hard dependency of
langchain-core, so it can't be removed. We can only keep it switched off.

### Q1. Does langgraph / langchain-core call the network on import or at runtime, besides the model provider?

**Answer: not by default.** Every outbound path I found is opt-in:

| Path | Where | What turns it on |
|---|---|---|
| LangSmith tracer → `https://api.smith.langchain.com` (full inputs/outputs of every run) | `langchain_core/callbacks/manager.py:2497-2541` adds `LangChainTracer`; default URL `langsmith/utils.py:841` | Tracing enabled (see Q2) |
| **LangSmith LLM gateway → `https://gateway.smith.langchain.com/anthropic`** (the *model request itself* is sent to LangChain's proxy) | `langchain_core/utils/_gateway.py:38,95-103,148-177`, used by `langchain_anthropic/chat_models.py:1415-1434` | `LANGSMITH_GATEWAY=true` (or a URL) with no explicit `base_url` |
| Model request redirected to another host | `langchain_anthropic/chat_models.py:1432` (`ANTHROPIC_API_URL`, `ANTHROPIC_BASE_URL`), `_client_utils.py:54-56`; proxy from `ANTHROPIC_PROXY` at `chat_models.py:1143-1144` | Those env vars |
| Mermaid PNG render → `mermaid.ink` (sends graph *structure*, not messages) | `langchain_core/runnables/graph_mermaid.py:280` (default `MermaidDrawMethod.API`), `:461` `requests.get` | Calling `graph.get_graph().draw_mermaid_png()` |
| `RemoteGraph` → LangGraph server | `langgraph/pregel/remote.py` (via `langgraph_sdk`) | Only if we use `RemoteGraph` |

Nothing else: `langgraph/_internal/_retry.py` only imports `httpx`/`requests` to classify exceptions.
`langchain_core/_security/_transport.py` is an SSRF-guarded client factory, not a caller. There's no telemetry or
analytics code in langgraph, langchain-core or langchain-anthropic (grep for `telemetry|analytics|posthog|sentry` finds
nothing). Hits in `anthropic/lib/_stainless_helpers.py` are request headers sent to Anthropic only. The canary (below)
recorded **zero** connection attempts for import + two graph runs with a clean env.
**Confidence: high.**

### Q2. Which env vars turn LangSmith tracing on, and is it off by default?

**Answer: off by default.** The decision lives in `langsmith/utils.py:121-142` (`tracing_is_enabled`), checked in this order:
1. context var from `tracing_context(enabled=...)` (`:132-133`)
2. "already inside a run tree" → `True` (`:135-136`)
3. global from `langsmith.configure(enabled=...)` (`:138-139`)
4. env: `get_env_var("TRACING_V2", default=get_env_var("TRACING"))` must equal `"true"` (`:141-142`)

`get_env_var` tries the `LANGSMITH_` then `LANGCHAIN_` prefix (`utils.py:419-442`). That means **four** env vars can
turn it on: `LANGSMITH_TRACING_V2`, `LANGCHAIN_TRACING_V2`, `LANGSMITH_TRACING`, `LANGCHAIN_TRACING`. It's
`@functools.lru_cache`d (`:418`), so env changes after the first check are ignored. langchain-core also turns tracing on if
`tracing_v2_callback_var` is set by `tracing_v2_enabled()` (`langchain_core/tracers/context.py:132-135`). That check runs
*before* langsmith's own. `LANGSMITH_API_KEY` doesn't turn tracing on. Without it the tracer still tries to send
(canary case b used a fake key, so this wasn't tested keyless). `LANGSMITH_ENDPOINT`/`LANGSMITH_PROJECT` only change
where the data goes. Unrelated but important: `LANGSMITH_GATEWAY` (Q1) reroutes model traffic even with tracing off.
**Confidence: high** (source + canary).

### Q3. Can we force tracing off in code so a stray env var can't turn it on?

**Answer: yes.** Call `langsmith.configure(enabled=False)` at startup (`langsmith/run_trees.py:235`, sets both the context
var and the global at `:314-316`). It's checked before the env var (`utils.py:138-139` beats `:141`). In the canary
it beat `LANGSMITH_TRACING=true` and all `*_TRACING_V2=true` together (cases c1, c4). The other options:
- `with tracing_context(enabled=False):` also works (c2), but only inside the `with` block. Every entry point would
  need it, so it's easy to miss one.
- Scrubbing `os.environ` before importing works (c3), but it's fragile: it depends on import order and on
  `lru_cache`, and it misses vars added later by `.env` loaders.
- None of these stop code that *explicitly* passes `callbacks=[LangChainTracer()]` or uses `tracing_v2_enabled()`
  (`context.py:133` returns `True` first). Enforce that with a lint rule or test.

**Belt and braces:** do `configure(enabled=False)` **and** delete the `LANGSMITH_*`/`LANGCHAIN_*` tracing, endpoint and
gateway vars from `os.environ` at the very top of app startup, then assert `tracing_is_enabled() is False`.
**Confidence: high.**

### Q4. Does langchain-anthropic send anything extra to Anthropic?

**Answer: no user IDs or run metadata, just SDK/version headers.**
- Headers: `User-Agent: langchain-anthropic/1.7.2` (`langchain_anthropic/chat_models.py:103,1447`) plus the Anthropic SDK's
  `X-Stainless-*` headers: OS, arch, Python runtime and version, package version (`anthropic/_base_client.py:2387-2394`,
  `anthropic/_client.py:387`).
- Body (`chat_models.py:1630-1646`): model, max_tokens, messages, system, sampling params, and fields that stay `None`
  unless set (`betas`, `mcp_servers`, `container`, `user_profile_id`, `context_management`), plus `model_kwargs`/call
  kwargs. There's no Anthropic `metadata.user_id` unless we pass it. LangGraph run config, tags and metadata stay in the
  callback system and are **not** put into the request (`_add_version` at `langchain_core/language_models/base.py:253`
  only feeds tracing metadata).
- ⚠️ The destination is env-dependent (Q1 table). Canary case d: with `LANGSMITH_GATEWAY=true`, `ChatAnthropic()` connected to
  `gateway.smith.langchain.com:443`. Case e: passing `base_url="https://api.anthropic.com"` explicitly won over both
  `LANGSMITH_GATEWAY` and `ANTHROPIC_BASE_URL`.

**Confidence: high.**

### Q5. What does Anthropic do with API inputs by default?

**Answer:** it doesn't train on them and deletes them within 30 days, with exceptions for flagged content and legal holds.
- Training: "By default, we will not use your inputs or outputs from our commercial products... to train our models."
  Exceptions are explicit feedback or opt-in programs.
  <https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training>
- Retention: API inputs and outputs are deleted from Anthropic's backend within 30 days. Content flagged by trust and
  safety systems is kept up to 2 years, with safety scores kept up to 7 years. Data is also kept when required by law.
  Feedback is kept 5 years.
  <https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data>
- Zero data retention (ZDR) is available per organization through Anthropic sales. "Covered Models" (Fable 5/5.1, Mythos 5/5.1)
  *require* 30-day retention. Flagged content can be kept up to 2 years even under ZDR. Console/playground use isn't
  covered by ZDR. <https://platform.claude.com/docs/en/manage-claude/api-and-data-retention>
- The `claude-api` skill has no retention details, so the answers above come from the official pages.

**Confidence: high** for what the policy says today (policies can change, so re-check yearly).

### 🐤 Canary results

Script: scratchpad `canary.py` (not in repo). Each case runs in a fresh subprocess with `socket.getaddrinfo`,
`socket.create_connection` and `socket.socket.connect`/`connect_ex` patched to record and block. Graph = one node calling
`GenericFakeChatModel`, run with `invoke` and `ainvoke`, then `wait_for_all_tracers()` + 3 s + client flush. No real keys, placeholder text.

| Case | Env | Kill switch | Outbound attempts |
|---|---|---|---|
| a | clean | none | **none** |
| b | `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY=fake` | none | **`getaddrinfo: api.smith.langchain.com`** |
| c1 | as b | `langsmith.configure(enabled=False)` after import | none |
| c2 | as b | `with langsmith.tracing_context(enabled=False)` | none (inside block only) |
| c3 | as b | delete `LANGSMITH_*`/`LANGCHAIN_*` from env before import | none |
| c4 | b + `LANGCHAIN_TRACING_V2=true` + `LANGSMITH_TRACING_V2=true` | `configure(enabled=False)` | none |
| d | `LANGSMITH_GATEWAY=true`, `LANGSMITH_API_KEY=lsv2_fake`; `ChatAnthropic()` | none | **`gateway.smith.langchain.com:443`** (resolved `api_url=…/anthropic`) |
| e | d + `ANTHROPIC_BASE_URL=https://proxy.invalid.example`; `ChatAnthropic(base_url="https://api.anthropic.com", api_key=fake)` | explicit `base_url` | `api.anthropic.com:443` only |

### Recommendation

LangGraph and LangChain are safe to use. Nothing phones home unless an env var or explicit code turns it on. At
startup, lango should call `langsmith.configure(enabled=False)`, strip the LangSmith/LangChain/Anthropic-routing env vars,
and create `ChatAnthropic` with an explicit `base_url="https://api.anthropic.com"`. A canary test in CI then proves no
host other than `api.anthropic.com` is ever contacted.

### Privacy statement (approved by Arren 2026-09-15, published in README)

> lango sends the text you type, and the other person's replies, to exactly one outside service: the Anthropic API,
> which does the translation. It doesn't use LangSmith, analytics, or error-tracking services. Tracing is switched off
> in code at startup, and an automated test checks that the app never connects anywhere else. lango doesn't log message
> text, translations, or prompts, only event names, timings, and token counts. Under Anthropic's commercial terms, API
> inputs and outputs aren't used to train models by default, and they're deleted within 30 days. Anthropic may keep
> content longer if its safety systems flag it (up to 2 years) or if the law requires it
> ([training](https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training),
> [retention](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)).

### Enforcement rules for LG-003

- At the top of app startup (before building graphs/models): `import langsmith; langsmith.configure(enabled=False)`.
- Also at startup, delete from `os.environ`: `LANGSMITH_TRACING`, `LANGSMITH_TRACING_V2`, `LANGCHAIN_TRACING`,
  `LANGCHAIN_TRACING_V2`, `LANGSMITH_API_KEY`, `LANGCHAIN_API_KEY`, `LANGSMITH_ENDPOINT`, `LANGCHAIN_ENDPOINT`,
  `LANGSMITH_RUNS_ENDPOINTS`, `LANGSMITH_OTEL_ENABLED`, `LANGSMITH_GATEWAY`, `LANGSMITH_GATEWAY_API_KEY`,
  `ANTHROPIC_API_URL`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_PROXY`. Log only the *names* removed, never the values.
- Then `assert langsmith.utils.tracing_is_enabled() is False`, and fail startup otherwise.
- Construct `ChatAnthropic(base_url="https://api.anthropic.com", api_key=settings.anthropic_api_key, ...)` explicitly;
  never rely on env resolution for URL or key. Assert `not model._uses_gateway`.
- Don't set `anthropic_proxy`, `default_headers`, `mcp_servers`, `user_profile_id`, or `metadata` on the model.
- Ban in code (ruff `banned-api` or a grep test): `LangChainTracer`, `tracing_v2_enabled`, `langsmith.traceable`,
  `langsmith.Client`, `RemoteGraph`, `draw_mermaid_png` (use `draw_mermaid()` text or `draw_method=PYPPETEER` locally).
- Permanent canary test (no network, fake model): patch sockets as in the canary, set hostile env
  (`LANGSMITH_TRACING=true`, `LANGSMITH_GATEWAY=true`, `ANTHROPIC_BASE_URL=…`), run app startup + graph, and assert zero
  attempts. A `live_llm` variant asserts the only host is `api.anthropic.com`.
- `.env.example` documents that LangSmith vars are intentionally unsupported.

### Suggested follow-up tickets (not created)

- **Startup privacy guard (`lango/privacy.py`)**: the configure/env-scrub/assert block above, called first in `main`.
- **Network canary test**: a pytest that blocks sockets under a hostile env and asserts no outbound attempts.
- **Ban tracing and remote APIs via ruff**: `flake8-tidy-imports` banned-api for `LangChainTracer`, `traceable`, `RemoteGraph`, `draw_mermaid_png`.
- **Pin ChatAnthropic endpoint in settings**: explicit `base_url` + key from pydantic-settings, and a test that `_uses_gateway` is False.
- **Dependency watch for new phone-home code**: on dependency bumps, re-run the grep and canary (e.g. a CI step or a checklist in the security agent).
- **README privacy section**: publish the agreed privacy statement.

## 📝 What I learned

1. I assumed my messages will pass through to Anthropic and to then to other third parties.
2. Don't care about that.
3. Its more permanent. A change in .env is possible if someone manages to go into your servers and stuff. Basic answer.
