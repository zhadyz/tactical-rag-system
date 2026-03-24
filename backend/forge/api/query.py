"""
Forge - Query endpoints with security hardening.

CRITICAL: All security measures from the original ATLAS query.py are preserved:
  - In-memory rate limiting per client IP
  - Input sanitization (null bytes, control characters)
  - Prompt injection detection (19 regex patterns)
  - Max query length validation (10,000 chars)
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..schemas.query import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])


# ---------------------------------------------------------------------------
# Security: rate limiting (in-memory — use Redis in production)
# ---------------------------------------------------------------------------
_rate_limit_store: dict[str, list[datetime]] = defaultdict(list)
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW = 60  # seconds


def _check_rate_limit(client_ip: str) -> tuple[bool, str | None]:
    now = datetime.now()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)

    _rate_limit_store[client_ip] = [
        ts for ts in _rate_limit_store[client_ip] if ts > window_start
    ]

    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False, (
            f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} "
            f"requests per {RATE_LIMIT_WINDOW} seconds."
        )

    _rate_limit_store[client_ip].append(now)
    return True, None


# ---------------------------------------------------------------------------
# Security: prompt injection detection
# ---------------------------------------------------------------------------
_PROMPT_INJECTION_PATTERNS: list[str] = [
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
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"assistant:\s*",
    r"###\s*(system|assistant|user)",
    r"\[INST\]",
    r"\[/INST\]",
    r"<<SYS>>",
    r"<</SYS>>",
]


def _detect_prompt_injection(query: str) -> tuple[bool, str | None]:
    query_lower = query.lower()
    for pattern in _PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            return True, pattern
    return False, None


# ---------------------------------------------------------------------------
# Security: input sanitization
# ---------------------------------------------------------------------------
def _sanitize_input(query: str) -> str:
    query = query.replace("\x00", "")
    query = "".join(ch for ch in query if ch.isprintable() or ch in "\n\r\t")
    return query.strip()


# ---------------------------------------------------------------------------
# Shared security checks
# ---------------------------------------------------------------------------
def _apply_security_checks(raw_question: str, client_ip: str) -> str:
    """Run rate-limit, sanitize, validate, and injection-detection.

    Returns the sanitized question or raises HTTPException.
    """
    # Rate limit
    allowed, err = _check_rate_limit(client_ip)
    if not allowed:
        logger.warning("[SECURITY] Rate limit exceeded for %s", client_ip)
        raise HTTPException(status_code=429, detail=err)

    # Sanitize
    question = _sanitize_input(raw_question)

    # Validate length
    if not question:
        raise HTTPException(status_code=400, detail="Query cannot be empty or whitespace-only")
    if len(question) > 10_000:
        raise HTTPException(status_code=400, detail="Query too long (maximum 10,000 characters)")

    # Injection detection (log only — do not reject)
    is_suspicious, matched = _detect_prompt_injection(question)
    if is_suspicious:
        logger.warning(
            "[SECURITY] Potential prompt injection from %s: pattern='%s', query='%s…'",
            client_ip, matched, question[:100],
        )

    return question


# ---------------------------------------------------------------------------
# Helper to get container
# ---------------------------------------------------------------------------
def _get_container(request: Request):
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(status_code=503, detail="Forge backend is still initializing.")
    return container


# ---------------------------------------------------------------------------
# POST /api/query — non-streaming
# ---------------------------------------------------------------------------
@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: Request, body: QueryRequest) -> QueryResponse:
    """Non-streaming query endpoint."""
    client_ip = request.client.host if request.client else "unknown"
    question = _apply_security_checks(body.question, client_ip)

    container = _get_container(request)
    logger.info("[QUERY] question='%s…' mode=%s", question[:50], body.mode)

    try:
        agent = await container.get_agent()
        result = await agent.query(
            question=question,
            mode=body.mode,
            use_context=body.use_context,
        )
        return QueryResponse(**result)

    except Exception as e:
        logger.error("Query endpoint error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query processing failed: {e}")


# ---------------------------------------------------------------------------
# POST /api/query/stream — SSE streaming
# ---------------------------------------------------------------------------
@router.post("/query/stream")
async def query_stream(request: Request, body: QueryRequest):
    """Streaming query endpoint with agentic events (SSE)."""
    client_ip = request.client.host if request.client else "unknown"
    question = _apply_security_checks(body.question, client_ip)

    container = _get_container(request)
    logger.info("[STREAM] question='%s…' mode=%s", question[:50], body.mode)

    async def generate():
        try:
            agent = await container.get_agent()
            async for event in agent.query_stream(
                question=question,
                mode=body.mode,
                use_context=body.use_context,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error("Streaming error: %s", e, exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# POST /api/conversation/clear
# ---------------------------------------------------------------------------
@router.post("/conversation/clear")
async def clear_conversation(request: Request):
    """Clear conversation memory."""
    container = _get_container(request)

    try:
        memory = await container.get_memory()
        memory.clear()
        return {"success": True, "message": "Conversation memory cleared."}
    except Exception as e:
        logger.error("Clear conversation error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation: {e}")
