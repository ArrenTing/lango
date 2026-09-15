---
id: LG-002
title: Investigate what data LangGraph and LangChain send anywhere
status: todo
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

- [ ] Findings with file:line / doc evidence written into this ticket
- [ ] A one-paragraph privacy statement I agree with, ready for the README
- [ ] Follow-up tickets created for anything we need to enforce in code (feeds LG-003)

## 🔍 Breakdown

## 🛠️ Approach

## 📝 What I learned
