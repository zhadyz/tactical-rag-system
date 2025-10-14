"""
Enterprise RAG System - Configuration Management
Centralized configuration with validation and environment support
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Literal
import os
from pathlib import Path


class EmbeddingConfig(BaseModel):
    """Embedding model configuration"""
    # UPGRADED: Using BAAI/bge-large-en-v1.5 for state-of-the-art retrieval quality
    # This is one of the best open-source embedding models for semantic search
    model_name: str = Field(default="BAAI/bge-large-en-v1.5", description="HuggingFace embedding model")
    model_type: str = Field(default="huggingface", description="Model type: 'huggingface' or 'ollama'")
    dimension: int = Field(default=1024, description="Embedding dimension (1024 for bge-large)")
    batch_size: int = Field(default=32, description="Batch size for embedding generation")
    cache_embeddings: bool = Field(default=True, description="Cache embeddings in memory")
    normalize_embeddings: bool = Field(default=True, description="Normalize embeddings for cosine similarity")


class LLMConfig(BaseModel):
    """LLM configuration (Ollama)"""
    model_name: str = Field(default="llama3.1:8b", description="Ollama LLM model")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Generation temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: int = Field(default=40, ge=0, description="Top-k sampling parameter")
    num_ctx: int = Field(default=8192, description="Context window size")
    repeat_penalty: float = Field(default=1.1, description="Repetition penalty")
    timeout: int = Field(default=120, description="Request timeout in seconds")


class VLLMConfig(BaseModel):
    """vLLM configuration (10-20x faster than Ollama)"""
    host: str = Field(default="http://vllm-server:8000", description="vLLM server endpoint")
    model_name: str = Field(default="meta-llama/Meta-Llama-3.1-8B-Instruct", description="HuggingFace model ID")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Generation temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: int = Field(default=40, ge=0, description="Top-k sampling parameter")
    max_tokens: int = Field(default=512, ge=1, le=2048, description="Maximum tokens to generate")
    timeout: int = Field(default=180, description="Request timeout in seconds (180s for first inference)")
    retry_attempts: int = Field(default=3, description="Number of retry attempts on failure")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")


class ChunkingConfig(BaseModel):
    """Document chunking configuration"""
    strategy: Literal["recursive", "semantic", "sentence", "hybrid"] = "hybrid"
    chunk_size: int = Field(default=800, ge=100, le=2000)
    chunk_overlap: int = Field(default=200, ge=0, le=500)
    min_chunk_size: int = Field(default=100, ge=50)
    semantic_similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    
    @validator("chunk_overlap")
    def validate_overlap(cls, v, values):
        if "chunk_size" in values and v >= values["chunk_size"]:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v


class RetrievalConfig(BaseModel):
    """Advanced retrieval configuration"""
    # Multi-stage retrieval
    initial_k: int = Field(default=50, description="Initial candidates to retrieve")
    rerank_k: int = Field(default=20, description="Candidates after first reranking")
    final_k: int = Field(default=5, description="Final results to return")
    
    # Hybrid search weights
    dense_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    sparse_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Fusion method
    fusion_method: Literal["rrf", "weighted", "score_normalization"] = "rrf"
    rrf_k: int = Field(default=60, description="RRF constant")
    
    # Query enhancement
    use_query_expansion: bool = True
    use_query_decomposition: bool = True
    use_hypothetical_document: bool = True
    
    # Reranking
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"
    use_colbert_rerank: bool = False
    
    # Filtering
    use_metadata_filtering: bool = True
    relevance_threshold: float = Field(default=0.3, ge=0.0, le=1.0)


class ScopeDetectionConfig(BaseModel):
    """Semantic scope detection configuration"""
    enable_semantic_scope: bool = Field(default=True, description="Enable semantic boundary detection")
    strict_threshold: float = Field(default=1.5, ge=0.5, le=3.0, description="Strict threshold (x avg_distance)")
    relaxed_threshold: float = Field(default=2.0, ge=1.0, le=5.0, description="Relaxed threshold (x avg_distance)")
    metadata_path: str = Field(default="data/collection_metadata.json", description="Path to metadata file")
    auto_compute: bool = Field(default=True, description="Auto-compute metadata if missing")
    force_recompute: bool = Field(default=False, description="Force recomputation on startup")


class QdrantConfig(BaseModel):
    """Qdrant vector database configuration"""
    host: str = Field(default="localhost", description="Qdrant server host")
    port: int = Field(default=6333, description="Qdrant server port")
    collection_name: str = Field(default="air_force_docs", description="Collection name")
    grpc_port: int = Field(default=6334, description="Qdrant gRPC port")
    api_key: Optional[str] = Field(default=None, description="API key for Qdrant Cloud")
    timeout: int = Field(default=30, description="Request timeout in seconds")

    # Performance settings
    prefer_grpc: bool = Field(default=False, description="Use gRPC for better performance")
    batch_size: int = Field(default=100, description="Batch size for indexing")

    # HNSW index parameters
    hnsw_m: int = Field(default=16, description="HNSW connections per layer")
    hnsw_ef_construct: int = Field(default=200, description="HNSW construction quality")

    # Quantization for memory optimization
    enable_quantization: bool = Field(default=True, description="Enable scalar quantization (4x memory reduction)")


class CacheConfig(BaseModel):
    """Caching configuration"""
    enable_embedding_cache: bool = True
    enable_query_cache: bool = True
    enable_result_cache: bool = True

    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    max_cache_size: int = Field(default=10000, description="Maximum cache entries")

    # Redis config (optional distributed cache)
    use_redis: bool = True
    redis_host: str = "redis"  # Docker service name
    redis_port: int = 6379
    redis_db: int = 0


class MonitoringConfig(BaseModel):
    """Observability and monitoring"""
    enable_logging: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_file: Optional[str] = "logs/rag_system.log"
    
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    enable_tracing: bool = False
    trace_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)


class PerformanceConfig(BaseModel):
    """Performance optimization settings"""
    max_workers: int = Field(default=4, description="Thread pool size")
    enable_async: bool = True
    connection_pool_size: int = Field(default=10, description="HTTP connection pool")
    
    # Batching
    enable_batching: bool = True
    batch_timeout_ms: int = Field(default=100, description="Batch accumulation timeout")
    max_batch_size: int = Field(default=32, description="Maximum batch size")


class SystemConfig(BaseModel):
    """Root system configuration"""
    # Paths
    documents_dir: Path = Field(default=Path("./documents"))
    vector_db_dir: Path = Field(default=Path("./chroma_db"))
    cache_dir: Path = Field(default=Path("./.cache"))

    # Service endpoints
    ollama_host: str = Field(default="http://localhost:11434")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=7860)

    # Component configs
    embedding: EmbeddingConfig = EmbeddingConfig()
    llm: LLMConfig = LLMConfig()
    vllm: VLLMConfig = VLLMConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    scope_detection: ScopeDetectionConfig = ScopeDetectionConfig()
    cache: CacheConfig = CacheConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    performance: PerformanceConfig = PerformanceConfig()
    qdrant: QdrantConfig = QdrantConfig()

    # Feature flags
    enable_evaluation: bool = True
    enable_feedback_loop: bool = True
    enable_auto_optimization: bool = False

    # Vector store selection (CRITICAL FEATURE FLAG)
    use_qdrant: bool = Field(
        default=False,
        description="Use Qdrant instead of ChromaDB (False = ChromaDB, True = Qdrant)"
    )

    # LLM backend selection (CRITICAL FEATURE FLAG)
    use_vllm: bool = Field(
        default=False,
        description="Use vLLM instead of Ollama (False = Ollama 16s, True = vLLM 1-2s)"
    )
    
    class Config:
        env_prefix = "RAG_"
        case_sensitive = False


def load_config(config_file: Optional[str] = None) -> SystemConfig:
    """Load configuration from file or environment"""

    if config_file and os.path.exists(config_file):
        import yaml
        with open(config_file, 'r') as f:
            config_dict = yaml.safe_load(f)
        return SystemConfig(**config_dict)

    # Load from environment with fallback to defaults
    return SystemConfig(
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        documents_dir=Path(os.getenv("DOCUMENTS_DIR", "./documents")),
        vector_db_dir=Path(os.getenv("VECTOR_DB_DIR", "./chroma_db")),
        use_qdrant=os.getenv("USE_QDRANT", "false").lower() in ("true", "1", "yes"),
        use_vllm=os.getenv("USE_VLLM", "false").lower() in ("true", "1", "yes"),
        qdrant=QdrantConfig(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            collection_name=os.getenv("QDRANT_COLLECTION", "air_force_docs"),
        ),
        vllm=VLLMConfig(
            host=os.getenv("VLLM_HOST", "http://vllm-server:8000"),
            model_name=os.getenv("VLLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct"),
        )
    )


# Global config instance
config = load_config()