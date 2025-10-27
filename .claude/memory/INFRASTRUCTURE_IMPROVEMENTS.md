# Apollo v4.1 - Infrastructure Improvement Roadmap

**Generated**: 2025-10-26
**Context**: Post-memory deletion comprehensive analysis
**Status**: Actionable recommendations prioritized by impact

---

## Executive Summary

Apollo v4.1 has achieved significant optimization progress (60% speedup through 7 Quick Wins) but faces **critical infrastructure issues** that are blocking further performance gains. This document provides a prioritized roadmap for infrastructure improvements.

---

## Critical Priority (P0) - Immediate Action Required

### 1. Docker NVIDIA Runtime Fix

**Issue**: Container running with `runc` instead of `nvidia` runtime
- **Impact**: 10x performance degradation (22,000ms vs 2,000ms query time)
- **Root Cause**: Docker Compose v3.8 `runtime: nvidia` directive not honored
- **Evidence**: `docker inspect atlas-backend` shows `"Runtime": "runc"`
- **Fix Time**: 6-7 minutes
- **Priority**: P0 - BLOCKING

**Solution**:

Update `backend/docker-compose.atlas.yml` (lines 247-251):

```yaml
# BEFORE (broken)
runtime: nvidia
environment:
  - NVIDIA_VISIBLE_DEVICES=0
  - NVIDIA_DRIVER_CAPABILITIES=compute,utility

# AFTER (working - modern syntax)
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
environment:
  - NVIDIA_VISIBLE_DEVICES=0
  - NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

**Execution**:
```bash
cd backend
docker-compose -f docker-compose.atlas.yml down atlas-backend
docker-compose -f docker-compose.atlas.yml up -d --force-recreate atlas-backend
```

**Verification**:
```bash
# Should show GPU information
docker exec atlas-backend nvidia-smi

