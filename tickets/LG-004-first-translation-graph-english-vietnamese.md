---
id: LG-004
title: First translation graph (English ⇄ Vietnamese)
status: todo
priority: P1
milestone: M1 Text translation
mode: guided
labels: [langgraph, llm]
depends: [LG-003, LG-016]
---

## 🧭 The problem, in plain words

The heart of lango: give it a sentence in English or Vietnamese and get a natural translation in the other
language. Built as a tiny LangGraph so we can grow it later (detect language → translate → polish).

## ✅ Done when

- [ ] A LangGraph `StateGraph` with a typed state and a `translate` node using `ChatAnthropic`
- [ ] Source language is detected; output is always the *other* language
- [ ] The other person's text is data in the human message, never inside the system prompt
- [ ] Unit tests with a fake chat model (no network), including a prompt-injection test
- [ ] One `live_llm` test I can run by hand with a real key

## 🔍 Breakdown

## 🛠️ Approach

## 🧑‍💻 Session plan

## 📝 What I learned
