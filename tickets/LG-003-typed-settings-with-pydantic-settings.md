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
key never printed by accident and tracing guaranteed off, whatever the environment says.

## ✅ Done when

- [ ] `lango.config.Settings` loads from env / `.env`, and the API key is a `SecretStr`
- [ ] App fails fast with a clear message if the key is missing (without echoing any value)
- [ ] Tracing is forced off at startup (per LG-002 findings) with a test proving it
- [ ] All checks green

## 🔍 Breakdown

## 🛠️ Approach

## 🧑‍💻 Session plan

## 📝 What I learned
