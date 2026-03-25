"""
Forge - Document management schemas.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentInfo(BaseModel):
    id: str
    file_name: str
    file_type: str
    size_bytes: int = 0
    indexed_at: Optional[datetime] = None
    chunk_count: int = 0
    status: str = "indexed"  # "pending" | "indexing" | "indexed" | "failed"


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo] = []
    total: int = 0


class ReindexResponse(BaseModel):
    status: str  # "started" | "completed" | "failed"
    documents_processed: int = 0
    message: str = ""


class IngestStatusResponse(BaseModel):
    status: str  # "idle" | "running" | "completed" | "failed"
    progress: float = 0.0  # 0.0 - 1.0
    current_document: Optional[str] = None
    documents_total: int = 0
    documents_completed: int = 0
    errors: List[str] = []
