---
id: LG-005
title: POST /api/translate endpoint
status: todo
priority: P1
milestone: M1 Text translation
mode: guided
labels: [fastapi]
depends: [LG-004]
---

## 🧭 The problem, in plain words

My phone needs a way to ask the server for a translation. A single HTTP endpoint that takes text and returns the
translation, validated on the way in and out.

## ✅ Done when

- [ ] Pydantic request/response models with a sensible max text length
- [ ] Graph injected with a FastAPI dependency, so tests override it with a fake
- [ ] Errors from the model become a clean 502 without leaking text or keys
- [ ] Endpoint tests with `TestClient`

## 🔍 Breakdown

## 🛠️ Approach

## 🧑‍💻 Session plan

## 📝 What I learned
