"""
Forge - Document management endpoints.

Handles upload, listing, deletion, reindex, and the new ingestion pipeline trigger.
"""

import asyncio
import hashlib
import logging
import threading
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from werkzeug.utils import secure_filename

from ..schemas.documents import (
    DocumentInfo,
    DocumentListResponse,
    ReindexResponse,
    IngestStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Concurrency lock for reindex / ingest operations
_ingest_lock = threading.Lock()

# In-memory ingestion status (shared across requests)
_ingest_status: dict = {
    "status": "idle",
    "progress": 0.0,
    "current_document": None,
    "documents_total": 0,
    "documents_completed": 0,
    "errors": [],
}


def _get_container(request: Request):
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(status_code=503, detail="Forge backend is still initializing.")
    return container


# ---------------------------------------------------------------------------
# GET /api/documents — list indexed documents
# ---------------------------------------------------------------------------
@router.get("", response_model=DocumentListResponse)
async def list_documents(request: Request) -> DocumentListResponse:
    """List all indexed documents with metadata."""
    container = _get_container(request)

    try:
        vs = await container.get_vectorstore()

        # Ask vectorstore for document inventory (interface defined in infra)
        if hasattr(vs, "list_documents"):
            docs = await vs.list_documents()
            return DocumentListResponse(
                documents=[DocumentInfo(**d) for d in docs],
                total=len(docs),
            )

        # Fallback: return empty list
        return DocumentListResponse(documents=[], total=0)

    except Exception as e:
        logger.error("Error listing documents: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {e}")


# ---------------------------------------------------------------------------
# POST /api/documents/upload — upload a new document
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc", ".md"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
) -> JSONResponse:
    """Upload a new document. Accepts PDF, TXT, DOCX, DOC, MD."""
    container = _get_container(request)

    # Sanitize filename (prevents path traversal)
    sanitized = secure_filename(file.filename or "")
    if not sanitized:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    ext = Path(sanitized).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(content) / 1024 / 1024:.1f}MB. Maximum: 50MB.",
        )

    # Duplicate check via SHA-256
    file_hash = hashlib.sha256(content).hexdigest()
    docs_dir = container.config.documents_dir
    docs_dir.mkdir(parents=True, exist_ok=True)

    for existing in docs_dir.rglob("*"):
        if existing.is_file() and existing.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                if hashlib.sha256(existing.read_bytes()).hexdigest() == file_hash:
                    return JSONResponse(
                        status_code=200,
                        content={
                            "success": True,
                            "message": f"File already exists as '{existing.name}' (duplicate detected)",
                            "file_name": existing.name,
                            "duplicate": True,
                            "sha256": file_hash,
                        },
                    )
            except Exception:
                continue

    # Path traversal guard
    file_path = (docs_dir / sanitized).resolve()
    if not str(file_path).startswith(str(docs_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file path detected.")

    if file_path.exists():
        raise HTTPException(
            status_code=409,
            detail=f"File '{sanitized}' already exists. Delete it first or use a different name.",
        )

    file_path.write_bytes(content)
    logger.info("[UPLOAD] Saved %s (%d bytes, SHA256=%s…)", sanitized, len(content), file_hash[:16])

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": f"File '{sanitized}' uploaded successfully",
            "file_name": sanitized,
            "file_size_bytes": len(content),
            "note": "Run /api/ingest or /api/documents/reindex to process this document",
        },
    )


# ---------------------------------------------------------------------------
# DELETE /api/documents/{doc_id}
# ---------------------------------------------------------------------------
@router.delete("/{doc_id}")
async def delete_document(request: Request, doc_id: str):
    """Delete a document by ID."""
    container = _get_container(request)

    try:
        vs = await container.get_vectorstore()
        if hasattr(vs, "delete_document"):
            await vs.delete_document(doc_id)
            return {"success": True, "message": f"Document {doc_id} deleted."}

        raise HTTPException(status_code=501, detail="Document deletion not supported by vectorstore.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting document %s: %s", doc_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {e}")


# ---------------------------------------------------------------------------
# POST /api/documents/reindex — legacy reindex (simpler pipeline)
# ---------------------------------------------------------------------------
@router.post("/reindex", response_model=ReindexResponse)
async def reindex_documents(request: Request) -> ReindexResponse:
    """Trigger reindexing of all documents (legacy path)."""
    if not _ingest_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Ingestion already in progress.")

    container = _get_container(request)

    try:
        start = time.time()
        vs = await container.get_vectorstore()

        if hasattr(vs, "reindex_all"):
            result = await vs.reindex_all(container.config.documents_dir)
            elapsed = time.time() - start
            return ReindexResponse(
                status="completed",
                documents_processed=result.get("count", 0),
                message=f"Reindexing completed in {elapsed:.1f}s",
            )

        return ReindexResponse(status="completed", documents_processed=0, message="No-op: reindex not implemented.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Reindex error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {e}")
    finally:
        _ingest_lock.release()


# ---------------------------------------------------------------------------
# POST /api/ingest — trigger full Forge ingestion pipeline (background)
# ---------------------------------------------------------------------------
@router.post("/ingest")
async def trigger_ingest(request: Request):
    """
    Start the full Forge ingestion pipeline as a background task.

    Pipeline: parse -> hierarchical chunk -> contextual enrich -> proposition
    extract -> knowledge graph build -> BGE-M3 multi-representation index.
    """
    global _ingest_status

    if not _ingest_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Ingestion already in progress.")

    container = _get_container(request)
    task_id = str(uuid.uuid4())

    _ingest_status = {
        "status": "running",
        "progress": 0.0,
        "current_document": None,
        "documents_total": 0,
        "documents_completed": 0,
        "errors": [],
    }

    async def _run_ingest():
        global _ingest_status
        try:
            # Import ingestion pipeline (built by infra-agent)
            from ..ingestion.indexer import run_ingestion_pipeline

            await run_ingestion_pipeline(container, _ingest_status)
            _ingest_status["status"] = "completed"
            _ingest_status["progress"] = 1.0
        except Exception as e:
            logger.error("Ingestion failed: %s", e, exc_info=True)
            _ingest_status["status"] = "failed"
            _ingest_status["errors"].append(str(e))
        finally:
            _ingest_lock.release()

    asyncio.create_task(_run_ingest())

    return {
        "success": True,
        "message": "Ingestion pipeline started.",
        "task_id": task_id,
    }


# ---------------------------------------------------------------------------
# GET /api/ingest/status
# ---------------------------------------------------------------------------
@router.get("/ingest/status", response_model=IngestStatusResponse)
async def ingest_status():
    """Get current ingestion pipeline progress."""
    return IngestStatusResponse(**_ingest_status)
