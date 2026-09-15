"""Chat model factory (LG-016).

`build_chat_model()` is the only place `ChatAnthropic` may be constructed. It passes the base URL
and API key explicitly, so no env var (`ANTHROPIC_BASE_URL`, `LANGSMITH_GATEWAY`, ...) can reroute
traffic or swap the key (LG-002).
"""

from langchain_anthropic import ChatAnthropic

from lango.config import ANTHROPIC_BASE_URL, Settings
from lango.privacy import enforce_privacy


def build_chat_model(
    settings: Settings, *, max_retries: int = 2, timeout: float = 30.0
) -> ChatAnthropic:
    """Build the Claude chat model pinned to the Anthropic API.

    Runs `enforce_privacy()` first (idempotent), so a model built outside the FastAPI lifespan,
    such as a script or `uvicorn --lifespan off`, is still guarded. Proxy is explicitly `None`;
    default headers, metadata, MCP servers and user profile are deliberately left unset.
    """
    enforce_privacy()
    return ChatAnthropic(
        model=settings.model,
        api_key=settings.anthropic_api_key,
        base_url=ANTHROPIC_BASE_URL,
        anthropic_proxy=None,
        max_retries=max_retries,
        timeout=timeout,
    )
