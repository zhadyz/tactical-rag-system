"""
Forge - Model control endpoints.

Runtime model switching (hotswap) adapted from ATLAS model_control.py.
Accesses ModelManager via ServiceContainer instead of global injection.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


# ---------------------------------------------------------------------------
# Schemas (kept local — small and specific to this router)
# ---------------------------------------------------------------------------
class ModelInfo(BaseModel):
    id: str
    name: str
    backend: str
    description: str
    expected_vram_gb: float
    expected_tokens_per_sec: float
    active: bool = False


class ModelSwitchRequest(BaseModel):
    model_id: str


class ModelSwitchResponse(BaseModel):
    success: bool
    message: str
    previous_model: Optional[str] = None
    current_model: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_container(request: Request):
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(status_code=503, detail="Forge backend is still initializing.")
    return container


# ---------------------------------------------------------------------------
# GET /api/models/available
# ---------------------------------------------------------------------------
@router.get("/available", response_model=List[ModelInfo])
async def get_available_models(request: Request):
    """List available LLM models for hotswapping."""
    container = _get_container(request)

    try:
        manager = await container.get_model_manager()
        return manager.get_available_models()
    except Exception as e:
        logger.error("Error getting available models: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /api/models/current
# ---------------------------------------------------------------------------
@router.get("/current", response_model=ModelInfo)
async def get_current_model(request: Request):
    """Get the currently active model."""
    container = _get_container(request)

    try:
        manager = await container.get_model_manager()
        current = manager.get_current_model()
        if not current:
            raise HTTPException(status_code=404, detail="No model loaded")
        current["active"] = True
        return current
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting current model: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /api/models/switch
# ---------------------------------------------------------------------------
@router.post("/switch", response_model=ModelSwitchResponse)
async def switch_model(request: Request, body: ModelSwitchRequest):
    """Switch to a different model at runtime."""
    container = _get_container(request)

    try:
        manager = await container.get_model_manager()

        if manager.is_switching():
            raise HTTPException(status_code=409, detail="Model switch already in progress")

        previous = manager.get_current_model()
        previous_id = previous["id"] if previous else None

        logger.info("Model switch requested: %s -> %s", previous_id, body.model_id)

        success = await manager.switch_model(body.model_id)
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to switch to model: {body.model_id}",
            )

        current = manager.get_current_model()
        logger.info("Model hotswap complete: %s -> %s", previous_id, current["id"])

        return ModelSwitchResponse(
            success=True,
            message=f"Successfully switched to {current['name']}",
            previous_model=previous_id,
            current_model=current["id"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error switching model: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /api/models/status
# ---------------------------------------------------------------------------
@router.get("/status")
async def get_model_status(request: Request):
    """Get detailed model manager status."""
    container = _get_container(request)

    try:
        manager = await container.get_model_manager()
        current = manager.get_current_model()
        return {
            "initialized": manager.initialized,
            "switching": manager.is_switching(),
            "current_model": current,
            "available_models_count": len(manager.PROFILES),
        }
    except Exception as e:
        logger.error("Error getting model status: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
