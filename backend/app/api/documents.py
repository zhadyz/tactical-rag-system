"""
Document management API endpoints
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse

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

        # Validate file extension
        supported_extensions = ['.pdf', '.txt', '.docx', '.doc', '.md']
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(supported_extensions)}"
            )

        # Save file to documents directory
        documents_dir = engine.config.documents_dir
        documents_dir.mkdir(exist_ok=True)

        file_path = documents_dir / file.filename

        # Read and save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"[API] File saved: {file_path} ({len(content)} bytes)")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"File '{file.filename}' uploaded successfully",
                "file_name": file.filename,
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
    try:
        logger.info("[API] Starting document reindexing")
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

        # Reinitialize vectorstore with new chunks
        logger.info("Rebuilding vector database...")

        # Delete existing vectorstore
        import shutil
        if config.vector_db_dir.exists():
            shutil.rmtree(config.vector_db_dir)
        config.vector_db_dir.mkdir(exist_ok=True, parents=True)

        # Create new vectorstore
        from langchain_chroma import Chroma
        from langchain_community.embeddings import OllamaEmbeddings
        from langchain_community.retrievers import BM25Retriever

        embeddings = OllamaEmbeddings(
            model=config.embedding.model_name,
            base_url=config.ollama_host
        )

        vectorstore = await asyncio.to_thread(
            Chroma.from_documents,
            documents=result.documents,
            embedding=embeddings,
            persist_directory=str(config.vector_db_dir)
        )

        logger.info("Vector database rebuilt")

        # Rebuild BM25 index
        logger.info("Rebuilding BM25 index...")
        bm25_retriever = BM25Retriever.from_documents(result.documents)

        # Save chunk metadata for BM25
        import json
        metadata_file = config.vector_db_dir / "chunk_metadata.json"
        chunk_data = {
            'texts': [doc.page_content for doc in result.documents],
            'metadata': [doc.metadata for doc in result.documents]
        }
        with open(metadata_file, 'w') as f:
            json.dump(chunk_data, f)

        logger.info("BM25 index rebuilt")

        # Update RAG engine components
        logger.info("Updating RAG engine...")
        engine.vectorstore = vectorstore
        engine.bm25_retriever = bm25_retriever
        engine.bm25_retriever.k = config.retrieval.initial_k

        # Update retrieval engine
        if engine.retrieval_engine:
            engine.retrieval_engine.vectorstore = vectorstore
            engine.retrieval_engine.bm25_retriever = bm25_retriever

        # Clear cache to force fresh results
        if engine.cache_manager:
            # Clear query cache
            if hasattr(engine.cache_manager, 'redis_client') and engine.cache_manager.redis_client:
                engine.cache_manager.redis_client.flushdb()
                logger.info("Cache cleared")

        processing_time = time.time() - start_time

        response = ReindexResponse(
            success=True,
            message="Reindexing completed successfully",
            total_files=result.metadata.get('successful', 0),
            total_chunks=len(result.documents),
            processing_time_seconds=processing_time
        )

        logger.info(f"[API] Reindexing complete: {response.total_files} files, {response.total_chunks} chunks in {processing_time:.1f}s")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during reindexing: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Reindexing failed: {str(e)}"
        )
