"""
Forge - Common Pydantic schemas (health, errors).
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    version: str = "5.0.0"
    components: Dict[str, str] = {}  # component -> status


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
