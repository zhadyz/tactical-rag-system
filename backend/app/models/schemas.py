"""
Pydantic schemas for API request/response models
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    # SECURITY FIX: Accept both 'question' and 'query' field names for compatibility
    # Uses Field alias to support both naming conventions
    question: str = Field(..., min_length=1, max_length=10000, alias="query", description="User's question")
    mode: Literal["simple", "adaptive"] = Field(
        default="simple",
        description="Retrieval mode: 'simple' for fast direct search, 'adaptive' for intelligent routing"
    )
    use_context: bool = Field(
        default=False,  # PERFORMANCE FIX: Context enhancement causes 4-6x slowdown
        description="Whether to use conversation context for follow-up questions"
    )

    class Config:
        # Allow population by both field name and alias
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "question": "Can I grow a beard?",
                "query": "Can I grow a beard?",  # Also show alias example
                "mode": "simple",
                "use_context": True
            }
        }


class Source(BaseModel):
    """Source document information"""
    file_name: str = Field(..., description="Name of the source file")
    file_type: str = Field(..., description="Type of file (pdf, txt, docx, etc)")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")
    excerpt: str = Field(..., description="Relevant excerpt from the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "AFI36-2903.pdf",
                "file_type": "pdf",
                "relevance_score": 0.95,
                "excerpt": "Male Airmen are authorized to wear beards...",
                "metadata": {
                    "page_number": 12,
                    "chunk_index": 5
                }
            }
        }


class QueryExplanation(BaseModel):
    """Explanation of query classification and strategy selection"""
    query_type: str = Field(..., description="Classified query type (simple/moderate/complex)")
    complexity_score: int = Field(..., description="Complexity score used for classification")
    scoring_breakdown: Dict[str, str] = Field(..., description="Detailed scoring breakdown")
    strategy_reasoning: Optional[str] = Field(None, description="Reasoning for strategy selection")
    example_text: Optional[str] = Field(None, description="Example explanation text")

    class Config:
        json_schema_extra = {
            "example": {
                "query_type": "simple",
                "complexity_score": 0,
                "scoring_breakdown": {
                    "length": "5 words (+0)",
                    "question_type": "can i (+0)"
                },
                "strategy_reasoning": "Simple lookup query requires direct search",
                "example_text": "This is a straightforward factual question"
            }
        }


class QueryMetadata(BaseModel):
    """Metadata about query processing"""
    strategy_used: str = Field(..., description="Retrieval strategy used")
    query_type: str = Field(..., description="Query type classification")
    mode: str = Field(..., description="Mode used (simple/adaptive)")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    timing_breakdown: Optional[Dict[str, Any]] = Field(None, description="Detailed timing breakdown by stage")
    cache_hit: Optional[bool] = Field(None, description="Whether result was served from cache")
    optimization: Optional[str] = Field(None, description="Optimization strategy applied")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall confidence score (0-1)")
    confidence_interpretation: Optional[str] = Field(None, description="Human-readable confidence level (Low/Medium/High)")
    confidence_signals: Optional[Dict[str, float]] = Field(None, description="Individual confidence signal scores")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_used": "simple_dense",
                "query_type": "simple",
                "mode": "simple",
                "processing_time_ms": 1250.5,
                "timing_breakdown": {
                    "total_ms": 1250.5,
                    "stages": {
                        "cache_lookup": {"time_ms": 0.5, "percentage": 0.0},
                        "retrieval": {"time_ms": 850.0, "percentage": 68.0},
                        "answer_generation": {"time_ms": 400.0, "percentage": 32.0}
                    }
                },
                "cache_hit": False,
                "optimization": "speed_optimized",
                "confidence": 0.82,
                "confidence_interpretation": "High",
                "confidence_signals": {
                    "retrieval_score": 0.85,
                    "answer_length": 0.78,
                    "semantic_coherence": 0.83
                }
            }
        }


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    answer: str = Field(..., description="Generated answer to the query")
    sources: List[Source] = Field(default_factory=list, description="Source documents used")
    metadata: QueryMetadata = Field(..., description="Query processing metadata")
    explanation: Optional[QueryExplanation] = Field(
        None,
        description="Explanation of query classification (only in adaptive mode)"
    )
    error: bool = Field(default=False, description="Whether an error occurred")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Yes, according to AFI 36-2903, male Airmen are authorized to wear beards under specific medical or religious accommodation conditions.",
                "sources": [
                    {
                        "file_name": "AFI36-2903.pdf",
                        "file_type": "pdf",
                        "relevance_score": 0.95,
                        "excerpt": "Male Airmen are authorized to wear beards...",
                        "metadata": {"page_number": 12}
                    }
                ],
                "metadata": {
                    "strategy_used": "simple_dense",
                    "query_type": "simple",
                    "mode": "simple",
                    "processing_time_ms": 1250.5
                },
                "explanation": None,
                "error": False
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="System status")
    message: str = Field(..., description="Status message")
    components: Dict[str, str] = Field(default_factory=dict, description="Component health status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "All systems operational",
                "components": {
                    "vectorstore": "ready",
                    "llm": "connected",
                    "redis": "connected",
                    "conversation_memory": "ready"
                }
            }
        }


class ConversationClearResponse(BaseModel):
    """Response for conversation clear endpoint"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Conversation memory cleared successfully"
            }
        }


