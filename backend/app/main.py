"""
FastAPI Backend for Tactical RAG System
Main application entry point
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .core.rag_engine import RAGEngine
from .api.query import router as query_router, set_rag_engine as set_query_engine
from .api.settings import router as settings_router
from .api.documents import router as documents_router, set_rag_engine as set_documents_engine
from .api.models import router as models_router
from .models.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SECURITY: Initialize rate limiter
# Limit: 5 requests per minute per IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Global RAG engine instance
rag_engine: RAGEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI startup and shutdown.
    Initializes RAG engine on startup and cleans up on shutdown.
    """
    global rag_engine

    # Startup
    logger.info("=" * 70)
    logger.info("STARTING TACTICAL RAG FASTAPI BACKEND")
    logger.info("=" * 70)

    try:
        # Initialize RAG engine
        logger.info("Initializing RAG Engine...")
        rag_engine = RAGEngine()

        success, message = await rag_engine.initialize()

        if not success:
            logger.error(f"RAG Engine initialization failed: {message}")
            raise RuntimeError(f"Failed to initialize RAG Engine: {message}")

        # Set engine in routers
        set_query_engine(rag_engine)
        set_documents_engine(rag_engine)

        logger.info("=" * 70)
        logger.info("BACKEND READY - Listening on port 8000")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Available endpoints:")
        logger.info("  - GET  /api/health          - Health check")
        logger.info("  - POST /api/query           - Process query")
        logger.info("  - POST /api/conversation/clear - Clear conversation")
        logger.info("  - GET  /api/settings        - Get settings")
        logger.info("  - PUT  /api/settings        - Update settings")
        logger.info("  - POST /api/settings/reset  - Reset settings")
        logger.info("  - GET  /api/documents       - List all indexed documents")
        logger.info("  - POST /api/documents/upload - Upload new document")
        logger.info("  - POST /api/documents/reindex - Reindex all documents")
        logger.info("  - GET  /api/models          - List available LLM models")
        logger.info("  - POST /api/models/select   - Select LLM model")
        logger.info("  - GET  /docs                - API documentation (Swagger)")
        logger.info("  - GET  /redoc               - API documentation (ReDoc)")
        logger.info("")

        yield

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

    # Shutdown
    logger.info("Shutting down RAG Engine...")
    # Add any cleanup logic here if needed


# Create FastAPI app
app = FastAPI(
    title="Tactical RAG API",
    description="""
    FastAPI backend for Tactical RAG Document Intelligence System.

    This API provides access to an advanced Retrieval-Augmented Generation (RAG) system
    with adaptive query routing, conversation memory, and multi-stage caching.

    ## Features

    - **Dual Retrieval Modes**: Simple (fast, direct) and Adaptive (intelligent routing)
    - **Conversation Memory**: Multi-turn conversations with automatic context tracking
    - **Advanced Caching**: Multi-stage cache with exact, normalized, and semantic matching
    - **Configurable Settings**: Runtime configuration of retrieval parameters
    - **Source Attribution**: All answers include source documents with relevance scores
    - **Security Hardening**: Prompt injection detection, input sanitization, rate limiting

    ## Query Modes

    ### Simple Mode (Default)
    - Direct dense vector search
    - Fast and consistent performance (~8-15 seconds)
    - Best for most queries
    - No query classification overhead

    ### Adaptive Mode
    - Automatic query classification (simple/moderate/complex)
    - Strategy routing (simple/hybrid/advanced retrieval)
    - Query expansion for complex questions
    - Best for varied query complexity
    - Variable response time based on complexity

    ## Security Features

    - **Rate Limiting**: 100 requests/minute per IP (general), 5 requests/minute for query endpoint
    - **Input Sanitization**: Removes null bytes, control characters
    - **Prompt Injection Detection**: Logs suspicious patterns
    - **Input Validation**: Maximum 10,000 characters, no empty queries

    ## Authentication

    Currently no authentication required. Add your own auth middleware as needed for production.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# SECURITY: Attach rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
# SECURITY: Restrict origins in production
# TODO: Set environment variable CORS_ORIGINS in production to specific domains
import os
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Restrict to specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods only
    allow_headers=["Content-Type", "Authorization"],  # Specific headers only
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


# Health check endpoint
@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the current status of the RAG system and its components.

    **Returns:**
    - `status`: Overall system status (healthy/unhealthy/initializing)
    - `message`: Status message
    - `components`: Health status of individual components

    **Component Status:**
    - `vectorstore`: Vector database (ChromaDB)
    - `llm`: Language model (Ollama)
    - `bm25_retriever`: BM25 sparse retriever
    - `cache`: Redis caching system
    - `conversation_memory`: Conversation memory system

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "message": "All systems operational",
        "components": {
            "vectorstore": "ready",
            "llm": "ready",
            "bm25_retriever": "ready",
            "cache": "ready",
            "conversation_memory": "ready"
        }
    }
    ```
    """
    global rag_engine

    if rag_engine is None:
        return HealthResponse(
            status="initializing",
            message="RAG Engine is starting up",
            components={}
        )

    if not rag_engine.initialized:
        return HealthResponse(
            status="unhealthy",
            message="RAG Engine initialization failed or incomplete",
            components={}
        )

    # Get detailed status from engine
    status_dict = rag_engine.get_status()

    # Determine overall health
    all_ready = all(
        status == "ready"
        for status in status_dict["components"].values()
    )

    return HealthResponse(
        status="healthy" if all_ready else "degraded",
        message=status_dict["message"],
        components=status_dict["components"]
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> Dict:
    """
    Root endpoint - API information.

    Returns basic information about the API.
    """
    return {
        "name": "Tactical RAG API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "health": "/api/health",
            "query": "/api/query",
            "conversation_clear": "/api/conversation/clear",
            "settings": "/api/settings"
        }
    }


# Include routers
app.include_router(query_router)
app.include_router(settings_router)
app.include_router(documents_router)
app.include_router(models_router)


# For development/testing
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting development server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
