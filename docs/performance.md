# Performance Guide

Apollo's performance metrics, benchmarks, and optimization strategies.

## Current Performance (v4.1)

### GPU Acceleration Success

| Metric | CPU Baseline | GPU (CUDA) | Improvement |
|--------|--------------|------------|-------------|
| **Inference Speed** | 4.1 tok/s | 63.8 tok/s | **15.6x faster** |
| **Query Latency (P95)** | 18-25s | 2.0s | **10x faster** |
| **Throughput** | 2-3 req/min | 30-40 req/min | **13x higher** |

**Hardware**: NVIDIA RTX 5080 (16GB VRAM) with CUDA 12.1

### Query Latency Breakdown

**Simple Mode** (P50: 1.2s, P95: 2.0s):

```
Component              Time    Percentage
────────────────────────────────────────
Embedding Generation    25ms       2%
Vector Search (Qdrant)   4ms     0.3%
Cross-Encoder Reranking 820ms     65%
LLM Generation (GPU)    650ms     52%
Other Overhead          50ms       4%
────────────────────────────────────────
Total                 ~1.2s      100%
```

**Adaptive Mode** (P50: 3.0s, P95: 5.0s):
- Additional query classification: +100ms
- More reranking candidates: +800ms
- Longer LLM responses: +1000ms

### Cache Performance

| Layer | Hit Rate | Latency | Purpose |
|-------|----------|---------|---------|
| **L1** (Exact) | 40-50% | <1ms | Exact query match |
| **L2** (Normalized) | 10-15% | <1ms | Case-insensitive match |
| **L3** (Semantic) | 10-20% | <20ms | Similar queries (Redis) |
| **L4** (Embeddings) | 80-90% | <10ms | Cached vectors (Redis) |
| **L5** (Results) | 60-70% | <15ms | Cached LLM outputs (Redis) |
| **Overall** | **60-85%** | **<1ms avg** | **Combined effectiveness** |

---

## Resource Utilization

### VRAM Usage (16GB RTX 5080)

```
Embedding Model (BGE-large):      500MB   (3%)
LLM Model (Llama 3.1 8B):           6GB  (37.5%)
KV Cache:                           2GB  (12.5%)
CUDA Overhead:                    1.5GB   (9%)
────────────────────────────────────────────
Total Used:                        10GB  (62.5%)
Available:                          6GB  (37.5%)
```

### RAM Usage (96GB System)

```
Qdrant Vector DB:                  24GB   (25%)
Redis Cache:                        8GB    (8%)
Backend (FastAPI):                  4GB    (4%)
OS + Other Services:               12GB  (12.5%)
────────────────────────────────────────────
Total Used:                        48GB   (50%)
Available:                         48GB   (50%)
```

### CPU Utilization

- **Idle**: 5-10%
- **Query Processing**: 40-60%
- **Document Indexing**: 80-95%

---

## Optimization Strategies

### 1. Increase LLM Speed

**Current**: 63.8 tok/s

**Optimizations**:

```yaml
# backend/config.yml
llamacpp:
  n_gpu_layers: 50          # Increase from 35 (if VRAM allows)
  n_batch: 1024             # Increase from 512
  flash_attn: true          # Enable Flash Attention 2 (if supported)
```

**Expected Gain**: +10-15% speed

### 2. Reduce Query Latency

**Current**: P95 = 2.0s

**Optimizations**:

```yaml
retrieval:
  initial_k: 50             # Reduce from 100
  rerank_k: 15              # Reduce from 30
  final_k: 5                # Reduce from 8
```

**Expected Gain**: -30% latency (1.4s P95)

**Trade-off**: Slight reduction in answer quality

### 3. Improve Cache Hit Rate

**Current**: 60-85%

**Optimizations**:

```yaml
cache:
  cache_ttl: 7200           # Increase from 3600 (2 hours)
  max_cache_size: 20000     # Increase from 10000

  # Add query normalization
  normalize_queries: true   # Lowercase, remove punctuation
```

**Expected Gain**: +10-15% hit rate

### 4. Faster Vector Search

**Current**: 3-5ms

**Optimizations**:

