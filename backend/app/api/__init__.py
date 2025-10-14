"""
API endpoints for FastAPI
"""

from .query import router as query_router
from .settings import router as settings_router

__all__ = ["query_router", "settings_router"]
