"""
ATLAS Protocol - Model Control API

Endpoints for runtime model switching and management.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


class ModelInfo(BaseModel):
    """Model information response"""
    id: str
    name: str
    backend: str
    description: str
    expected_vram_gb: float
    expected_tokens_per_sec: float
    active: bool = False


class ModelSwitchRequest(BaseModel):
    """Model switch request"""
    model_id: str


class ModelSwitchResponse(BaseModel):
    """Model switch response"""
    success: bool
    message: str
    previous_model: Optional[str] = None
    current_model: Optional[str] = None


# Global instances (injected by main.py)
_model_manager = None
_rag_engine = None


def set_model_manager(manager):
    """Inject model manager instance"""
    global _model_manager
    _model_manager = manager


def set_rag_engine(engine):
    """Inject RAG engine instance"""
    global _rag_engine
    _rag_engine = engine


def get_model_manager():
    """Dependency to get model manager"""
    if _model_manager is None:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    return _model_manager


def get_rag_engine():
    """Dependency to get RAG engine"""
    if _rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    return _rag_engine


@router.get("/available", response_model=List[ModelInfo])
async def get_available_models(
    manager=Depends(get_model_manager)
):
    """
    Get list of available models for hotswapping.

    Returns:
        List of model profiles with metadata
    """
    try:
        models = manager.get_available_models()
        return models

    except Exception as e:
        logger.error(f"Error getting available models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current", response_model=ModelInfo)
async def get_current_model(
    manager=Depends(get_model_manager)
):
    """
    Get currently active model.

    Returns:
        Active model info
    """
    try:
        current = manager.get_current_model()

        if not current:
            raise HTTPException(status_code=404, detail="No model loaded")

        # Add active flag
        current["active"] = True
        return current

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch", response_model=ModelSwitchResponse)
async def switch_model(
    request: ModelSwitchRequest,
    manager=Depends(get_model_manager),
    rag_engine=Depends(get_rag_engine)
):
    """
    Switch to a different model at runtime.

    Args:
        request: Model switch request with target model_id

    Returns:
        Switch operation result

    Example:
        POST /api/models/switch
        {
            "model_id": "qwen-14b-q8"
        }
    """
    try:
        # Check if switching is already in progress
        if manager.is_switching():
            raise HTTPException(
                status_code=409,
                detail="Model switch already in progress"
            )

        # Get previous model
        previous = manager.get_current_model()
        previous_id = previous["id"] if previous else None

        logger.info(f"Model switch requested: {previous_id} → {request.model_id}")

        # Perform switch at ModelManager level
        success = await manager.switch_model(request.model_id)

        if success:
            # Synchronize RAG engine with new model
            logger.info("Synchronizing RAG engine with new model...")
            sync_success = rag_engine.sync_llm_from_model_manager()

            if not sync_success:
                logger.error("RAG engine sync failed after model switch")
                raise HTTPException(
                    status_code=500,
                    detail="Model switched but RAG engine sync failed"
                )

            current = manager.get_current_model()
            logger.info(f"✓ Model hotswap complete: {previous_id} → {current['id']}")

            return ModelSwitchResponse(
                success=True,
                message=f"Successfully switched to {current['name']}",
                previous_model=previous_id,
                current_model=current["id"]
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to switch to model: {request.model_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_model_status(
    manager=Depends(get_model_manager)
):
    """
    Get detailed model manager status.

    Returns:
        Status information including switching state
    """
    try:
        current = manager.get_current_model()

        return {
            "initialized": manager.initialized,
            "switching": manager.is_switching(),
            "current_model": current,
            "available_models_count": len(manager.PROFILES)
        }

    except Exception as e:
        logger.error(f"Error getting model status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
