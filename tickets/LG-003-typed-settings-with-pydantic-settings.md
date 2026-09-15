---
id: LG-003
title: Typed settings with pydantic-settings
status: done
priority: P1
milestone: M0 Foundation
mode: guided
labels: [config, privacy]
depends: [LG-002]
---

## 🧭 The problem, in plain words

The app needs a few settings (my API key, which Claude model, language pair) loaded safely from `.env`, with the
key never printed by accident and the model's address fixed in code, so no env var can reroute my messages.

## ✅ Done when

- [x] `lango.config.Settings` loads from env / `.env`, and the API key is a `SecretStr`
- [x] App fails fast with a clear message if the key is missing or malformed, **without the key appearing in the error**
- [x] Anthropic endpoint pinned in code as a constant (`ANTHROPIC_BASE_URL = "https://api.anthropic.com"`), **not** a
      setting, so no env var can override it (LG-002 found `LANGSMITH_GATEWAY` / `ANTHROPIC_BASE_URL` can reroute model traffic)
- [x] Tests never read the real `.env` on my machine
- [x] `.env.example` says LangSmith and Anthropic-routing vars are intentionally unsupported
- [x] All checks green

Tracing kill switch, env scrubbing, and the network canary test are split out into **LG-016**.

## 🔍 Breakdown

Settings are the app's **ID card**: a small, typed object holding everything that changes between my laptop, CI, and
the server. Code asks the card; it never reads `os.environ` directly.

```
 .env file ─┐
            ├──▶ Settings (pydantic-settings) ──▶ checks types + rules ──▶ get_settings() ──▶ app / graph
 env vars ──┘         │                                  │
                      │                                  └─ ❌ bad/missing key → clear error, key NOT shown
                      └─ anthropic_api_key: SecretStr   → prints as '**********'

 ANTHROPIC_BASE_URL  = constant in code  (not on the ID card, so nothing outside can change it)
```

1. **A typed settings class.** Fields with types and defaults: the API key, the model name, and my language and hers.
   📚 *pydantic-settings `BaseSettings`* ([docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/))