# Should return True
docker exec atlas-backend python -c "from llama_cpp import llama_supports_gpu_offload; print(llama_supports_gpu_offload())"
```

**Expected Result**: Query time drops from 22,000ms to ~2,000ms (10x speedup)

---

### 2. Speculative Decoding Config Parsing Fix

**Issue**: Config parser doesn't read speculative_decoding parameters from YAML
- **Impact**: 40% TTFT improvement blocked (500ms → 300ms)
- **Root Cause**: `backend/_src/config.py` lines 301-318 missing parameter parsing
- **Code Status**: Implementation exists in `llm_engine_llamacpp.py`, config exists in `config.yml`, but parser doesn't connect them
- **Fix Time**: 10 minutes
- **Priority**: P0 (after GPU fix)

**Solution**:

Add to `backend/_src/config.py` in `load_config()` function (around line 318):

```python
# Parse speculative decoding params from YAML
config.llamacpp = LlamaCppConfig(
    # ... existing params ...
    draft_model_path=lc_data.get('draft_model_path', config.llamacpp.draft_model_path),
    enable_speculative_decoding=lc_data.get('enable_speculative_decoding', config.llamacpp.enable_speculative_decoding),
    n_gpu_layers_draft=lc_data.get('n_gpu_layers_draft', config.llamacpp.n_gpu_layers_draft),
    num_draft=lc_data.get('num_draft', config.llamacpp.num_draft)
)
```

**Verification**:
```bash
# Check logs for speculative decoding initialization
docker logs atlas-backend 2>&1 | grep -i "speculative"
# Should show: "Speculative decoding enabled with draft model: ..."
```

**Expected Result**: Answer generation TTFT improves from 500ms to ~300ms (40% speedup)

---

## High Priority (P1) - This Week

### 3. Implement Quick Win #9: BGE-M3 Embeddings

**Goal**: Improve retrieval accuracy by 15-20%
- **Timeline**: 8-12 days (per Implementation Roadmap Phase 2)
- **Impact**: Recall@3: 0.70 → 0.82, multi-lingual support
- **Risk**: Medium (requires full document re-indexing)
- **Priority**: P1

**Implementation Steps**:

1. **Update Embedding Service** (`backend/_src/embedding_service.py`)
   ```python
   # Change model
   model_name = "BAAI/bge-m3"  # was: "BAAI/bge-large-en-v1.5"
   ```

2. **Backup Existing Collection**
   ```bash
   # Backup Qdrant collection
   docker exec qdrant curl -X POST "http://localhost:6333/collections/documents/snapshots"
   ```

3. **Trigger Re-indexing**
   ```bash
   curl -X POST http://localhost:8000/api/documents/reindex
   # Monitor progress: ~10K docs = 2-3 hours
   ```

4. **Validation**
   - Run 20 test queries (factual, procedural, temporal, comparative, complex)
   - Measure Recall@3, Recall@5, MRR
   - Test multi-lingual queries (Spanish, French)
   - A/B test: BGE-M3 vs bge-large-en-v1.5

**Success Criteria**:
- ✅ Recall@3 improvement ≥ 15%
- ✅ All documents re-indexed without errors
- ✅ Multi-lingual query support validated
- ✅ No degradation in English-only queries

---

### 4. Add GPU Metrics to Prometheus/Grafana

**Goal**: Real-time GPU utilization monitoring
- **Timeline**: 2-4 hours
- **Impact**: Proactive performance issue detection
- **Risk**: Low
- **Priority**: P1

**Implementation**:

1. **Add NVIDIA DCGM Exporter to docker-compose.atlas.yml**:
   ```yaml
   dcgm-exporter:
     image: nvcr.io/nvidia/k8s/dcgm-exporter:3.1.7-3.1.4-ubuntu20.04
     runtime: nvidia
     environment:
       - NVIDIA_VISIBLE_DEVICES=0
     ports:
       - "9400:9400"
     networks:
       - atlas-network
   ```

2. **Configure Prometheus Scraping** (`backend/monitoring/prometheus.yml`):
   ```yaml
   scrape_configs:
     - job_name: 'dcgm'
       static_configs:
         - targets: ['dcgm-exporter:9400']
   ```

3. **Create Grafana Dashboard**
   - Import NVIDIA DCGM dashboard (ID: 12239)
   - Metrics: gpu_utilization, gpu_memory_used, gpu_temperature, gpu_power_usage

**Expected Result**: Real-time visibility into GPU performance, alerts on anomalies

---

### 5. Upgrade Rate Limiting to Redis-Based

**Goal**: Scalable, distributed rate limiting
- **Timeline**: 1-2 hours
- **Impact**: Production-ready rate limiting
- **Current**: In-memory dictionary (single instance only)
- **Priority**: P1

**Implementation**:

Replace in-memory rate limiter in `backend/app/api/query.py` (lines 23-51):

```python
# OLD: In-memory rate limiter
rate_limit_dict = defaultdict(lambda: {"count": 0, "window_start": time.time()})

# NEW: Redis-based rate limiter
from redis import Redis
redis_client = Redis(host='redis', port=6379, decode_responses=True)

def check_rate_limit(ip: str, limit: int = 30, window: int = 60) -> bool:
    key = f"rate_limit:{ip}"
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, window)
    return count <= limit
```

**Benefits**:
- Distributed rate limiting across multiple backend instances
- Persistent across restarts
- Configurable per-endpoint limits

---

## Medium Priority (P2) - Next 2-4 Weeks

### 6. Add GPU Runtime Verification to CI/CD

**Goal**: Prevent GPU runtime issues from reaching production
- **Timeline**: 1-2 hours
- **Impact**: Catch configuration issues automatically
- **Priority**: P2

**Implementation**:

Create `backend/scripts/verify_gpu.sh`:
```bash
#!/bin/bash
set -e

# Verify NVIDIA runtime
if ! docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi; then
    echo "ERROR: NVIDIA runtime not accessible"
    exit 1
fi

# Verify container GPU access
if ! docker exec atlas-backend nvidia-smi; then
    echo "ERROR: GPU not accessible in container"
    exit 1
fi

# Verify llama.cpp GPU support
if ! docker exec atlas-backend python -c "from llama_cpp import llama_supports_gpu_offload; assert llama_supports_gpu_offload()"; then
    echo "ERROR: llama.cpp GPU offload not supported"
    exit 1
fi

echo "✅ GPU verification passed"
```

Add to deployment pipeline:
```yaml
# .github/workflows/deploy.yml
- name: Verify GPU Access
  run: ./backend/scripts/verify_gpu.sh
