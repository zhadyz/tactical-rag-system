"""
Query API endpoints with security hardening
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict
from collections import defaultdict
from datetime import datetime, timedelta
import logging
import json
import asyncio
import re

from ..models.schemas import QueryRequest, QueryResponse, ConversationClearResponse
from ..core.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])

# SECURITY: Rate limiting (simple in-memory implementation)
# In production, use Redis or a proper rate limiting library
_rate_limit_store = defaultdict(list)
RATE_LIMIT_REQUESTS = 30  # Max requests
RATE_LIMIT_WINDOW = 60  # Per 60 seconds

def check_rate_limit(client_ip: str) -> tuple[bool, str | None]:
    """
    Check if client has exceeded rate limit

    Returns:
        (is_allowed, error_message)
    """
    now = datetime.now()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)

    # Clean old requests
    _rate_limit_store[client_ip] = [
        ts for ts in _rate_limit_store[client_ip]
        if ts > window_start
    ]

    # Check limit
    request_count = len(_rate_limit_store[client_ip])
    if request_count >= RATE_LIMIT_REQUESTS:
        return False, f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."

    # Record this request
    _rate_limit_store[client_ip].append(now)
    return True, None

# SECURITY: Prompt injection detection patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"ignore\s+(all\s+)?instructions?",
    r"disregard\s+(all\s+)?previous\s+instructions?",
    r"forget\s+(all\s+)?previous\s+instructions?",
    r"system\s+prompt",
    r"reveal\s+(your\s+)?instructions?",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"what\s+(is|are)\s+your\s+instructions?",
    r"you\s+are\s+now",
    r"developer\s+mode",
    r"admin\s+mode",
    r"debug\s+mode",
    r"<\|im_start\|>",  # Role markers (ChatML format)
    r"<\|im_end\|>",
    r"assistant:\s*",  # Role injection
    r"###\s*(system|assistant|user)",  # Role markers
    r"\[INST\]",  # Instruction markers (Llama format)
    r"\[/INST\]",
    r"<<SYS>>",  # System markers
    r"<</SYS>>",
]

def detect_prompt_injection(query: str) -> tuple[bool, str | None]:
    """
    Detect potential prompt injection attempts

    Returns:
        (is_suspicious, matched_pattern)
    """
    query_lower = query.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return True, pattern

    return False, None

def sanitize_input(query: str) -> str:
    """
    Sanitize user input

    - Remove null bytes
    - Strip leading/trailing whitespace
    - Remove control characters (except newlines/tabs)
    """
    # Remove null bytes
    query = query.replace('\x00', '')

    # Remove other control characters except \n \r \t
    query = ''.join(char for char in query if char.isprintable() or char in '\n\r\t')

    # Strip whitespace
    query = query.strip()

    return query

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


@router.post("/query", response_model=QueryResponse)
async def query(
    req: Request,
    request: QueryRequest,
    engine: RAGEngine = Depends(get_rag_engine)
) -> QueryResponse:
    """
    Process a query using the RAG system.

    **Modes:**
    - `simple`: Fast direct vector search (8-15 seconds)
    - `adaptive`: Intelligent query classification and routing (variable time)

    **Context:**
    - `use_context=True`: Uses conversation history for follow-up questions
    - `use_context=False`: Treats each query independently

    **Returns:**
    - `answer`: Generated response
    - `sources`: Relevant source documents with relevance scores
    - `metadata`: Processing information (strategy, query type, timing)
    - `explanation`: Detailed explanation (only in adaptive mode)

    **Example:**
    ```json
    {
        "question": "Can I grow a beard?",
        "mode": "simple",
        "use_context": true
    }
    ```
    """
    try:
        # SECURITY: Rate limiting
        client_ip = req.client.host if req.client else "unknown"
        is_allowed, error_msg = check_rate_limit(client_ip)
        if not is_allowed:
            logger.warning(f"[SECURITY] Rate limit exceeded for {client_ip}")
            raise HTTPException(status_code=429, detail=error_msg)

        # SECURITY: Sanitize input
        sanitized_query = sanitize_input(request.question)

        # SECURITY: Validate input length (already validated by Pydantic, but double-check)
        if not sanitized_query or len(sanitized_query) == 0:
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty or whitespace-only"
            )

        if len(sanitized_query) > 10000:
            raise HTTPException(
                status_code=400,
                detail="Query too long (maximum 10,000 characters)"
            )

        # SECURITY: Detect prompt injection attempts
        is_suspicious, matched_pattern = detect_prompt_injection(sanitized_query)
        if is_suspicious:
            client_ip = req.client.host if req else "unknown"
            logger.warning(
                f"[SECURITY] Potential prompt injection detected from {client_ip}: "
                f"pattern='{matched_pattern}', query='{sanitized_query[:100]}...'"
            )
            # Log but don't reject - allow system to process normally
            # In production, you may want to reject: raise HTTPException(status_code=400, ...)

        # ENHANCEMENT: Detailed query logging for accuracy tracking
        logger.info(f"[QUERY TRACKING] query='{sanitized_query}', mode={request.mode}, use_context={request.use_context}, client_ip={client_ip}")
        logger.info(f"[API] Query received: {sanitized_query[:50]}... (mode={request.mode})")

        # DEBUG: About to call engine.query()
        logger.info(f"[DEBUG] About to call engine.query() with question='{sanitized_query[:50]}...'")

        # Process query through RAG engine with sanitized input
        result = await engine.query(
            question=sanitized_query,
            mode=request.mode,
            use_context=request.use_context
        )

        # DEBUG: engine.query() returned successfully
        logger.info(f"[DEBUG] engine.query() completed, result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")

        # Convert dict result to Pydantic model
        return QueryResponse(**result)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Query endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


@router.post("/query/stream")
async def query_stream(
    req: Request,
    request: QueryRequest,
    engine: RAGEngine = Depends(get_rag_engine)
):
    """
    Process a query with streaming response (Server-Sent Events).

    Returns answer tokens as they are generated, providing real-time feedback.
    Uses the same RAG engine but streams the LLM generation.

    **Response Format:** Server-Sent Events (text/event-stream)

    Each event contains JSON:
    - `{"type": "token", "content": "..."}` - Generated text token
    - `{"type": "sources", "content": [...]}` - Retrieved sources
    - `{"type": "metadata", "content": {...}}` - Processing metadata
    - `{"type": "done"}` - Generation complete

    **Example:**
    ```json
    {
        "question": "Can I grow a beard?",
        "mode": "simple",
        "use_context": false
    }
    ```
    """
    # SECURITY: Rate limiting (check before starting stream)
    client_ip = req.client.host if req.client else "unknown"
    is_allowed, error_msg = check_rate_limit(client_ip)
    if not is_allowed:
        logger.warning(f"[SECURITY] Rate limit exceeded for {client_ip} (streaming)")
        raise HTTPException(status_code=429, detail=error_msg)

    # SECURITY: Sanitize and validate input
    sanitized_query = sanitize_input(request.question)

    if not sanitized_query or len(sanitized_query) == 0:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty or whitespace-only"
        )

    if len(sanitized_query) > 10000:
        raise HTTPException(
            status_code=400,
            detail="Query too long (maximum 10,000 characters)"
        )

    # SECURITY: Detect prompt injection
    is_suspicious, matched_pattern = detect_prompt_injection(sanitized_query)
    if is_suspicious:
        logger.warning(
            f"[SECURITY] Potential prompt injection in streaming query from {client_ip}: "
            f"pattern='{matched_pattern}', query='{sanitized_query[:100]}...'"
        )

    async def generate():
        try:
            logger.info(f"[API STREAM] Query received: {sanitized_query[:50]}... (mode={request.mode})")

            # Stream the response (use sanitized query)
            async for chunk in engine.query_stream(
                question=sanitized_query,
                mode=request.mode,
                use_context=request.use_context
            ):
                # Send as Server-Sent Event
                yield f"data: {json.dumps(chunk)}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_event = {
                "type": "error",
                "content": str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/conversation/clear", response_model=ConversationClearResponse)
async def clear_conversation(
    engine: RAGEngine = Depends(get_rag_engine)
) -> ConversationClearResponse:
    """
    Clear conversation memory.

    This resets the conversation history, removing all context.
    Useful when starting a new topic or conversation.

    **Returns:**
    - `success`: Whether the operation succeeded
    - `message`: Result message
    """
    try:
        success, message = engine.clear_conversation()

        return ConversationClearResponse(
            success=success,
            message=message
        )

    except Exception as e:
        logger.error(f"Clear conversation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear conversation: {str(e)}"
        )
