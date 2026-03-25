"""
Forge - Query request / response / streaming schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str
    mode: Literal["direct", "agentic"] = "direct"
    use_context: bool = True
    rerank_preset: Literal["quick", "quality", "deep"] = "quality"


# ---------------------------------------------------------------------------
# Sub-models used in the response
# ---------------------------------------------------------------------------

class Source(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}
    relevance_score: float = 0.0


class CRAGEvaluation(BaseModel):
    doc_id: str
    score: float
    verdict: Literal["correct", "ambiguous", "incorrect"]
    reason: Optional[str] = None


class VerificationResult(BaseModel):
    claim: str
    supported: bool
    confidence: float = 0.0
    supporting_sources: List[str] = []
    explanation: Optional[str] = None


class AgentStep(BaseModel):
    id: str
    type: Literal[
        "thinking", "tool_call", "tool_result",
        "observation", "decision",
    ]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: Any = None
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    status: Literal["pending", "running", "completed", "failed"] = "completed"


class RetrievalStage(BaseModel):
    stage_name: str
    results_count: int = 0
    top_score: float = 0.0
    duration_ms: float = 0.0
    sources: List[Source] = []


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source] = []
    metadata: Dict[str, Any] = {}
    agent_steps: List[AgentStep] = []
    verification_results: List[VerificationResult] = []


# ---------------------------------------------------------------------------
# SSE stream events
# ---------------------------------------------------------------------------

class StreamEvent(BaseModel):
    type: Literal[
        "token",
        "sources",
        "metadata",
        "done",
        "error",
        "agent_thinking",
        "tool_call",
        "tool_result",
        "crag_evaluation",
        "retrieval_complete",
        "verification",
    ]
    content: Any = None
