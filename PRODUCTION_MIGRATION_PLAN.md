# Production Migration Plan - Air Force Technical Documentation RAG

**Goal**: Scale to thousands of documents with 5-10 second response times

**Hardware**: 128GB RAM, 24GB VRAM

**Target Scale**: 500k-2M chunks

---

## Phase 1: Quick Wins (Week 1)

### 1.1 Deploy Qdrant

```bash
# Add to docker-compose.yml
docker-compose up qdrant -d

# Verify
curl http://localhost:6333/collections
```

### 1.2 Implement Embedding Cache

**Files to create:**
- `_src/embedding_cache.py` (Redis-backed cache)
- Update `_src/config.py` (add cache config)

**Expected impact**: 5-8s savings per query (80% hit rate)

### 1.3 Benchmark Current System

**Test queries**: 100 diverse queries from Air Force SOPs

**Metrics to measure**:
- P50, P95, P99 latency
- Cache hit rates
- GPU utilization
- Memory usage

**Script**: `tests/benchmark_production.py`

---

## Phase 2: Vector DB Migration (Week 2)

### 2.1 Create Migration Script

**File**: `scripts/migrate_to_qdrant.py`

Steps:
1. Read all documents from `documents/`
2. Generate embeddings (with progress bar)
3. Create Qdrant collection with optimized config
4. Batch insert (100 docs at a time)
5. Verify index integrity

### 2.2 Update Retrieval Engine

**Files to modify**:
- `_src/adaptive_retrieval.py` (use Qdrant client)
- `_src/app.py` (initialize Qdrant instead of ChromaDB)
- `_src/config.py` (add Qdrant config)

**Backwards compatibility**: Keep ChromaDB support with feature flag

### 2.3 Implement Query Optimization

**Features**:
- Query normalization (40-60% cache hit rate boost)
- Pre-filtering (by document ID, category)
- HNSW parameter tuning

**Expected impact**: 10-30s → 2-5s retrieval time

---

## Phase 3: vLLM Integration (Week 3)

### 3.1 Deploy vLLM Server

```bash
# Add to docker-compose.yml
docker-compose up vllm-server -d

# Test
curl http://localhost:8001/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Llama-3.1-8B-Instruct", "prompt": "Hello", "max_tokens": 50}'
```

### 3.2 Update Answer Generator

**Files to modify**:
- `_src/adaptive_retrieval.py` (AdaptiveAnswerGenerator)
- Use OpenAI client with vLLM base_url

**Expected impact**: 16s → 1-2s generation time

### 3.3 Implement Streaming

**Backend**: Already has `/api/query/stream` endpoint!

**Frontend**: Implement SSE client
- `frontend/src/hooks/useStreamingQuery.ts`
- Update `ChatMessage.tsx` to show incremental responses

---

## Phase 4: Production Hardening (Weeks 4-6)

### 4.1 Incremental Indexing

**File**: `_src/incremental_indexer.py`

**Features**:
- Detect new/changed/deleted documents
- Background indexing (non-blocking)
- Progress tracking API
- Atomic index swaps

### 4.2 Monitoring & Observability

**Tools**:
- Prometheus metrics export
- Grafana dashboards
- Alert rules (latency, error rate, GPU utilization)

**Dashboards**:
- Query latency (P50, P95, P99)
- Cache hit rates
- GPU/CPU/Memory usage
- Index size & growth
- Error rates by component

### 4.3 Load Testing

**Script**: `tests/load_test.py`

**Scenarios**:
- 10 concurrent users
- 100 concurrent users
- Burst traffic (1000 req/min)
- Long-running queries

**Success criteria**:
- P95 latency < 10s
- No crashes or OOM
- Cache hit rate > 80%

---

## Critical Decisions Needed

### Decision 1: Vector Database

**Option A: Qdrant** ✅ RECOMMENDED
- Pros: Fastest, easiest migration, excellent docs
- Cons: Less mature ecosystem than Weaviate

**Option B: Weaviate**
- Pros: Built-in hybrid search, better multi-tenancy
- Cons: More complex, slightly slower

**Recommendation**: Start with Qdrant. Easier migration, faster performance.

### Decision 2: Embedding Model

**Current**: nomic-embed-text (768-dim)
- Pros: Good quality, decent speed
- Cons: Not the fastest

**Alternative**: BAAI/bge-large-en-v1.5 (1024-dim)
- Pros: Better quality (+5-10% accuracy)
- Cons: Slower, larger index

**Recommendation**: Keep nomic-embed-text initially. Optimize later if accuracy isn't sufficient.

### Decision 3: Reranking Strategy

**Current**: CrossEncoder on GPU
- Works well, keep it

**Enhancement**: Consider Cohere Rerank API
- Pros: Best quality, no GPU needed
- Cons: API cost, latency

**Recommendation**: Keep GPU reranking. No external dependencies.

---

## Risk Mitigation

### Risk 1: Migration breaks existing queries
**Mitigation**: Feature flag for ChromaDB/Qdrant, A/B test

### Risk 2: vLLM model compatibility issues
**Mitigation**: Test with smaller model first (Llama-3-8B)

### Risk 3: Performance regression
**Mitigation**: Comprehensive benchmarking before/after each phase

### Risk 4: Index corruption during migration
**Mitigation**: Backup existing ChromaDB, rollback script ready

---

## Success Metrics

### Performance Metrics
- ✅ Cold query: < 10s (P95)
- ✅ Warm query: < 5s (P95)
- ✅ Hot query: < 1s (cache hit)
- ✅ Indexing: < 2 hours for full corpus

### Quality Metrics
- ✅ Retrieval accuracy: > 95% (Phase 0 baseline)
- ✅ Answer accuracy: > 90% (human eval)
- ✅ Out-of-scope detection: > 95% precision

### Scalability Metrics
- ✅ Handles 2M chunks without degradation
- ✅ 100 concurrent users supported
- ✅ Index growth: 1000 docs/hour

### Reliability Metrics
- ✅ Uptime: > 99.9%
- ✅ Error rate: < 0.1%
- ✅ Cache hit rate: > 80%

---

## Next Steps

1. **Today**: Set up Qdrant container, test basic operations
2. **Tomorrow**: Implement embedding cache, measure impact
3. **This Week**: Complete Phase 1 benchmarking
4. **Week 2**: Begin Qdrant migration

Let's build a battle-tested RAG system! 🚀
