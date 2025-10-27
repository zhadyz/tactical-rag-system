# Configuration Guide

Apollo uses a centralized YAML configuration file for all settings.

**Location**: `backend/config.yml`

## Core Settings

```yaml
# System Paths
documents_dir: "./documents"
qdrant_db_dir: "./qdrant_storage"
cache_dir: "./.cache"

# Service Endpoints
api_host: "0.0.0.0"
api_port: 8000
```

---

## LLM Configuration

### llama.cpp Backend (Recommended)

```yaml
llm_backend: "llamacpp"

llamacpp:
  model_path: "/models/llama-3.1-8b-instruct.Q5_K_M.gguf"

  # GPU Settings
  n_gpu_layers: 35              # Full GPU offload (16GB VRAM)
  n_ctx: 8192                   # Context window
  n_batch: 512                  # Processing batch size
  n_threads: 8                  # CPU fallback threads

  # Memory Optimization
  use_mlock: true               # Lock model in RAM
  use_mmap: true                # Memory-mapped file loading

  # Generation Parameters
  temperature: 0.0              # Deterministic output (0.0-2.0)
  top_p: 0.9                    # Nucleus sampling
  top_k: 40                     # Top-K sampling
  repeat_penalty: 1.1           # Reduce repetition
  max_tokens: 2048              # Max response length
```

### GPU Layer Recommendations

| VRAM | Model | n_gpu_layers | Performance |
|------|-------|--------------|-------------|
| 8GB | Llama 3.1 8B | 15-20 | ~40 tok/s |
| 12GB | Llama 3.1 8B | 25-30 | ~55 tok/s |
| 16GB | Llama 3.1 8B | 35 (full) | ~64 tok/s |
| 16GB | Qwen 2.5 14B | 25-30 | ~35 tok/s |
| 24GB | Qwen 2.5 14B | 45 (full) | ~50 tok/s |

---

## Embedding Configuration

**CRITICAL**: Changing the embedding model requires full re-indexing!

```yaml
embedding:
  model_name: "BAAI/bge-large-en-v1.5"  # HuggingFace model ID
  model_type: "huggingface"
  dimension: 1024                        # Must match model
  batch_size: 64                         # GPU batch size
  cache_embeddings: true                 # Enable L4 cache
```

### Batch Size Tuning

| VRAM | batch_size | Speed |
|------|------------|-------|
| 8GB | 32 | Conservative |
| 16GB | 64 | Recommended |
| 24GB+ | 128 | Aggressive |

---

## Retrieval Configuration

```yaml
retrieval:
  # Candidate Selection
  initial_k: 100                # Initial search candidates
  rerank_k: 30                  # Candidates for reranking
  final_k: 8                    # Final sources for LLM

  # Hybrid Weights (must sum to 1.0)
  dense_weight: 0.6             # Semantic similarity
  sparse_weight: 0.4            # BM25 keyword matching

  # Fusion
  fusion_method: "rrf"          # Reciprocal Rank Fusion
  rrf_k: 60                     # RRF constant
```

### Tuning Profiles

| Profile | initial_k | rerank_k | final_k | Use Case |
|---------|-----------|----------|---------|----------|
| **Fast** | 50 | 15 | 5 | Speed priority, lower recall |
| **Balanced** | 100 | 30 | 8 | **Default (recommended)** |
| **Accurate** | 200 | 50 | 15 | Quality priority, higher recall |

---

## Cache Configuration

```yaml
cache:
  # Enable/Disable Layers
  enable_embedding_cache: true  # L4: Embedding vectors
  enable_query_cache: true      # L3: Semantic similarity
  enable_result_cache: true     # L5: LLM outputs

  # Cache Parameters
  cache_ttl: 3600               # 1 hour (seconds)
  max_cache_size: 10000         # Max entries per layer

  # Redis (Distributed Cache)
  use_redis: true
  redis_host: "redis"           # Docker service name
  redis_port: 6379
  redis_db: 0
```

### Cache Layer Details

| Layer | Storage | TTL | Purpose | Hit Rate |
|-------|---------|-----|---------|----------|
| L1 | In-Memory | None | Exact query match | 40-50% |
| L2 | In-Memory | None | Normalized query | 10-15% |
| L3 | Redis | 1h | Semantic similarity | 10-20% |
| L4 | Redis | 24h | Embedding vectors | 80-90% |
| L5 | Redis | 1h | LLM results | 60-70% |

---

## Qdrant Configuration

```yaml
qdrant:
  # Connection
  host: "qdrant"                # Docker service name
  port: 6333
  collection_name: "documents"

  # Hybrid Search
  enable_hybrid_search: true
  dense_prefetch_limit: 20      # Semantic candidates
  sparse_prefetch_limit: 20     # BM25 candidates
  fusion_algorithm: "rrf"

  # HNSW Index (Hierarchical Navigable Small World)
  hnsw_m: 16                    # Graph connectivity
  hnsw_ef_construct: 128        # Build quality

  # Memory Management
  on_disk_payload: false        # Keep in RAM
  memmap_threshold: null        # No disk mapping
  indexing_threshold: 20000     # Index after 20K docs

  # Reranking
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-12-v2"
  relevance_threshold: 0.2      # Min similarity score
```

### HNSW Tuning

| Profile | hnsw_m | hnsw_ef_construct | Search Latency | Quality |
|---------|--------|-------------------|----------------|---------|
| Fast | 8 | 64 | ~2ms | Good |
| **Balanced** | **16** | **128** | **~5ms** | **Very Good** |
| Accurate | 32 | 256 | ~10ms | Excellent |

---

## Performance Configuration

```yaml
performance:
  # Threading
  max_workers: 16               # Thread pool (CPU cores × 2)
  enable_async: true            # Async I/O

  # Database Connections
  connection_pool_size: 20      # Qdrant connections

  # Batching
  enable_batching: true
  batch_timeout_ms: 50          # Wait time before processing
  max_batch_size: 128           # Max batch items
```

---

## Example Configurations

### Development (Low VRAM)

```yaml
llamacpp:
  model_path: "/models/llama-3.1-8b-instruct.Q5_K_M.gguf"
  n_gpu_layers: 20              # Partial GPU offload
  n_ctx: 4096                   # Smaller context

embedding:
  batch_size: 32                # Conservative batch

retrieval:
  initial_k: 50                 # Fewer candidates
  rerank_k: 15
  final_k: 5

qdrant:
  hnsw_m: 8                     # Faster search
  hnsw_ef_construct: 64
```

### Production (High Performance)

```yaml
llamacpp:
  model_path: "/models/qwen2.5-14b-instruct-q5_k_m.gguf"
  n_gpu_layers: 40              # Full GPU offload
  n_ctx: 8192                   # Large context

embedding:
  batch_size: 128               # Aggressive batching

retrieval:
  initial_k: 200                # More candidates
  rerank_k: 50
  final_k: 15

qdrant:
  hnsw_m: 32                    # Best quality
  hnsw_ef_construct: 256

cache:
  cache_ttl: 7200               # 2 hours
  max_cache_size: 50000         # Large cache
```

---

## Applying Configuration Changes

1. **Edit config file**:
   ```bash
   nano backend/config.yml
   ```

2. **Restart backend**:
   ```bash
   docker restart apollo-backend
   ```

3. **Verify changes**:
   ```bash
   curl http://localhost:8000/api/settings
   ```

---

[← Back to API Reference](api-reference.md) | [Next: Performance →](performance.md)
