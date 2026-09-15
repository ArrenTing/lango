---
id: LG-008
title: Investigate hosting that only I can reach
status: todo
priority: P2
milestone: M2 Private on my phone
mode: guided
labels: [investigation, privacy, hosting]
depends: []
---

## 🧭 The problem, in plain words

"A URL only I know" isn't real privacy, because URLs leak. I need lango reachable from my phone anywhere, but
invisible or locked to everyone else, and cheap to run.

## ❓ Questions for the investigation agent

1. Private network option: run on a home PC / small cloud VM behind Tailscale (or similar). Setup effort, cost, phone UX, HTTPS?
2. Public cloud option (Fly.io, Railway, Render, Cloud Run): cost for one user, cold starts vs "real-time", and which auth we'd have to build.
3. Which option gives the smallest attack surface for the least work?
4. What does CD look like for each (image to GHCR, deploy on push to `main`)?

## ✅ Done when

- [ ] Findings + recommendation written here
- [ ] LG-009 (auth) and LG-010 (CD) updated to match the chosen option

## 🔍 Breakdown

## 🛠️ Approach

## 📝 What I learned
