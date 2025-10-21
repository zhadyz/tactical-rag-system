"""
Document Coverage Validation API
Shows which files are indexed vs which are in the documents folder
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
import logging
from pathlib import Path
import hashlib

from ..core.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Global RAG engine instance (initialized in main.py)
_rag_engine: RAGEngine = None


def set_rag_engine(engine: RAGEngine):
    """Set the global RAG engine instance"""
    global _rag_engine
    _rag_engine = engine


def get_rag_engine() -> RAGEngine:
    """Dependency to get RAG engine"""
    if _rag_engine is None or not _rag_engine.initialized:
        raise HTTPException(
            status_code=503,
            detail="RAG Engine not initialized. Please wait for system startup."
        )
    return _rag_engine


class FileCoverage(BaseModel):
    filename: str
    path: str
    indexed: bool
    size_bytes: int
    sha256: str


class CoverageResponse(BaseModel):
    total_files: int
    indexed_files: int
    missing_files: int
    coverage_percentage: float
    files: List[FileCoverage]


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.warning(f"Failed to hash {file_path}: {e}")
        return ""


@router.get("/coverage", response_model=CoverageResponse)
async def get_document_coverage(
    engine: RAGEngine = Depends(get_rag_engine)
):
    """
    Analyze which documents are indexed vs present in documents folder.

    **Returns:**
    - `total_files`: Total PDF/DOCX files found
    - `indexed_files`: Number of files found in vector database
    - `missing_files`: Files present but not indexed
    - `coverage_percentage`: Percentage of files indexed
    - `files`: Detailed list of each file's status

    **Use Case:**
    Identify which documents need reindexing without destroying existing index.
    """
    try:
        # Get all documents from folder
        documents_dir = Path("/app/documents")
        if not documents_dir.exists():
            documents_dir.mkdir(parents=True, exist_ok=True)

        # Find all supported documents
        supported_extensions = {".pdf", ".docx", ".doc", ".txt", ".md"}
        all_files = []

        for ext in supported_extensions:
            all_files.extend(documents_dir.rglob(f"*{ext}"))

        # Get indexed documents from ChromaDB
        indexed_sources = set()
        try:
            collection = engine.vectorstore._collection
            # Get all unique source filenames from metadata
            results = collection.get(include=["metadatas"])
            for metadata in results.get("metadatas", []):
                if metadata and "source" in metadata:
                    source_path = Path(metadata["source"])
                    indexed_sources.add(source_path.name)
        except (Exception) as e:
            logger.warning(f"Could not access vector database: {e}")
            indexed_sources = set()

        # Build coverage report
        files = []
        for file_path in sorted(all_files):
            is_indexed = file_path.name in indexed_sources

            try:
                size = file_path.stat().st_size
                sha256 = calculate_sha256(file_path)
            except Exception as e:
                logger.warning(f"Could not stat {file_path}: {e}")
                size = 0
                sha256 = ""

            files.append(FileCoverage(
                filename=file_path.name,
                path=str(file_path.relative_to(documents_dir)),
                indexed=is_indexed,
                size_bytes=size,
                sha256=sha256
            ))

        # Calculate statistics
        total_files = len(files)
        indexed_count = sum(1 for f in files if f.indexed)
        missing_count = total_files - indexed_count
        coverage_pct = (indexed_count / total_files * 100) if total_files > 0 else 0.0

        return CoverageResponse(
            total_files=total_files,
            indexed_files=indexed_count,
            missing_files=missing_count,
            coverage_percentage=round(coverage_pct, 1),
            files=files
        )

    except Exception as e:
        logger.error(f"Coverage analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze document coverage: {str(e)}"
        )
