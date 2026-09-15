---
id: LG-007
title: Stream translations as they are written
status: todo
priority: P2
milestone: M1 Text translation
mode: guided
labels: [langgraph, streaming, realtime]
depends: [LG-006]
---

## 🧭 The problem, in plain words

Waiting for the whole translation feels slow in a live conversation. Words should appear as Claude writes them,
so it feels real-time.

## ✅ Done when

- [ ] Graph streams tokens (`astream` with `stream_mode="messages"`)
- [ ] FastAPI streams them to the page (Server-Sent Events or WebSocket; decide in Approach)
- [ ] Time-to-first-word measured and noted here, and a faster model tried if it's sluggish
- [ ] Tests for the streaming endpoint with a fake streaming model

## 🔍 Breakdown

## 🛠️ Approach

## 🧑‍💻 Session plan

## 📝 What I learned
