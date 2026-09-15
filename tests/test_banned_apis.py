"""No code in src/ may use APIs that send data outside the Anthropic API (LG-002, LG-016).

Ruff's banned-api rule catches imports; this grep also catches attribute use and string tricks
that lint can't see (e.g. `graph.get_graph().draw_mermaid_png()` needs no import at all).
"""

import re
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "lango"

# name → (pattern, why it's banned)
BANNED_PATTERNS: dict[str, tuple[re.Pattern[str], str]] = {
    "draw_mermaid_png": (
        re.compile(r"\bdraw_mermaid_png\b"),
        "renders via mermaid.ink by default; use draw_mermaid() text",
    ),
    "LangChainTracer": (re.compile(r"\bLangChainTracer\b"), "uploads runs to LangSmith"),
    "tracing_v2_enabled": (
        re.compile(r"\btracing_v2_enabled\b"),
        "turns LangSmith tracing on, ahead of configure(enabled=False)",
    ),
    "traceable": (re.compile(r"\btraceable\b"), "langsmith decorator that uploads runs"),
    "RemoteGraph": (re.compile(r"\bRemoteGraph\b"), "sends graph runs to a LangGraph server"),
    "langsmith.Client": (re.compile(r"\blangsmith\.Client\b"), "LangSmith API client"),
    "Client imported from langsmith": (
        re.compile(r"^\s*from\s+langsmith(\.\w+)*\s+import\s+[^#\n]*\bClient\b", re.MULTILINE),
        "LangSmith API client",
    ),
}


def source_files() -> list[Path]:
    return sorted(SRC_DIR.rglob("*.py"))


def test_source_tree_is_found() -> None:
    # Guards against the grep below silently passing because it scanned nothing.
    assert SRC_DIR.is_dir()
    assert source_files(), f"no .py files under {SRC_DIR}"


@pytest.mark.parametrize("banned", list(BANNED_PATTERNS))
def test_src_does_not_use_banned_network_api(banned: str) -> None:
    # Arrange
    pattern, reason = BANNED_PATTERNS[banned]

    # Act
    hits = [
        f"{path.relative_to(SRC_DIR.parent)}:{text.count(chr(10), 0, match.start()) + 1}"
        for path in source_files()
        for text in [path.read_text(encoding="utf-8")]
        for match in pattern.finditer(text)
    ]

    # Assert
    assert hits == [], f"`{banned}` is banned in src/ ({reason}). Found at: {hits}"