```

---

### 7. Migrate to Docker Compose v2 Syntax

**Goal**: Use modern Docker Compose features for GPU configuration
- **Timeline**: 2-3 hours
- **Impact**: Better GPU control, future-proof
- **Priority**: P2

**Changes**:

1. Remove `version: "3.8"` from docker-compose.atlas.yml
2. Use modern GPU syntax everywhere (no `runtime:` directive)
3. Test with `docker compose` (v2 CLI, no hyphen)

**Benefits**:
- Better GPU configuration options
- Native support for GPU resource limits
- Modern best practices
- Future compatibility

---

### 8. Document WSL2 GPU Setup Requirements

**Goal**: Prevent team members from facing same GPU issues
- **Timeline**: 1 hour
- **Impact**: Improved onboarding, reduced debugging time
- **Priority**: P2

**Deliverables**:

1. **WSL2_GPU_SETUP.md**:
   - NVIDIA driver installation
   - Docker NVIDIA runtime installation
   - WSL2-specific LD_LIBRARY_PATH configuration
   - Verification steps

2. **TROUBLESHOOTING.md**:
   - Common GPU issues and solutions
   - Runtime verification commands
   - Performance debugging checklist

3. **Update README.md**:
   - Add GPU prerequisites section
   - Link to WSL2 GPU setup guide

---

## Long-Term Priority (P3) - Future Roadmap

### 9. Implement ColBERT Late Interaction

**Goal**: 2-3x retrieval quality improvement
- **Timeline**: 2-3 weeks
- **Impact**: Significant quality boost
- **Trade-off**: 10x index size increase (1GB → 10GB)
- **Priority**: P3

**Research Required**:
- Evaluate `colbert-ai/colbert` library
- Prototype implementation
- Benchmark against BGE embeddings
- Assess storage requirements

---

### 10. Implement HyDE (Hypothetical Document Embeddings)

**Goal**: +20-30% recall on complex queries
- **Timeline**: 1 week
- **Impact**: Better handling of abstract/complex queries
- **Trade-off**: +200-500ms per query (LLM call)
- **Priority**: P3

**Implementation**:
1. LLM generates hypothetical answer to query
2. Embed hypothetical answer (instead of raw query)
3. Search with hypothetical embedding
4. Return actual documents

---

### 11. Migrate to vLLM for Continuous Batching

**Goal**: 3-5x throughput improvement (10 → 30-50 queries/min)
- **Timeline**: 4-6 weeks
- **Impact**: Massive throughput gains
- **Trade-off**: Major architectural change, different API
- **Priority**: P3

**Migration Steps**:
1. Research vLLM integration patterns
2. Prototype vLLM server setup
3. Update backend to use vLLM API
4. Benchmark throughput improvements
5. Gradual migration with A/B testing

---

## Frontend Performance Improvements

### 12. Implement Request Caching

**Goal**: Reduce redundant API calls
- **Timeline**: 2-3 hours
- **Impact**: Better UX, reduced backend load
- **Priority**: P2

**Implementation** (using React Query):
```typescript
// src/services/api.ts
import { useQuery } from '@tanstack/react-query';

export const useDocuments = () => {
  return useQuery({
    queryKey: ['documents'],
    queryFn: api.listDocuments,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000 // 10 minutes
  });
};
```

**Benefits**:
- Settings panel: No refetch on every open
- Document list: Cached for 5 minutes
- Automatic background refetching
- Request deduplication

---

### 13. Add Virtual Scrolling for Message List

**Goal**: Prevent performance degradation with 100+ messages
- **Timeline**: 2-3 hours
- **Impact**: Smooth scrolling with large conversation history
- **Priority**: P3 (nice-to-have)

**Implementation** (using react-window):
```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={messages.length}
  itemSize={120}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <ChatMessage message={messages[index]} />
    </div>
  )}
</FixedSizeList>
```

---

### 14. Implement Code Splitting

**Goal**: Reduce initial bundle size
- **Timeline**: 1-2 hours
- **Impact**: Faster initial page load
- **Priority**: P3

**Implementation**:
```typescript
// Lazy load heavy components
const SettingsPanel = lazy(() => import('./components/Settings/SettingsPanel'));
const DocumentManagement = lazy(() => import('./components/Documents/DocumentManagement'));
const PerformanceDashboard = lazy(() => import('./components/Performance/PerformanceDashboard'));
```

---

## Monitoring & Observability Improvements

### 15. Implement Query Timing Breakdown Logging

**Goal**: Detailed performance visibility
- **Timeline**: 1 hour
- **Impact**: Better debugging, optimization target identification
- **Priority**: P2

**Implementation**:

Add detailed timing logs in `backend/app/core/rag_engine.py`:

```python
timing_breakdown = {
    "query_embedding": 50,      # ms
    "vector_search": 200,       # ms
    "cross_encoder": 150,       # ms
    "bge_reranking": 60,        # ms
    "answer_generation": 500,   # ms
    "confidence_scoring": 100,  # ms
    "post_processing": 50       # ms
}

