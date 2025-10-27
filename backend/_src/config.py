"""
ATLAS Protocol - Configuration Management

Loads configuration from config.yml and provides SystemConfig dataclass.
Integrates with llama.cpp backend selection.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RerankPreset(str, Enum):
    """Rerank preset options for performance/quality tradeoff"""
    QUICK = "quick"      # 2 documents - fastest
    QUALITY = "quality"  # 3 documents - balanced (default)
    DEEP = "deep"        # 5 documents - highest quality


@dataclass
class EmbeddingConfig:
    """Embedding model configuration"""
    model_name: str = "BAAI/bge-large-en-v1.5"
    model_type: str = "huggingface"  # or "ollama"
    dimension: int = 1024
    batch_size: int = 64
    cache_embeddings: bool = True
    normalize_embeddings: bool = True


@dataclass
class LLMConfig:
    """LLM configuration (legacy Ollama)"""
    model_name: str = "qwen2.5:14b-instruct-q4_K_M"
    temperature: float = 0.0
    top_p: float = 0.9
    top_k: int = 40
    num_ctx: int = 8192
    repeat_penalty: float = 1.1
    timeout: int = 120


@dataclass
class LlamaCppConfig:
    """llama.cpp direct inference configuration"""
    model_path: str = "./models/llama-3.1-8b-instruct.Q5_K_M.gguf"
    n_gpu_layers: int = 33
    n_ctx: int = 8192
    n_batch: int = 512
    n_threads: int = 8
    use_mlock: bool = True
    use_mmap: bool = True
    temperature: float = 0.0
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 2048
    verbose: bool = False

    # QUICK WIN #8: Speculative Decoding (500ms → 300ms)
    draft_model_path: Optional[str] = None  # "./models/Llama-3.2-1B-Instruct.Q4_K_M.gguf"
    enable_speculative_decoding: bool = False
    n_gpu_layers_draft: int = 33
    num_draft: int = 5


@dataclass
class ChunkingConfig:
    """Document chunking configuration"""
    strategy: str = "hybrid"
    chunk_size: int = 1200
    chunk_overlap: int = 400
    min_chunk_size: int = 100
    semantic_similarity_threshold: float = 0.7


@dataclass
class RetrievalConfig:
    """Advanced retrieval configuration"""
    initial_k: int = 100
    rerank_k: int = 30
    final_k: int = 8
    dense_weight: float = 0.5
    sparse_weight: float = 0.5
    similarity_threshold: float = 0.5
    use_reranking: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"
    use_multi_query: bool = True  # Enable multi-query fusion for vague queries
    multi_query_variants: int = 4  # Number of query variants to generate


@dataclass
class QueryTransformationConfig:
    """Query transformation configuration (HyDE, Multi-Query, Classification)"""
    enable_hyde: bool = True  # Enable HyDE (Hypothetical Document Embeddings)
    enable_multiquery_rewrite: bool = True  # Enable policy-oriented query rewriting
    enable_classification: bool = True  # Enable query classification for adaptive retrieval
    hyde_include_original: bool = True  # Include original query with HyDE
    multiquery_num_variants: int = 3  # Number of query variants to generate
    hyde_temperature: float = 0.3  # LLM temperature for HyDE
    rewrite_temperature: float = 0.5  # LLM temperature for query rewriting


@dataclass
class BGERerankerConfig:
    """BGE Reranker v2-m3 configuration (Quick Win #7)"""
    enable_bge_reranker: bool = True  # Enable BGE Reranker (85% faster than LLM)
    model_name: str = "BAAI/bge-reranker-v2-m3"
    batch_size: int = 32  # Optimal for RTX 5080
    max_length: int = 512  # Max tokens per document
    device: str = "cuda"  # or "cpu"
    normalize_scores: bool = True


@dataclass
class AdvancedRerankingConfig:
    """Advanced reranking configuration (BGE/LLM-based + Cross-Encoder)"""
    # QUICK WIN #7: BGE Reranker v2-m3 (400ms → 60ms)
    enable_bge_reranker: bool = True  # Prefer BGE over LLM (85% speedup)
    bge_reranker_device: str = "cuda"  # GPU acceleration
    bge_reranker_batch_size: int = 32

    # LLM reranking (fallback)
    enable_llm_reranking: bool = True  # Fallback if BGE unavailable
    llm_rerank_top_n: int = 3  # QUICK WIN #3: Reduced from 5→3 (15-20% speedup)
    rerank_preset: RerankPreset = RerankPreset.QUALITY  # Default preset
    hybrid_rerank_alpha: float = 0.7  # Weight for cross-encoder vs reranker (0-1)
    llm_scoring_temperature: float = 0.0  # LLM temperature for scoring

    def get_rerank_count_for_preset(self, preset: Optional[RerankPreset] = None) -> int:
        """Get document count for a specific preset"""
        preset = preset or self.rerank_preset
        preset_map = {
            RerankPreset.QUICK: 2,
            RerankPreset.QUALITY: 3,
            RerankPreset.DEEP: 5
        }
        return preset_map.get(preset, 3)  # Default to 3 if unknown


@dataclass
class SemanticChunkingConfig:
    """Semantic chunking configuration"""
    enable_semantic_chunking: bool = True  # Use semantic chunking vs fixed-size
    buffer_size: int = 1  # Sentences to combine for embedding
    breakpoint_threshold: float = 0.75  # Similarity threshold for splits (0-1)
    min_chunk_size: int = 200  # Minimum characters per chunk
    max_chunk_size: int = 2000  # Maximum characters per chunk


@dataclass
class CacheConfig:
    """Caching configuration"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    ttl: int = 86400 * 7  # 7 days
    max_cache_size: int = 10000


@dataclass
class ScopeDetectionConfig:
    """Scope detection configuration"""
    metadata_path: str = "./chroma_db/collection_metadata.json"
    force_recompute: bool = False
    enable_scope_detection: bool = True


@dataclass
class SystemConfig:
    """Complete system configuration"""
    # Paths
    documents_dir: Path = Path("./documents")
    vector_db_dir: Path = Path("./chroma_db")
    qdrant_db_dir: Path = Path("./qdrant_storage")
    cache_dir: Path = Path("./.cache")

    # Vector store selection
    vector_store: str = "qdrant"  # "chromadb" or "qdrant"

    # Service endpoints
    ollama_host: str = "http://ollama:11434"
    api_host: str = "0.0.0.0"
    api_port: int = 7860

    # LLM backend selection
    llm_backend: str = "llamacpp"  # "ollama" or "llamacpp"

    # Component configs
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    llamacpp: LlamaCppConfig = field(default_factory=LlamaCppConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    scope_detection: ScopeDetectionConfig = field(default_factory=ScopeDetectionConfig)

    # Advanced RAG optimizations
    query_transformation: QueryTransformationConfig = field(default_factory=QueryTransformationConfig)
    advanced_reranking: AdvancedRerankingConfig = field(default_factory=AdvancedRerankingConfig)
    semantic_chunking: SemanticChunkingConfig = field(default_factory=SemanticChunkingConfig)


def load_config(config_path: Optional[str] = None) -> SystemConfig:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config.yml. If None, searches in standard locations.

    Returns:
        SystemConfig instance with loaded configuration
    """
    # Search for config.yml in standard locations
    if config_path is None:
        search_paths = [
            Path("./config.yml"),
            Path("../config.yml"),
            Path("../../config.yml"),
            Path("/app/config.yml"),
        ]

        for path in search_paths:
            if path.exists():
                config_path = str(path)
                logger.info(f"Found config at: {config_path}")
                break
        else:
            logger.warning("No config.yml found, using defaults")
            return SystemConfig()

    # Load YAML
    try:
        with open(config_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return SystemConfig()

    # Parse configuration
    config = SystemConfig()

    # Paths
    if 'documents_dir' in yaml_data:
        config.documents_dir = Path(yaml_data['documents_dir'])
    if 'vector_db_dir' in yaml_data:
        config.vector_db_dir = Path(yaml_data['vector_db_dir'])
    if 'qdrant_db_dir' in yaml_data:
        config.qdrant_db_dir = Path(yaml_data['qdrant_db_dir'])
    if 'cache_dir' in yaml_data:
        config.cache_dir = Path(yaml_data['cache_dir'])

    # Vector store
    if 'vector_store' in yaml_data:
        config.vector_store = yaml_data['vector_store']

    # Endpoints
    if 'ollama_host' in yaml_data:
        config.ollama_host = yaml_data['ollama_host']
    if 'api_host' in yaml_data:
        config.api_host = yaml_data['api_host']
    if 'api_port' in yaml_data:
        config.api_port = yaml_data['api_port']

    # LLM backend
    if 'llm_backend' in yaml_data:
        config.llm_backend = yaml_data['llm_backend']

    # Embedding config
    if 'embedding' in yaml_data:
        emb_data = yaml_data['embedding']
        config.embedding = EmbeddingConfig(
            model_name=emb_data.get('model_name', config.embedding.model_name),
            model_type=emb_data.get('model_type', config.embedding.model_type),
            dimension=emb_data.get('dimension', config.embedding.dimension),
            batch_size=emb_data.get('batch_size', config.embedding.batch_size),
            cache_embeddings=emb_data.get('cache_embeddings', config.embedding.cache_embeddings),
            normalize_embeddings=emb_data.get('normalize_embeddings', config.embedding.normalize_embeddings)
        )

    # LLM config (legacy Ollama)
    if 'llm' in yaml_data:
        llm_data = yaml_data['llm']
        config.llm = LLMConfig(
            model_name=llm_data.get('model_name', config.llm.model_name),
            temperature=llm_data.get('temperature', config.llm.temperature),
            top_p=llm_data.get('top_p', config.llm.top_p),
            top_k=llm_data.get('top_k', config.llm.top_k),
            num_ctx=llm_data.get('num_ctx', config.llm.num_ctx),
            repeat_penalty=llm_data.get('repeat_penalty', config.llm.repeat_penalty),
            timeout=llm_data.get('timeout', config.llm.timeout)
        )

    # llama.cpp config
    if 'llamacpp' in yaml_data:
        lc_data = yaml_data['llamacpp']
        config.llamacpp = LlamaCppConfig(
            model_path=lc_data.get('model_path', config.llamacpp.model_path),
            n_gpu_layers=lc_data.get('n_gpu_layers', config.llamacpp.n_gpu_layers),
            n_ctx=lc_data.get('n_ctx', config.llamacpp.n_ctx),
            n_batch=lc_data.get('n_batch', config.llamacpp.n_batch),
            n_threads=lc_data.get('n_threads', config.llamacpp.n_threads),
            use_mlock=lc_data.get('use_mlock', config.llamacpp.use_mlock),
            use_mmap=lc_data.get('use_mmap', config.llamacpp.use_mmap),
            temperature=lc_data.get('temperature', config.llamacpp.temperature),
            top_p=lc_data.get('top_p', config.llamacpp.top_p),
            top_k=lc_data.get('top_k', config.llamacpp.top_k),
            repeat_penalty=lc_data.get('repeat_penalty', config.llamacpp.repeat_penalty),
            max_tokens=lc_data.get('max_tokens', config.llamacpp.max_tokens),
            verbose=lc_data.get('verbose', config.llamacpp.verbose)
        )

    # Chunking config
    if 'chunking' in yaml_data:
        chunk_data = yaml_data['chunking']
        config.chunking = ChunkingConfig(
            strategy=chunk_data.get('strategy', config.chunking.strategy),
            chunk_size=chunk_data.get('chunk_size', config.chunking.chunk_size),
            chunk_overlap=chunk_data.get('chunk_overlap', config.chunking.chunk_overlap),
            min_chunk_size=chunk_data.get('min_chunk_size', config.chunking.min_chunk_size),
            semantic_similarity_threshold=chunk_data.get('semantic_similarity_threshold', config.chunking.semantic_similarity_threshold)
        )

    # Retrieval config
    if 'retrieval' in yaml_data:
        ret_data = yaml_data['retrieval']
        config.retrieval = RetrievalConfig(
            initial_k=ret_data.get('initial_k', config.retrieval.initial_k),
            rerank_k=ret_data.get('rerank_k', config.retrieval.rerank_k),
            final_k=ret_data.get('final_k', config.retrieval.final_k),
            dense_weight=ret_data.get('dense_weight', config.retrieval.dense_weight),
            sparse_weight=ret_data.get('sparse_weight', config.retrieval.sparse_weight),
            similarity_threshold=ret_data.get('similarity_threshold', config.retrieval.similarity_threshold),
            use_reranking=ret_data.get('use_reranking', config.retrieval.use_reranking),
            reranker_model=ret_data.get('reranker_model', config.retrieval.reranker_model)
        )

    # Cache config
    cache_data = yaml_data.get('cache', {})
    config.cache = CacheConfig(
        redis_host=cache_data.get('redis_host', 'localhost'),
        redis_port=cache_data.get('redis_port', 6379),
        redis_db=cache_data.get('redis_db', 0),
        redis_password=cache_data.get('redis_password'),
        ttl=cache_data.get('ttl', 86400 * 7),
        max_cache_size=cache_data.get('max_cache_size', 10000)
    )

    # Scope detection
    scope_data = yaml_data.get('scope_detection', {})
    config.scope_detection = ScopeDetectionConfig(
        metadata_path=scope_data.get('metadata_path', './chroma_db/collection_metadata.json'),
        force_recompute=scope_data.get('force_recompute', False),
        enable_scope_detection=scope_data.get('enable_scope_detection', True)
    )

    # Advanced reranking config (CRITICAL FIX: Parse from YAML instead of using defaults)
    if 'advanced_reranking' in yaml_data:
        ar_data = yaml_data['advanced_reranking']
        config.advanced_reranking = AdvancedRerankingConfig(
            # BGE Reranker v2-m3 settings (Quick Win #7)
            enable_bge_reranker=ar_data.get('enable_bge_reranker', config.advanced_reranking.enable_bge_reranker),
            bge_reranker_device=ar_data.get('bge_reranker_device', config.advanced_reranking.bge_reranker_device),
            bge_reranker_batch_size=ar_data.get('bge_reranker_batch_size', config.advanced_reranking.bge_reranker_batch_size),
            # LLM reranking (fallback)
            enable_llm_reranking=ar_data.get('enable_llm_reranking', config.advanced_reranking.enable_llm_reranking),
            llm_rerank_top_n=ar_data.get('llm_rerank_top_n', config.advanced_reranking.llm_rerank_top_n),
            hybrid_rerank_alpha=ar_data.get('hybrid_rerank_alpha', config.advanced_reranking.hybrid_rerank_alpha),
            llm_scoring_temperature=ar_data.get('llm_scoring_temperature', config.advanced_reranking.llm_scoring_temperature),
            # Preset (if available)
            rerank_preset=RerankPreset(ar_data.get('rerank_preset', config.advanced_reranking.rerank_preset.value)) if 'rerank_preset' in ar_data else config.advanced_reranking.rerank_preset
        )

    logger.info(f"Configuration loaded: LLM backend={config.llm_backend}, Vector store={config.vector_store}")

    return config
