"""FastAPI entry point.

Run locally:  uv run uvicorn lango.main:app --reload
"""

from fastapi import FastAPI

from lango import __version__

app = FastAPI(title="lango", version=__version__)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe: the app is up. Says nothing about the model or secrets."""
    return {"status": "ok", "version": __version__}
