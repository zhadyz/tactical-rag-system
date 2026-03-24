"""
Forge - Health check endpoint.

Reports component-level readiness from the ServiceContainer.
"""

import logging
from fastapi import APIRouter, Request

from ..schemas.common import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.

    Returns component status: vectorstore, llm, cache, embeddings.
    """
    container = getattr(request.app.state, "container", None)

    if container is None:
        return HealthResponse(
            status="initializing",
            components={},
        )

    try:
        components: dict[str, str] = {}

        # Check vectorstore
        try:
            vs = await container.get_vectorstore()
            components["vectorstore"] = "ready" if vs else "unavailable"
        except Exception:
            components["vectorstore"] = "unavailable"

        # Check LLM
        try:
            llm = await container.get_llm()
            components["llm"] = "ready" if llm else "unavailable"
        except Exception:
            components["llm"] = "unavailable"

        # Check cache
        try:
            cache = await container.get_cache()
            components["cache"] = "ready" if cache else "unavailable"
        except Exception:
            components["cache"] = "unavailable"

        # Check embeddings
        try:
            emb = await container.get_embeddings()
            components["embeddings"] = "ready" if emb else "unavailable"
        except Exception:
            components["embeddings"] = "unavailable"

        all_ready = all(s == "ready" for s in components.values())
        status = "healthy" if all_ready else "degraded"

        return HealthResponse(status=status, components=components)

    except Exception as e:
        logger.error("Health check failed: %s", e, exc_info=True)
        return HealthResponse(status="unhealthy", components={})
