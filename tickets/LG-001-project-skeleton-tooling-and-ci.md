---
id: LG-001
title: Project skeleton, tooling and CI
status: done
priority: P0
milestone: M0 Foundation
mode: fast
labels: [infra]
depends: []
---

## 🧭 The problem, in plain words

Before writing any translator code I need a clean, modern Python project that checks itself on every push, so I
can move fast without breaking things.

## ✅ Done when

- [x] `uv` project on Python 3.14 with FastAPI, pydantic-settings, LangGraph, langchain-anthropic, Jinja2
- [x] ruff (format + lint), mypy `--strict`, pytest + coverage, pip-audit
- [x] `/health` endpoint with a test
- [x] GitHub Actions CI on push/PR to `main`; Dependabot for uv + actions
- [x] CLAUDE.md standing orders, agents (investigation, coding, testing, security), ticket board
- [x] Public repo `ArrenTing/lango`, CI green

## 📝 What I learned

<!-- Arren writes this -->
