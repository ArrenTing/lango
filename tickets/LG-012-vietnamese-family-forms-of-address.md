---
id: LG-012
title: Vietnamese family forms of address
status: backlog
priority: P2
milestone: M3 Conversation mode
mode: guided
labels: [llm, prompt]
depends: [LG-004]
---

## 🧭 The problem, in plain words

Vietnamese has no neutral "I/you". Talking to my mother-in-law, the translation should say *con* for me and *mẹ*
for her, not a stiff or rude default. The translator needs to know who is talking to whom.

## ✅ Done when

- [ ] A small "people" profile (me, her, relationship) feeds the prompt as context, not as instructions from the chat
- [ ] Example-based tests on a handful of phrases (live eval, run by hand)
