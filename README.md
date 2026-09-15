# lango 🗣️

A private, real-time AI translator I built for myself, so I can chat with family in Vietnamese
(English ⇄ Vietnamese first, more languages later). I open it on my phone, type or talk, and
lango translates both sides of the conversation as fast as the model allows.

It's a personal tool first and a portfolio project second. Every feature exists because I use it.

## Principles

- **Private by default.** Only I can reach it. Conversations go to the Anthropic API for
  translation and nowhere else: no tracing services, no analytics, no third-party logging.
- **Modern Python.** Python 3.14, `uv`, FastAPI, Pydantic v2, LangGraph + LangChain (Anthropic).
- **Built by hand, with an AI pair.** I write the core code myself in guided sessions. See
  [CLAUDE.md](CLAUDE.md) for the workflow and [tickets/BOARD.md](tickets/BOARD.md) for progress.

## Quickstart

```bash
uv sync                                   # install Python 3.14 + dependencies
cp .env.example .env                      # then add your ANTHROPIC_API_KEY
uv run uvicorn lango.main:app --reload    # http://127.0.0.1:8000/health
```

## Checks (same as CI)

```bash
uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest
```

## Status

Early days. Milestones and tickets live in [tickets/](tickets/BOARD.md).
