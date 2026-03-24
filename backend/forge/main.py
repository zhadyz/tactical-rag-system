"""
Forge - FastAPI Application Entry Point

Replaces the ATLAS Protocol main.py with a clean DI container pattern.
ServiceContainer is attached to app.state and accessed via request.app.state.container.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import load_config
from .api import query, documents, settings, models, health

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter (global, attached to app.state)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: build and initialize ServiceContainer. Shutdown: teardown."""

    logger.info("=" * 70)
    logger.info("STARTING FORGE BACKEND")
    logger.info("=" * 70)

    try:
        # Late import to avoid circular dependency — container.py may still be
        # in-flight from infra-agent.
        from .container import ServiceContainer

        config = load_config()
        container = ServiceContainer(config)
        await container.initialize()
        app.state.container = container

        logger.info("=" * 70)
        logger.info("FORGE BACKEND READY — Listening on port %d", config.api_port)
        logger.info("=" * 70)

        yield

    except Exception as e:
        logger.error("Startup failed: %s", e, exc_info=True)
        raise

    # Shutdown
    logger.info("Shutting down Forge backend…")
    if hasattr(app.state, "container"):
        await app.state.container.shutdown()
    logger.info("Forge backend stopped.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Forge API",
    description=(
        "Forge — Agentic Document Intelligence System.\n\n"
        "A LangGraph-powered RAG backend with BGE-M3 multi-representation "
        "embeddings, corrective RAG, ColBERT reranking, and self-verification."
    ),
    version="5.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — restrict in production via CORS_ORIGINS env var
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["root"])
async def root() -> Dict:
    return {
        "name": "Forge API",
        "version": "5.0.0",
        "status": "operational",
        "documentation": {"swagger": "/docs", "redoc": "/redoc"},
        "endpoints": {
            "health": "/api/health",
            "query": "/api/query",
            "query_stream": "/api/query/stream",
            "documents": "/api/documents",
            "settings": "/api/settings",
            "models": "/api/models",
        },
    }


# ---------------------------------------------------------------------------
# Include routers
# ---------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(query.router)
app.include_router(documents.router)
app.include_router(settings.router)
app.include_router(models.router)
