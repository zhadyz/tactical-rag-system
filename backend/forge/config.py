"""
Forge - Configuration Management

Loads configuration from config.yml and provides ForgeConfig dataclass.
Extends the original ATLAS config with BGE-M3, ColBERT, contextual retrieval,
propositions, knowledge graph, agent, and CRAG settings.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RerankPreset(str, Enum):
    QUICK = "quick"
    QUALITY = "quality"
    DEEP = "deep"


# ---------------------------------------------------------------------------
# Preserved config sections (adapted from _src/config.py)
# ---------------------------------------------------------------------------

@dataclass
class LLMConfig:
    """Ollama fallback LLM configuration."""
    model_name: str = "qwen2.5:14b-instruct-q4_K_M"
    temperature: float = 0.0
    top_p: float = 0.9
    top_k: int = 40
    num_ctx: int = 8192
    repeat_penalty: float = 1.1
    timeout: int = 120


@dataclass
class LlamaCppConfig:
    """llama.cpp direct inference configuration."""
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
    draft_model_path: Optional[str] = None
    enable_speculative_decoding: bool = False
    n_gpu_layers_draft: int = 33
    num_draft: int = 5


@dataclass
class CacheConfig:
    """Redis caching configuration."""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    ttl: int = 86400 * 7  # 7 days
    max_cache_size: int = 10000


@dataclass
class SemanticChunkingConfig:
    """Semantic chunking configuration for L2 chunks."""
    enable_semantic_chunking: bool = True
    buffer_size: int = 1
    breakpoint_threshold: float = 0.75
    min_chunk_size: int = 200
    max_chunk_size: int = 2000


# ---------------------------------------------------------------------------
# New Forge V5 config sections
# ---------------------------------------------------------------------------

@dataclass
class BGEM3Config:
    """BGE-M3 embedding model configuration (dense + sparse + ColBERT)."""
    model_name: str = "BAAI/bge-m3"
    dimension: int = 1024
    device: str = "cpu"
    batch_size: int = 64
    cache_embeddings: bool = True
    normalize_embeddings: bool = True
    max_length: int = 8192


@dataclass
class ColBERTConfig:
    """ColBERT late-interaction reranking configuration."""
    enable_colbert: bool = True
    rerank_top_k: int = 20
    max_query_length: int = 64
    max_doc_length: int = 512


@dataclass
class ContextualRetrievalConfig:
    """Anthropic-style contextual retrieval enrichment."""
    enable: bool = True
    context_prefix_max_tokens: int = 100
    batch_size: int = 10


@dataclass
class PropositionConfig:
    """Dense-X proposition extraction settings."""
    enable: bool = True
    max_propositions_per_chunk: int = 10
    batch_size: int = 5


@dataclass
class GraphConfig:
    """Knowledge graph construction settings."""
    enable: bool = True
    entity_types: List[str] = field(default_factory=lambda: [
        "regulation", "role", "procedure", "requirement", "date",
        "organization", "location", "equipment",
    ])
    relationship_types: List[str] = field(default_factory=lambda: [
        "authorizes", "requires", "references", "supersedes",
        "applies_to", "defines", "amends",
    ])
    max_entities_per_chunk: int = 20
    max_relationships_per_chunk: int = 30


@dataclass
class AgentConfig:
    """LangGraph agentic loop settings."""
    max_iterations: int = 3
    tools_enabled: List[str] = field(default_factory=lambda: [
        "semantic_search", "proposition_search", "keyword_search",
        "graph_traverse", "chunk_read", "section_read",
    ])
    default_mode: str = "direct"  # "direct" or "agentic"


@dataclass
class CRAGConfig:
    """Corrective RAG quality-gate settings."""
    threshold_correct: float = 0.7
    threshold_ambiguous: float = 0.3
    max_retries: int = 1
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"


@dataclass
class RetrievalConfig:
    """Retrieval pipeline configuration."""
    initial_k: int = 100
    rerank_k: int = 30
    final_k: int = 8
    dense_weight: float = 0.5
    sparse_weight: float = 0.5
    similarity_threshold: float = 0.5
    use_reranking: bool = True


# ---------------------------------------------------------------------------
# Top-level system config
# ---------------------------------------------------------------------------

@dataclass
class ForgeConfig:
    """Complete Forge system configuration."""
    # Paths
    documents_dir: Path = Path("./documents")
    qdrant_db_dir: Path = Path("./qdrant_storage")
    cache_dir: Path = Path("./.cache")

    # Service endpoints
    ollama_host: str = "http://ollama:11434"
    api_host: str = "0.0.0.0"
    api_port: int = 7860

    # LLM backend selection
    llm_backend: str = "llamacpp"  # "ollama" or "llamacpp"

    # Qdrant collection
    collection_name: str = "forge_documents"

    # Preserved component configs
    llm: LLMConfig = field(default_factory=LLMConfig)
    llamacpp: LlamaCppConfig = field(default_factory=LlamaCppConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    semantic_chunking: SemanticChunkingConfig = field(default_factory=SemanticChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)

    # New Forge V5 configs
    bge_m3: BGEM3Config = field(default_factory=BGEM3Config)
    colbert: ColBERTConfig = field(default_factory=ColBERTConfig)
    contextual_retrieval: ContextualRetrievalConfig = field(default_factory=ContextualRetrievalConfig)
    propositions: PropositionConfig = field(default_factory=PropositionConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    crag: CRAGConfig = field(default_factory=CRAGConfig)


# ---------------------------------------------------------------------------
# YAML loader
# ---------------------------------------------------------------------------

def _parse_dataclass(dc_class, data: dict, defaults=None):
    """Parse a dict into a dataclass, falling back to defaults for missing keys."""
    if defaults is None:
        defaults = dc_class()
    kwargs = {}
    for f in dc_class.__dataclass_fields__:
        kwargs[f] = data.get(f, getattr(defaults, f))
    return dc_class(**kwargs)


def load_config(config_path: Optional[str] = None) -> ForgeConfig:
    """
    Load configuration from YAML file.

    Searches standard locations if config_path is not provided.
    Returns ForgeConfig with defaults for any missing sections.
    """
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
            return ForgeConfig()

    try:
        with open(config_path, "r") as f:
            yaml_data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return ForgeConfig()

    config = ForgeConfig()

    # --- Top-level scalars ---
    if "documents_dir" in yaml_data:
        config.documents_dir = Path(yaml_data["documents_dir"])
    if "qdrant_db_dir" in yaml_data:
        config.qdrant_db_dir = Path(yaml_data["qdrant_db_dir"])
    if "cache_dir" in yaml_data:
        config.cache_dir = Path(yaml_data["cache_dir"])
    if "ollama_host" in yaml_data:
        config.ollama_host = yaml_data["ollama_host"]
    if "api_host" in yaml_data:
        config.api_host = yaml_data["api_host"]
    if "api_port" in yaml_data:
        config.api_port = yaml_data["api_port"]
    if "llm_backend" in yaml_data:
        config.llm_backend = yaml_data["llm_backend"]
    if "collection_name" in yaml_data:
        config.collection_name = yaml_data["collection_name"]

    # --- Nested sections ---
    if "llm" in yaml_data:
        config.llm = _parse_dataclass(LLMConfig, yaml_data["llm"])
    if "llamacpp" in yaml_data:
        config.llamacpp = _parse_dataclass(LlamaCppConfig, yaml_data["llamacpp"])
    if "cache" in yaml_data:
        config.cache = _parse_dataclass(CacheConfig, yaml_data["cache"])
    if "semantic_chunking" in yaml_data:
        config.semantic_chunking = _parse_dataclass(SemanticChunkingConfig, yaml_data["semantic_chunking"])
    if "retrieval" in yaml_data:
        config.retrieval = _parse_dataclass(RetrievalConfig, yaml_data["retrieval"])

    # New Forge sections
    if "bge_m3" in yaml_data:
        config.bge_m3 = _parse_dataclass(BGEM3Config, yaml_data["bge_m3"])
    if "colbert" in yaml_data:
        config.colbert = _parse_dataclass(ColBERTConfig, yaml_data["colbert"])
    if "contextual_retrieval" in yaml_data:
        config.contextual_retrieval = _parse_dataclass(ContextualRetrievalConfig, yaml_data["contextual_retrieval"])
    if "propositions" in yaml_data:
        config.propositions = _parse_dataclass(PropositionConfig, yaml_data["propositions"])
    if "graph" in yaml_data:
        config.graph = _parse_dataclass(GraphConfig, yaml_data["graph"])
    if "agent" in yaml_data:
        config.agent = _parse_dataclass(AgentConfig, yaml_data["agent"])
    if "crag" in yaml_data:
        config.crag = _parse_dataclass(CRAGConfig, yaml_data["crag"])

    logger.info(f"Forge config loaded: backend={config.llm_backend}, collection={config.collection_name}")
    return config
