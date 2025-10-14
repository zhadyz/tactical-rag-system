"""
Settings and configuration API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from ..models.schemas import SettingsUpdate, SettingsResponse
from ..core.rag_engine import RAGEngine
from .query import get_rag_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    engine: RAGEngine = Depends(get_rag_engine)
) -> SettingsResponse:
    """
    Get current runtime settings.

    **Returns current values for:**
    - `simple_k`: Results for simple queries
    - `hybrid_k`: Results for hybrid queries
    - `advanced_k`: Results for advanced queries
    - `rerank_weight`: Weight for reranker (0-1)
    - `rrf_constant`: Reciprocal Rank Fusion constant
    - `simple_threshold`: Max complexity score for simple classification
    - `moderate_threshold`: Max complexity score for moderate classification

    **Example Response:**
    ```json
    {
        "success": true,
        "message": "Current settings retrieved",
        "current_settings": {
            "simple_k": 5,
            "hybrid_k": 20,
            "advanced_k": 15,
            "rerank_weight": 0.7,
            "rrf_constant": 60,
            "simple_threshold": 1,
            "moderate_threshold": 3
        }
    }
    ```
    """
    try:
        return SettingsResponse(
            success=True,
            message="Current settings retrieved",
            current_settings=engine.runtime_settings.copy()
        )

    except Exception as e:
        logger.error(f"Get settings error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get settings: {str(e)}"
        )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    settings: SettingsUpdate,
    engine: RAGEngine = Depends(get_rag_engine)
) -> SettingsResponse:
    """
    Update runtime settings.

    Only provide the settings you want to change. Omitted settings remain unchanged.

    **Parameters:**
    - `simple_k` (1-50): Number of results for simple queries
    - `hybrid_k` (5-40): Number of results for hybrid queries
    - `advanced_k` (5-30): Number of results for advanced queries
    - `rerank_weight` (0.0-1.0): Weight for reranker scores
    - `rrf_constant` (1-100): RRF constant for score fusion
    - `simple_threshold` (0-10): Max score for simple classification
    - `moderate_threshold` (0-10): Max score for moderate classification

    **Example Request:**
    ```json
    {
        "simple_k": 7,
        "rerank_weight": 0.8
    }
    ```

    **Example Response:**
    ```json
    {
        "success": true,
        "message": "Updated settings: simple_k, rerank_weight",
        "current_settings": {
            "simple_k": 7,
            "hybrid_k": 20,
            "advanced_k": 15,
            "rerank_weight": 0.8,
            ...
        }
    }
    ```
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        settings_dict = settings.model_dump(exclude_none=True)

        # Update settings
        success, message, current_settings = engine.update_settings(**settings_dict)

        return SettingsResponse(
            success=success,
            message=message,
            current_settings=current_settings
        )

    except Exception as e:
        logger.error(f"Update settings error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        )


@router.post("/settings/reset", response_model=SettingsResponse)
async def reset_settings(
    engine: RAGEngine = Depends(get_rag_engine)
) -> SettingsResponse:
    """
    Reset all settings to default values.

    **Default values:**
    - `simple_k`: 5
    - `hybrid_k`: 20
    - `advanced_k`: 15
    - `rerank_weight`: 0.7
    - `rrf_constant`: 60
    - `simple_threshold`: 1
    - `moderate_threshold`: 3

    **Returns:**
    ```json
    {
        "success": true,
        "message": "Settings reset to defaults",
        "current_settings": { ... }
    }
    ```
    """
    try:
        current_settings = engine.reset_settings()

        return SettingsResponse(
            success=True,
            message="Settings reset to defaults",
            current_settings=current_settings
        )

    except Exception as e:
        logger.error(f"Reset settings error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset settings: {str(e)}"
        )
