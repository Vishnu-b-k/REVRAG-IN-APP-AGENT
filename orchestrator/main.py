"""FastAPI application entrypoint for the RevRag Orchestrator."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from orchestrator import __version__
from orchestrator.routes.health import router as health_router
from orchestrator.routes.ingest import router as ingest_router
from orchestrator.routes.pack import router as pack_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Startup — placeholder for future session store init
    yield
    # Shutdown — placeholder for cleanup


app = FastAPI(
    title="RevRag Orchestrator",
    description="Backend orchestrator for the RevRag In-App Agent — autonomous Android exploration, "
                "screen understanding, and knowledge-pack generation.",
    version=__version__,
    lifespan=lifespan,
)

# CORS — permissive for hackathon (viewer and Android may call from different origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(pack_router)


if __name__ == "__main__":
    import uvicorn
    from orchestrator.config import settings

    uvicorn.run(
        "orchestrator.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