```yaml
qdrant:
  hnsw_m: 8                 # Reduce from 16
  hnsw_ef_construct: 64     # Reduce from 128
```

**Expected Gain**: -50% search time (1.5-2.5ms)

**Trade-off**: Slight reduction in search quality

---

## Performance Tuning Profiles

### Speed Priority

**Goal**: Minimize latency at all costs

```yaml
llamacpp:
  n_gpu_layers: 35
  n_ctx: 4096               # Reduce context window

retrieval:
  initial_k: 50
  rerank_k: 10
  final_k: 3                # Fewer sources

qdrant:
  hnsw_m: 8
  hnsw_ef_construct: 64
```

**Expected Performance**:
- Query Latency: 0.8-1.0s (P95)
- Cache Hit: 70-80%
- Answer Quality: Good (not excellent)

### Quality Priority

**Goal**: Best possible answers

```yaml
llamacpp:
  model_path: "/models/qwen2.5-14b-instruct-q5_k_m.gguf"
  n_gpu_layers: 40
  n_ctx: 8192

retrieval:
  initial_k: 200
  rerank_k: 50
  final_k: 15               # More sources

qdrant:
  hnsw_m: 32
  hnsw_ef_construct: 256
```

**Expected Performance**:
- Query Latency: 4-6s (P95)
- Cache Hit: 50-60%
- Answer Quality: Excellent

### Balanced (Default)

**Goal**: Best of both worlds

```yaml
llamacpp:
  n_gpu_layers: 35
  n_ctx: 8192

retrieval:
  initial_k: 100
  rerank_k: 30
  final_k: 8

qdrant:
  hnsw_m: 16
  hnsw_ef_construct: 128
```

**Expected Performance**:
- Query Latency: 1.2-2.0s (P95)
- Cache Hit: 60-85%
- Answer Quality: Very Good

---

## Monitoring Performance

### Real-Time Metrics

**GPU Utilization**:
```bash
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv -l 1
```

**Container Stats**:
```bash
docker stats apollo-backend apollo-qdrant apollo-redis
```

**API Metrics**:
```bash
curl http://localhost:8000/api/cache/metrics
```

### Performance Dashboard

Apollo exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

**Key Metrics**:
- `apollo_query_latency_seconds` - Query processing time
- `apollo_cache_hit_rate` - Cache effectiveness
- `apollo_llm_tokens_per_second` - Inference speed
- `apollo_active_requests` - Concurrent queries

---

## Benchmarking

### Query Performance Test

```python
import time
import requests

def benchmark_queries(num_queries=100):
    url = "http://localhost:8000/api/query"
    times = []

    for i in range(num_queries):
        start = time.time()
        response = requests.post(url, json={
            "question": f"Test query {i}",
            "mode": "simple"
        })
        elapsed = time.time() - start
        times.append(elapsed)

    print(f"P50: {sorted(times)[len(times)//2]:.2f}s")
    print(f"P95: {sorted(times)[int(len(times)*0.95)]:.2f}s")
    print(f"P99: {sorted(times)[int(len(times)*0.99)]:.2f}s")

benchmark_queries()
```

### Cache Hit Rate Test

```bash
# Send same query 10 times
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/query \
    -H "Content-Type: application/json" \
    -d '{"question":"What is Apollo?"}' \
    -w "\nTime: %{time_total}s\n"
done

# Check cache metrics
curl http://localhost:8000/api/cache/metrics
```

---

## Performance Targets

| Metric | Target | Current (v4.1) | Status |
|--------|--------|----------------|--------|
| Query Latency (P95) | <2s | 2.0s | ✅ Met |
| LLM Speed | 60+ tok/s | 63.8 tok/s | ✅ Exceeded |
| Cache Hit Rate | >60% | 60-85% | ✅ Exceeded |
| GPU Utilization | 50-90% | 70-85% | ✅ Optimal |
| Document Support | 10K+ | 10K-100K | ✅ Exceeded |
| Throughput | 30+ req/min | 30-40 req/min | ✅ Met |

---

[← Back to Configuration](configuration.md) | [Next: Model Management →](model-management.md)
