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

## Privacy

lango sends the text you type, and the other person's replies, to exactly one outside service: the Anthropic API,
which does the translation. It doesn't use LangSmith, analytics, or error-tracking services. Tracing is switched off
in code at startup, and an automated test checks that the app never connects anywhere else *(being built in
[LG-016](tickets/LG-016-startup-privacy-guard-and-network-canary-test.md))*. lango doesn't log message text,
translations, or prompts, only event names, timings, and token counts. Under Anthropic's commercial terms, API
inputs and outputs aren't used to train models by default, and they're deleted within 30 days. Anthropic may keep
content longer if its safety systems flag it (up to 2 years) or if the law requires it
([training](https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training),
[retention](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)).

The evidence behind this statement (library source file:line references and a network canary run) is in
[LG-002](tickets/LG-002-investigate-what-data-langgraph-and-langchain-send.md).

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
