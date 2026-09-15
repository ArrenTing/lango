---
id: LG-017
title: Re-check for phone-home code on dependency updates
status: backlog
priority: P3
milestone: M0 Foundation
mode: fast
labels: [privacy, security, ci]
depends: [LG-016]
---

## 🧭 The problem, in plain words

LG-002's "nothing phones home" is only true for today's versions. Dependabot will bump LangChain/LangGraph every
week, and a new release could add a new way out (like the LangSmith gateway). I want updates re-checked automatically.

## ✅ Done when

- [ ] CI runs the LG-016 canary test on every Dependabot PR (it already runs on all PRs; confirm it covers the hostile-env cases)
- [ ] Security agent checklist gains a step: on dependency bumps, grep new versions for new env switches / HTTP clients
      (`LANGSMITH_`, `GATEWAY`, `BASE_URL`, `telemetry`, `httpx`, `requests`) and diff against LG-002 findings
- [ ] Yearly reminder to re-read Anthropic's retention/training pages (policies change)
