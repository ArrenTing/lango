# tickets

lango's lightweight stand-in for Linear. Each ticket is one Markdown file, and [BOARD.md](BOARD.md) is generated from them.

```bash
uv run python tickets/board.py new "Add a copy button to translations"   # new ticket
uv run python tickets/board.py                                           # rebuild the board
```

**Statuses:** `backlog` (someday) → `todo` (ready) → `in-progress` → `review` (testing/security) → `done`, or `blocked`.
**Priority:** P0 (drop everything) … P3 (nice to have).
**Mode:** `guided` (I type the logic, Claude scaffolds) or `fast` (the coding agent builds it).

How a ticket is started, worked, and closed is described in [../CLAUDE.md](../CLAUDE.md#standing-orders).
