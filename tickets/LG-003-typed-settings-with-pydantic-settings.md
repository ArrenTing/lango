---
id: LG-003
title: Typed settings with pydantic-settings
status: todo
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

- [ ] `lango.config.Settings` loads from env / `.env`, and the API key is a `SecretStr`
- [ ] App fails fast with a clear message if the key is missing (without echoing any value)
- [ ] Anthropic endpoint pinned in settings: `anthropic_base_url = "https://api.anthropic.com"`, **not** overridable from
      env (LG-002 found `LANGSMITH_GATEWAY` / `ANTHROPIC_BASE_URL` can silently reroute model traffic)
- [ ] `.env.example` says LangSmith and Anthropic-routing vars are intentionally unsupported
- [ ] All checks green

Tracing kill switch, env scrubbing, and the network canary test are split out into **LG-016**.

## 🔍 Breakdown

## 🛠️ Approach

## 🧑‍💻 Session plan

## 📝 What I learned
