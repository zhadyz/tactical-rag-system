"""
Forge - Settings management endpoints.

GET / PUT / POST reset for runtime configuration.
Adapted from ATLAS app/api/settings.py with container-based DI.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["settings"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class SettingsUpdate(BaseModel):
    """Partial-update request — only provided fields are changed."""
    mode: Optional[str] = None           # "direct" | "agentic"
    initial_k: Optional[int] = Field(None, ge=1, le=200)
    rerank_k: Optional[int] = Field(None, ge=1, le=100)
    final_k: Optional[int] = Field(None, ge=1, le=50)
    dense_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    sparse_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=64, le=8192)
    show_agent_reasoning: Optional[bool] = None


class SettingsResponse(BaseModel):
    success: bool
    message: str
    current_settings: dict


# ---------------------------------------------------------------------------
# Defaults (mirrors ForgeConfig.retrieval + agent)
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "mode": "direct",
    "initial_k": 100,
    "rerank_k": 30,
    "final_k": 8,
    "dense_weight": 0.5,
    "sparse_weight": 0.5,
    "similarity_threshold": 0.5,
    "temperature": 0.0,
    "max_tokens": 2048,
    "show_agent_reasoning": False,
}

# Runtime settings (mutated in place, reset on restart)
_runtime_settings: dict = dict(_DEFAULTS)


def _get_container(request: Request):
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(status_code=503, detail="Forge backend is still initializing.")
    return container


# ---------------------------------------------------------------------------
# GET /api/settings
# ---------------------------------------------------------------------------
@router.get("/settings", response_model=SettingsResponse)
async def get_settings(request: Request) -> SettingsResponse:
    _get_container(request)  # ensure initialized

    return SettingsResponse(
        success=True,
        message="Current settings retrieved",
        current_settings=dict(_runtime_settings),
    )


# ---------------------------------------------------------------------------
# PUT /api/settings
# ---------------------------------------------------------------------------
@router.put("/settings", response_model=SettingsResponse)
async def update_settings(request: Request, body: SettingsUpdate) -> SettingsResponse:
    _get_container(request)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        return SettingsResponse(
            success=True,
            message="No changes requested",
            current_settings=dict(_runtime_settings),
        )

    _runtime_settings.update(updates)
    updated_keys = ", ".join(updates.keys())
    logger.info("[SETTINGS] Updated: %s", updated_keys)

    return SettingsResponse(
        success=True,
        message=f"Updated settings: {updated_keys}",
        current_settings=dict(_runtime_settings),
    )


# ---------------------------------------------------------------------------
# POST /api/settings/reset
# ---------------------------------------------------------------------------
@router.post("/settings/reset", response_model=SettingsResponse)
async def reset_settings(request: Request) -> SettingsResponse:
    _get_container(request)
    _runtime_settings.clear()
    _runtime_settings.update(_DEFAULTS)

    return SettingsResponse(
        success=True,
        message="Settings reset to defaults",
        current_settings=dict(_runtime_settings),
    )
