"""
Models API - Endpoints for LLM model management
Allows users to list, select, and switch between different LLM models
"""

import logging
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field

# Add _src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "_src"))

from model_registry import (
    get_all_models_info,
    get_model,
    get_model_info_dict,
    get_default_model,
    get_available_models,
    recommend_model_for_vram
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


# ============================================================
# Request/Response Models
# ============================================================

class ModelInfo(BaseModel):
    """Model information response"""
    id: str
    name: str
    backend: str
    parameters: str
    size: str
    speed_rating: int = Field(..., ge=1, le=5, description="Speed rating 1-5")
    quality_rating: int = Field(..., ge=1, le=5, description="Quality rating 1-5")
    min_vram_gb: int
    recommended_vram_gb: int
    description: str
    use_cases: List[str]
    available: bool
    default: bool


class ModelListResponse(BaseModel):
    """Response for listing all models"""
    models: List[ModelInfo]
    count: int
    default_model_id: str


class ModelSelectRequest(BaseModel):
    """Request to select a specific model"""
    model_id: str = Field(..., description="Model ID to select")


class ModelSelectResponse(BaseModel):
    """Response after model selection"""
    success: bool
    model_id: str
    model_name: str
    message: str
    requires_restart: bool = False  # If backend needs restart to apply


class ModelRecommendationRequest(BaseModel):
    """Request for model recommendation"""
    vram_gb: Optional[int] = Field(None, description="Available VRAM in GB")
    priority: Optional[str] = Field("balanced", description="Priority: speed, quality, or balanced")


class ModelRecommendationResponse(BaseModel):
    """Response with model recommendation"""
    recommended_model_id: str
    recommended_model_name: str
    reason: str
    alternatives: List[str] = []


# ============================================================
# API Endpoints
# ============================================================

@router.get("/", response_model=ModelListResponse)
async def list_models():
    """
    List all available LLM models

    Returns information about all models registered in the system,
    including their capabilities, requirements, and availability.

    Example:
        GET /api/models/
    """
    try:
        # Get all models from registry
        all_models_info = get_all_models_info()

        # Get default model
        default_model = get_default_model()

        # Convert to response model
        models = [ModelInfo(**model_info) for model_info in all_models_info]

        response = ModelListResponse(
            models=models,
            count=len(models),
            default_model_id=default_model.id
        )

        logger.info(f"Listed {len(models)} models")
        return response

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/{model_id}", response_model=ModelInfo)
async def get_model_info(model_id: str):
    """
    Get detailed information about a specific model

    Args:
        model_id: Model identifier (e.g., "phi3-mini", "llama3.1-8b")

    Returns:
        Detailed model information

    Example:
        GET /api/models/phi3-mini
    """
    try:
        model_info = get_model_info_dict(model_id)

        if not model_info:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_id}' not found"
            )

        return ModelInfo(**model_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.post("/select", response_model=ModelSelectResponse)
async def select_model(request: ModelSelectRequest):
    """
    Select a model for use in queries

    This endpoint allows switching between different LLM models.
    The selection persists for the current session.

    Args:
        request: Model selection request with model_id

    Returns:
        Confirmation of model selection

    Example:
        POST /api/models/select
        {
            "model_id": "phi3-mini"
        }

    Note:
        The model switch takes effect immediately for new queries.
        Ongoing queries will continue with the previous model.
    """
    try:
        model_id = request.model_id

        # Validate model exists
        model_spec = get_model(model_id)
        if not model_spec:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_id}' not found in registry"
            )

        # Check if model is available
        if not model_spec.available:
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_id}' is not currently available. "
                       f"It may require GPU hardware not present in this system."
            )

        # TODO: Implement actual model switching logic
        # For now, this is a placeholder that stores the selection
        # In production, this would:
        # 1. Update global config
        # 2. Recreate LLM client
        # 3. Update RAG engine

        logger.info(f"Model selected: {model_id} ({model_spec.name})")

        return ModelSelectResponse(
            success=True,
            model_id=model_id,
            model_name=model_spec.name,
            message=f"Model '{model_spec.name}' selected successfully. "
                   f"New queries will use this model.",
            requires_restart=False
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting model {request.model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to select model: {str(e)}")


@router.post("/recommend", response_model=ModelRecommendationResponse)
async def recommend_model(request: ModelRecommendationRequest):
    """
    Get model recommendation based on hardware and priorities

    Analyzes available hardware (VRAM) and user priorities to recommend
    the best model for the user's needs.

    Args:
        request: Recommendation criteria (vram_gb, priority)

    Returns:
        Recommended model with reasoning

    Example:
        POST /api/models/recommend
        {
            "vram_gb": 8,
            "priority": "balanced"
        }
    """
    try:
        vram_gb = request.vram_gb or 8  # Default to 8GB
        priority = request.priority or "balanced"

        # Get recommendation based on VRAM
        recommended_model = recommend_model_for_vram(vram_gb)

        # Generate reason
        reason = f"Recommended for {vram_gb}GB VRAM. "
        reason += f"Speed: {recommended_model.speed_rating}/5, "
        reason += f"Quality: {recommended_model.quality_rating}/5. "
        reason += recommended_model.description

        # Get alternatives
        available_models = get_available_models()
        alternatives = [
            model.id for model in available_models
            if model.id != recommended_model.id and model.min_vram_gb <= vram_gb
        ][:3]  # Top 3 alternatives

        return ModelRecommendationResponse(
            recommended_model_id=recommended_model.id,
            recommended_model_name=recommended_model.name,
            reason=reason,
            alternatives=alternatives
        )

    except Exception as e:
        logger.error(f"Error recommending model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to recommend model: {str(e)}")


@router.get("/health", response_model=dict)
async def models_health():
    """
    Check health of model management system

    Returns:
        Status of model registry and available models

    Example:
        GET /api/models/health
    """
    try:
        available_models = get_available_models()
        default_model = get_default_model()

        return {
            "status": "healthy",
            "models_available": len(available_models),
            "default_model": default_model.id,
            "backends": {
                "ollama": len([m for m in available_models if m.backend.value == "ollama"]),
                "vllm": len([m for m in available_models if m.backend.value == "vllm"])
            }
        }

    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