logger.info(f"Query timing breakdown: {json.dumps(timing_breakdown)}")
```

Export to Prometheus for Grafana visualization.

---

## Priority Matrix

| Priority | Task | Impact | Effort | ROI |
|----------|------|--------|--------|-----|
| P0 | Fix Docker NVIDIA Runtime | 10x speedup | 6-7 min | EXTREME |
| P0 | Fix Speculative Decoding Config | 40% speedup | 10 min | EXTREME |
| P1 | Implement BGE-M3 Embeddings | +15-20% accuracy | 8-12 days | HIGH |
| P1 | Add GPU Monitoring | Proactive detection | 2-4 hours | HIGH |
| P1 | Upgrade Rate Limiting | Production-ready | 1-2 hours | HIGH |
| P2 | GPU CI/CD Verification | Prevent issues | 1-2 hours | MEDIUM |
| P2 | Migrate to Compose v2 | Future-proof | 2-3 hours | MEDIUM |
| P2 | Request Caching (Frontend) | Better UX | 2-3 hours | MEDIUM |
| P2 | Query Timing Logging | Better debugging | 1 hour | MEDIUM |
| P3 | ColBERT Late Interaction | 2-3x quality | 2-3 weeks | LOW |
| P3 | HyDE Embeddings | +20-30% recall | 1 week | LOW |
| P3 | vLLM Migration | 3-5x throughput | 4-6 weeks | LOW |
| P3 | Virtual Scrolling | Smooth UX | 2-3 hours | LOW |
| P3 | Code Splitting | Faster load | 1-2 hours | LOW |

---

## Execution Timeline

### Week 1 (Immediate)
- Day 1: Fix Docker NVIDIA runtime + Speculative decoding config (P0)
- Day 2: Add GPU monitoring to Prometheus/Grafana (P1)
- Day 3: Upgrade rate limiting to Redis (P1)
- Day 4-5: Begin BGE-M3 embeddings implementation (P1)

### Week 2-3 (Short-term)
- Complete BGE-M3 embeddings migration
- Document re-indexing (2-3 hours)
- Validation and A/B testing

### Week 4-6 (Medium-term)
- GPU CI/CD verification (P2)
- Docker Compose v2 migration (P2)
- Frontend request caching (P2)
- WSL2 GPU documentation (P2)

### Month 2-3 (Long-term)
- ColBERT research and prototyping (P3)
- HyDE implementation (P3)
- Virtual scrolling and code splitting (P3)

### Month 4-6 (Future)
- vLLM continuous batching migration (P3)
- Advanced quantization (Q3_K_M models)
- Agentic RAG for complex queries

---

## Success Metrics

**Performance Metrics**:
- Query latency: Target 1,110ms (67% faster than baseline)
- TTFT: Target 300ms (after speculative decoding)
- Throughput: Target 80 queries/min (up from 54)
- GPU utilization: 70-90% sustained

**Quality Metrics**:
- Recall@3: Target 0.82 (up from 0.70)
- Answer quality: Maintain 8.5/10
- Cache hit rate: Maintain 60-85%

**Infrastructure Metrics**:
- GPU runtime uptime: 100% (no CPU fallback)
- Container startup time: <30 seconds
- Deployment success rate: 100%
- Zero GPU-related incidents

---

## Conclusion

Apollo v4.1's infrastructure improvements follow a clear priority order: **Fix GPU acceleration FIRST** (10x gain in 6-7 minutes), then unlock remaining optimizations (Quick Wins 8-9). The roadmap balances quick wins with strategic long-term investments, ensuring continuous performance improvement while maintaining system quality and reliability.

**Next Action**: Execute P0 fixes immediately for 10x performance recovery.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-26
**Maintainer**: MENDICANT_BIAS