class SettingsUpdate(BaseModel):
    """Request model for updating runtime settings"""
    simple_k: Optional[int] = Field(None, ge=1, le=50, description="K for simple retrieval")
    hybrid_k: Optional[int] = Field(None, ge=5, le=40, description="K for hybrid retrieval")
    advanced_k: Optional[int] = Field(None, ge=5, le=30, description="K for advanced retrieval")
    rerank_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Reranker weight")
    rrf_constant: Optional[int] = Field(None, ge=1, le=100, description="RRF constant")
    simple_threshold: Optional[int] = Field(None, ge=0, le=10, description="Simple classification threshold")
    moderate_threshold: Optional[int] = Field(None, ge=0, le=10, description="Moderate classification threshold")
    llm_model: Optional[str] = Field(None, description="LLM model name (Ollama model ID)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="LLM temperature")

    class Config:
        json_schema_extra = {
            "example": {
                "simple_k": 5,
                "hybrid_k": 20,
                "rerank_weight": 0.7,
                "llm_model": "qwen2.5:14b-instruct-q4_K_M",
                "temperature": 0.0
            }
        }


class SettingsResponse(BaseModel):
    """Response model for settings endpoints"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Result message")
    current_settings: Dict[str, Any] = Field(..., description="Current runtime settings")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Settings updated successfully",
                "current_settings": {
                    "simple_k": 5,
                    "hybrid_k": 20,
                    "advanced_k": 15,
                    "rerank_weight": 0.7,
                    "rrf_constant": 60,
                    "simple_threshold": 1,
                    "moderate_threshold": 3
                }
            }
        }


class DocumentInfo(BaseModel):
    """Information about an indexed document"""
    file_name: str = Field(..., description="Name of the file")
    file_type: str = Field(..., description="File extension (pdf, txt, docx, etc)")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="SHA256 hash of the file")
    num_chunks: int = Field(..., description="Number of chunks created from this document")
    processing_date: str = Field(..., description="When the document was last processed")

    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "AFI36-2903.pdf",
                "file_type": ".pdf",
                "file_size_bytes": 1024000,
                "file_hash": "abc123...",
                "num_chunks": 45,
                "processing_date": "2025-10-12T10:30:00"
            }
        }


class DocumentListResponse(BaseModel):
    """Response model for document list endpoint"""
    total_documents: int = Field(..., description="Total number of indexed documents")
    total_chunks: int = Field(..., description="Total number of chunks across all documents")
    documents: List[DocumentInfo] = Field(..., description="List of document information")

    class Config:
        json_schema_extra = {
            "example": {
                "total_documents": 5,
                "total_chunks": 234,
                "documents": [
                    {
                        "file_name": "AFI36-2903.pdf",
                        "file_type": ".pdf",
                        "file_size_bytes": 1024000,
                        "file_hash": "abc123...",
                        "num_chunks": 45,
                        "processing_date": "2025-10-12T10:30:00"
                    }
                ]
            }
        }


class ReindexResponse(BaseModel):
    """Response model for reindexing endpoint"""
    success: bool = Field(..., description="Whether reindexing succeeded")
    message: str = Field(..., description="Result message")
    total_files: int = Field(..., description="Total files processed")
    total_chunks: int = Field(..., description="Total chunks created")
    processing_time_seconds: float = Field(..., description="Time taken to reindex")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Reindexing completed successfully",
                "total_files": 5,
                "total_chunks": 234,
                "processing_time_seconds": 12.5
            }
        }
