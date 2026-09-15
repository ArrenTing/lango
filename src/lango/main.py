"""FastAPI entry point.

Run locally:  uv run uvicorn lango.main:app --reload
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from lango import __version__
from lango.config import load_settings
from lango.privacy import enforce_privacy


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001 (FastAPI passes the app)
    """Startup: lock down privacy first, then validate settings, before serving (LG-016)."""
    enforce_privacy()
    load_settings()
    yield


app = FastAPI(title="lango", version=__version__, lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe: the app is up. Says nothing about the model or secrets."""
    return {"status": "ok", "version": __version__}
