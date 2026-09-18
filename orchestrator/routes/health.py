"""Health check endpoint."""

from fastapi import APIRouter

from orchestrator import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Return service health and version info."""
    return {
        "status": "ok",
        "version": __version__,
        "service": "revrag-orchestrator",
    }
