"""
Document management API endpoints
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List
from werkzeug.utils import secure_filename
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse
import threading

from ..models.schemas import DocumentListResponse, DocumentInfo, ReindexResponse
from ..core.rag_engine import RAGEngine

# Import document processor
import sys
src_path = Path(__file__).parent.parent.parent / "_src"
sys.path.insert(0, str(src_path))
from document_processor import DocumentProcessor
from config import load_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Global RAG engine instance (initialized in main.py)
_rag_engine: RAGEngine = None

# CONCURRENCY FIX: Lock to prevent concurrent reindexing operations
_reindex_lock = threading.Lock()


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


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    engine: RAGEngine = Depends(get_rag_engine)
) -> DocumentListResponse:
    """
    List all indexed documents with metadata.

    Returns information about all documents currently indexed in the system,
    including file names, sizes, chunk counts, and processing dates.

    **Returns:**
    - `total_documents`: Total number of indexed documents
    - `total_chunks`: Total number of chunks across all documents
    - `documents`: List of document information
    """
    try:
        logger.info("[API] Listing all indexed documents")

        # Get metadata from chunk_metadata.json
        metadata_file = engine.config.vector_db_dir / "chunk_metadata.json"

        if not metadata_file.exists():
            return DocumentListResponse(
                total_documents=0,
                total_chunks=0,
                documents=[]
            )

        import json
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            metadata = data['metadata']

        # Aggregate documents by file_name
        doc_stats: Dict[str, Dict] = {}

        for meta in metadata:
            file_name = meta.get('file_name', 'Unknown')

            if file_name not in doc_stats:
                doc_stats[file_name] = {
                    'file_name': file_name,
                    'file_type': meta.get('file_type', ''),
                    'file_size_bytes': meta.get('file_size_bytes', 0),
                    'file_hash': meta.get('file_hash', ''),
                    'processing_date': meta.get('processing_date', ''),
                    'num_chunks': 0
                }

            doc_stats[file_name]['num_chunks'] += 1

        # Convert to list
        documents = [DocumentInfo(**doc) for doc in doc_stats.values()]

        # Sort by file name
        documents.sort(key=lambda x: x.file_name)

        result = DocumentListResponse(
            total_documents=len(documents),
            total_chunks=len(metadata),
            documents=documents
        )

        logger.info(f"[API] Found {len(documents)} documents with {len(metadata)} total chunks")
        return result

    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    engine: RAGEngine = Depends(get_rag_engine)
) -> JSONResponse:
    """
    Upload a new document to the system.

    Accepts a file upload and saves it to the documents directory.
    The file will be indexed when reindexing is triggered.

    **Supported formats:**
    - PDF (.pdf)
    - Text (.txt)
    - Word (.docx, .doc)
    - Markdown (.md)

    **Returns:**
    - Success message with file information
    """
    try:
        logger.info(f"[API] Uploading file: {file.filename}")

        # SECURITY FIX: Sanitize filename to prevent path traversal attacks
        # This prevents filenames like "../../../etc/passwd" or "..\\..\\windows\\system32"
        sanitized_filename = secure_filename(file.filename)

        if not sanitized_filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename. Filename must contain valid characters."
            )

        # Validate file extension
        supported_extensions = ['.pdf', '.txt', '.docx', '.doc', '.md']
        file_ext = Path(sanitized_filename).suffix.lower()

        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(supported_extensions)}"
            )

        # Read file content
        content = await file.read()

        # FILE SIZE LIMIT: 50MB industry standard (prevents memory issues)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {len(content) / 1024 / 1024:.1f}MB. Maximum allowed: 50MB"
            )

        # DUPLICATE DETECTION: Check SHA256 hash
        import hashlib
        file_hash = hashlib.sha256(content).hexdigest()

        # Check if file with same hash exists
        documents_dir = engine.config.documents_dir
        documents_dir.mkdir(exist_ok=True)

        duplicate_found = False
        for existing_file in documents_dir.rglob("*"):
            if existing_file.is_file() and existing_file.suffix.lower() in supported_extensions:
                try:
                    with open(existing_file, 'rb') as f:
                        existing_hash = hashlib.sha256(f.read()).hexdigest()
                        if existing_hash == file_hash:
                            duplicate_found = True
                            logger.info(f"[API] Duplicate detected: {file.filename} matches {existing_file.name}")
                            return JSONResponse(
                                status_code=200,
                                content={
                                    "success": True,
                                    "message": f"File already exists as '{existing_file.name}' (duplicate detected)",
                                    "file_name": existing_file.name,
                                    "file_size_bytes": len(content),
                                    "duplicate": True,
                                    "sha256": file_hash
                                }
                            )
                except Exception as e:
                    logger.warning(f"Could not check {existing_file}: {e}")
                    continue

        # Save file to documents directory with sanitized filename
        file_path = documents_dir / sanitized_filename

        # SECURITY FIX: Validate that the resolved path is still within documents_dir
        # This prevents path traversal even if secure_filename() has a bypass
        try:
            resolved_path = file_path.resolve()
            resolved_docs_dir = documents_dir.resolve()

            # Check if the resolved path is a child of documents_dir
            if not resolved_path.is_relative_to(resolved_docs_dir):
                logger.error(f"[SECURITY] Path traversal attempt blocked: {file.filename} -> {resolved_path}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file path detected. Security violation."
                )
        except ValueError:
            # is_relative_to() raises ValueError on Python < 3.9, use alternative
            if not str(resolved_path).startswith(str(resolved_docs_dir)):
                logger.error(f"[SECURITY] Path traversal attempt blocked: {file.filename} -> {resolved_path}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file path detected. Security violation."
                )

        # Check if filename exists (different content)
        if file_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"File '{sanitized_filename}' already exists. Delete it first or use a different name."
            )

        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"[API] File saved: {file_path} ({len(content)} bytes), SHA256: {file_hash[:16]}...")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"File '{sanitized_filename}' uploaded successfully",
                "file_name": sanitized_filename,
                "file_size_bytes": len(content),
                "note": "Run reindexing to process this document"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_documents(
    engine: RAGEngine = Depends(get_rag_engine)
) -> ReindexResponse:
    """
    Trigger reindexing of all documents.

    This will:
    1. Scan the documents directory for all files
    2. Process and chunk all documents
    3. Rebuild the vector database
    4. Update BM25 index

    **Warning:** This can take several seconds to minutes depending on document count.
    The system will continue serving queries during reindexing, but results may be
    inconsistent until reindexing completes.

    **Returns:**
    - Success status
    - Processing statistics (files, chunks, time)
    """
    # CONCURRENCY FIX: Check if reindexing is already in progress
    if not _reindex_lock.acquire(blocking=False):
        logger.warning("[API] Reindexing already in progress, rejecting concurrent request")
        raise HTTPException(
            status_code=409,
            detail="Reindexing already in progress. Please wait for current operation to complete."
        )

    try:
        logger.info("[API] Starting document reindexing (with lock acquired)")
        start_time = time.time()

        # Load config
        config = load_config()

        # Initialize document processor
        processor = DocumentProcessor(config)

        # Process all documents
        logger.info(f"Processing documents from {config.documents_dir}")
        result = await processor.process_documents(config.documents_dir)

        if not result.documents:
            raise HTTPException(
                status_code=400,
                detail="No documents found to index"
            )

        # Build new vectorstore based on configuration
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.retrievers import BM25Retriever

        # Use HuggingFace embeddings (pre-cached in Docker image)
        embeddings = HuggingFaceEmbeddings(
            model_name=config.embedding.model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        try:
            # Branch based on vector store type
            if config.vector_store == "qdrant":
                # ============================================================
                # QDRANT REINDEXING PATH
                # ============================================================
                logger.info("Reindexing into Qdrant vector store...")
                from vector_store_qdrant import QdrantVectorStore

                # Create new Qdrant vectorstore
                vectorstore = QdrantVectorStore(
                    collection_name="documents",
                    vector_size=config.embedding.dimension,
                    host="qdrant",
                    port=6333,
                    use_async=True,
                    enable_sparse=True  # QUICK WIN #1: Enable BM25 hybrid search (+5% accuracy)
                )

                # Initialize connection (create collection if doesn't exist, reuse if exists)
                success = await vectorstore.initialize(recreate=False)
                if not success:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to initialize Qdrant vector store"
                    )
                logger.info("Connected to Qdrant")

                # Transform LangChain documents to Qdrant format with embeddings
                logger.info(f"Generating embeddings for {len(result.documents)} documents...")
                texts = [doc.page_content for doc in result.documents]

                # Generate embeddings in batches for efficiency
                all_embeddings = await asyncio.to_thread(
                    embeddings.embed_documents,
                    texts
                )

                # Format documents for Qdrant
                qdrant_docs = []
                for idx, (doc, embedding) in enumerate(zip(result.documents, all_embeddings)):
                    qdrant_docs.append({
                        "id": f"doc_{idx}",
                        "text": doc.page_content,
                        "vector": embedding,  # FIXED: Changed from "embedding" to "vector"
                        "metadata": doc.metadata
                    })

                logger.info(f"Indexing {len(qdrant_docs)} documents into Qdrant...")
                await vectorstore.index_documents(qdrant_docs)
                logger.info("Documents indexed into Qdrant")

            else:
                # ============================================================
                # CHROMADB REINDEXING PATH (Legacy/Fallback)
                # ============================================================
                # RACE CONDITION FIX: Use atomic swap pattern
                import shutil
                import tempfile

                temp_db_dir = Path(tempfile.mkdtemp(prefix="vectordb_temp_"))
                logger.info(f"Building new ChromaDB index in temporary directory: {temp_db_dir}")

                from langchain_chroma import Chroma

                vectorstore = await asyncio.to_thread(
                    Chroma.from_documents,
                    documents=result.documents,
                    embedding=embeddings,
                    persist_directory=str(temp_db_dir)
                )

                logger.info("ChromaDB built in temporary location")

                # Save chunk metadata
                import json
                metadata_file = temp_db_dir / "chunk_metadata.json"
                chunk_data = {
                    'texts': [doc.page_content for doc in result.documents],
                    'metadata': [doc.metadata for doc in result.documents]
                }
                with open(metadata_file, 'w') as f:
                    json.dump(chunk_data, f)

                # ATOMIC SWAP: Backup old directory and move new one into place
                backup_dir = config.vector_db_dir.parent / f"{config.vector_db_dir.name}_backup"

                # Remove old backup if exists
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)

                # Rename current to backup (if exists)
                if config.vector_db_dir.exists():
                    shutil.move(str(config.vector_db_dir), str(backup_dir))
                    logger.info(f"Backed up old index to {backup_dir}")

                # Move new index into place
                shutil.move(str(temp_db_dir), str(config.vector_db_dir))
                logger.info(f"Swapped new index into place: {config.vector_db_dir}")

                # Clean up backup after successful swap
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                    logger.info("Cleaned up backup directory")

            # Build BM25 index (shared for both paths)
            logger.info("Building BM25 index...")
            bm25_retriever = BM25Retriever.from_documents(result.documents)
            bm25_retriever.k = config.retrieval.initial_k
            logger.info("BM25 index built")

            # Update RAG engine components
            logger.info("Updating RAG engine components...")
            engine.vectorstore = vectorstore
            engine.bm25_retriever = bm25_retriever

            # Update retrieval engine
            if engine.retrieval_engine:
                engine.retrieval_engine.vectorstore = vectorstore
                engine.retrieval_engine.bm25_retriever = bm25_retriever

            # Clear cache to force fresh results
            if engine.cache_manager:
                if hasattr(engine.cache_manager, 'redis_client') and engine.cache_manager.redis_client:
                    engine.cache_manager.redis_client.flushdb()
                    logger.info("Cache cleared")

            processing_time = time.time() - start_time

            response = ReindexResponse(
                success=True,
                message="Reindexing completed successfully (atomic swap)",
                total_files=result.metadata.get('successful', 0),
                total_chunks=len(result.documents),
                processing_time_seconds=processing_time
            )

            logger.info(f"[API] Reindexing complete: {response.total_files} files, {response.total_chunks} chunks in {processing_time:.1f}s")

            return response

        except Exception as e:
            # Clean up temporary directory on error (only for ChromaDB path)
            if 'temp_db_dir' in locals() and temp_db_dir.exists():
                import shutil
                shutil.rmtree(temp_db_dir)
                logger.info("Cleaned up temporary directory after error")
            raise

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during reindexing: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Reindexing failed: {str(e)}"
        )
    finally:
        # ALWAYS release the lock
        _reindex_lock.release()
        logger.info("[API] Reindexing lock released")