2. **Secrets that don't print.** `SecretStr` hides the value in `print`, logs, and `repr`. You have to ask for it explicitly
   with `.get_secret_value()`.
   📚 *Secret types* ([docs](https://docs.pydantic.dev/latest/api/types/#pydantic.types.SecretStr))
3. **Validate early.** A `@field_validator` rejects a key that doesn't look like an Anthropic key, and `Literal` types
   reject a model or language we don't support. The app refuses to start instead of failing mid-conversation.
   📚 *Validators* ([docs](https://docs.pydantic.dev/latest/concepts/validators/))
4. **⚠️ Errors can leak secrets.** Verified in pre-flight: by default a failed validator's error message **includes
   the raw key**. `hide_input_in_errors=True` in the config hides it. A test proves it stays hidden.
   📚 *`hide_input_in_errors`* ([docs](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.hide_input_in_errors))
5. **Config vs constants.** Anything that *should* differ per environment is a setting. Anything that must *never* differ
   (the Anthropic URL) is a `Final` constant.
   📚 *`typing.Final`* ([docs](https://docs.python.org/3/library/typing.html#typing.Final))
6. **One shared instance.** `get_settings()` with `functools.lru_cache` builds the settings once. FastAPI can inject it with
   `Depends`, and tests can swap it.
   📚 *FastAPI settings pattern* ([docs](https://fastapi.tiangolo.com/advanced/settings/))

## 🛠️ Approach

| Option | Trade-off |
|---|---|
| A. `os.environ["ANTHROPIC_API_KEY"]` scattered in code | Simple, but no types or validation, easy to leak, and hard to test |
| B. `pydantic-settings` class + cached `get_settings()` | Typed, validated, secret-safe, and testable. It's the FastAPI-recommended pattern |
| C. B + a separate config file format (TOML/YAML) | More flexible, but overkill for a handful of values |

**Recommendation: B.** Key details:
- Field `anthropic_api_key: SecretStr` reads env var `ANTHROPIC_API_KEY` (matching `.env.example`). No `LANGO_` prefix for
  it, because that's the name every Anthropic tool expects.
- `model: Literal["claude-sonnet-5", "claude-haiku-4-5-20251001"] = "claude-sonnet-5"`. Sonnet is the quality default.
  Haiku is there for LG-007, if streaming feels slow.
- `my_language: Literal["en"] = "en"`, `their_language: Literal["vi"] = "vi"`. Tight on purpose; widen them later.
- `SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)`.
- Env vars: `ANTHROPIC_API_KEY` (via `validation_alias`), then `LANGO_MODEL`, `LANGO_MY_LANGUAGE`, `LANGO_THEIR_LANGUAGE` (`env_prefix="LANGO_"`).
- Tests run from an empty temp folder (`monkeypatch.chdir(tmp_path)`) with Anthropic/LANGO_ env vars removed, so my
  real `.env` is never read, yet a test can still prove `env_file` works by writing a fake `.env` there.

**Pre-flight verification:** a reference solution passed all 9 tests, mypy, and ruff (then it was deleted).
Mutation check: removing `hide_input_in_errors=True` makes the leak test fail, so it really guards the key.

## 🧑‍💻 Session plan

**Files:** `src/lango/config.py` (new), `tests/test_config.py` (new), `.env.example` (updated).

| Claude scaffolds (pre-flight) | Arren writes in Cursor (`YOUR TURN`) |
|---|---|
| `config.py`: imports, `ANTHROPIC_BASE_URL: Final` constant, `Settings` class shell with docstring, `get_settings()` with `lru_cache` | **Gap 1 · Fields** (~6 lines): declare the 4 fields with the right types and defaults |
| `tests/test_config.py`: fixtures for a clean env, with all tests written first and failing | **Gap 2 · `model_config`** (~3 lines): `.env` file, ignore extra vars, hide input in errors |
| `.env.example`: comments on the LangSmith/routing vars being unsupported | **Gap 3 · Key validator** (~6 lines): `@field_validator` that rejects keys not starting with `sk-ant-`, with an error message that doesn't include the key |
| | **Run tests:** `uv run pytest tests/test_config.py -v` until green, then try printing `get_settings()` in a REPL and see `**********` |

**Tests written first (they define "done"):**
- valid env → settings load, the key is a `SecretStr`, and `str(settings)` doesn't contain the key
- missing key → `ValidationError` that names `anthropic_api_key`
- malformed key → `ValidationError`, and **the key text is not in the error message**
- unsupported model or language → `ValidationError`
- `ANTHROPIC_BASE_URL` env var set to a proxy → the constant is still `https://api.anthropic.com`
- `get_settings()` returns the same object twice (cached)

Wiring settings into FastAPI startup waits until there's something to use them (LG-004/LG-016), so it's not in this ticket.

## 🛬 Post-flight review (2026-09-15)

**Arren's code:** fields, `model_config`, and the validator logic were right, including `hide_input_in_errors=True` and
an error message that doesn't include the key. Claude fixed the rest at Arren's request:
- The validator was an instance method (`self`), but `@field_validator` needs `@classmethod` + `cls`, because validators
  run while the object is being built, before `self` exists. This error stopped every test from loading.
- A line `anthropic_api_key = field_validator(...)(check_key_format)  # type: ignore` **replaced the API key field**
  with a validator object. The `# type: ignore` hid mypy's warning about it. Removed.
- Duplicate `model` / `my_language` / `their_language` / `model_config` declarations removed (mypy `no-redef`).
- `test_valid_env_loads_settings_…` had been renamed to `valid_settings_object`. Without the `test_` prefix pytest
  **silently skipped it**, so the "key hidden when printed" check wasn't running. Name restored.

**Testing:** 11 passed (10 config + health), `config.py` coverage 100%. Mutation check: removing
`hide_input_in_errors=True` makes the leak test fail.

**Security agent: PASS.** Findings:
- Low, fixed: a key that's only `sk-ant-` was accepted. It's now rejected, with a new test.
- Low, carried to LG-016: `exc.errors()` / `exc.json()` still include the raw input despite `hide_input_in_errors`.
  Startup error handling must use `errors(include_input=False)`.
- Info, noted in LG-016: `pickle.dumps(settings)` contains the plaintext key, so never pickle `Settings`.
- Info, not fixed: the test fixture only removes upper-case env var names (it can only make a test flaky, never leak).

## 📝 What I learned
