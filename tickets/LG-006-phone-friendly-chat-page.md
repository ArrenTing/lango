---
id: LG-006
title: Phone-friendly chat page
status: todo
priority: P2
milestone: M1 Text translation
mode: guided
labels: [frontend]
depends: [LG-005]
---

## 🧭 The problem, in plain words

I want to open a page on my phone, type a message, and see the original and the translation like a chat thread,
with big text and one thumb. No app store, no heavy frontend framework.

## ✅ Done when

- [ ] Jinja2 page served by FastAPI; HTMX posts the message and appends the result
- [ ] Alpine.js for small in-page state (toggles, auto-scroll); HTMX and Alpine both self-hosted from `static/`, no CDN
- [ ] Mobile layout: sticky input at the bottom, large tap targets, works in iOS/Android browsers
- [ ] Model output rendered escaped (no `|safe`)
- [ ] Tested on my actual phone over the local network

## 🔍 Breakdown

## 🛠️ Approach

## 🧑‍💻 Session plan

## 📝 What I learned
