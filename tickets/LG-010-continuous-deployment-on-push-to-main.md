---
id: LG-010
title: Continuous deployment on push to main
status: todo
priority: P2
milestone: M2 Private on my phone
mode: fast
labels: [infra, cd]
depends: [LG-008, LG-009]
---

## 🧭 The problem, in plain words

When CI goes green on `main`, the new version should be live on my phone a few minutes later, with no manual deploy.

## ✅ Done when

- [ ] Multi-stage Dockerfile using `uv`, running as non-root
- [ ] GitHub Actions: build → push image to GHCR → deploy to the host chosen in LG-008, only after CI passes
- [ ] Secrets live in GitHub environment secrets; deploy job runs only on `main`, never for PRs from forks
- [ ] Rollback steps noted here

## 🔍 Breakdown

## 🛠️ Approach

## 📝 What I learned
