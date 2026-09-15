---
id: LG-013
title: Private conversation memory
status: backlog
priority: P3
milestone: M3 Conversation mode
mode: guided
labels: [langgraph, privacy, storage]
depends: [LG-011]
---

## 🧭 The problem, in plain words

Translations get better when Claude sees the last few messages ("it" and "that" make sense). Memory must stay on my
server and disappear on its own.

## ✅ Done when

- [ ] LangGraph checkpointer (local SQLite, git-ignored) keyed by conversation
- [ ] Automatic expiry and a "forget this conversation" button
- [ ] Security agent verdict: PASS
