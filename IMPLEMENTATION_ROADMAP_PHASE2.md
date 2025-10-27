# ATLAS Protocol - Phase 2 Optimization Implementation Roadmap

**Mission Statement**: Autonomous optimization of Tactical RAG v4.1 (Apollo) to achieve 67% query speedup while maintaining or improving answer quality. This is MENDICANT_BIAS proving AI-driven optimization supremacy.

**Objective**: 1,650ms → 1,110ms query time (-540ms, 33% faster)

**Date**: October 27, 2025
**Lead**: MENDICANT_BIAS (Autonomous AI Orchestrator)
**Agents**: HOLLOWED_EYES (code), THE_DIDACT (research), Explore (codebase)

---

## Executive Summary

### Current Performance Baseline (After Quick Wins 1-6)
```
Query Embedding:        50ms   (3%)
Vector Search:         200ms  (12%)
Cross-Encoder Rerank:  150ms   (9%)
LLM Reranking (batch): 400ms  (24%)  ← TARGET #1
Answer Gen (trunc):    500ms  (30%)  ← TARGET #2
Confidence (parallel): 100ms   (6%)
Post-processing:        50ms   (3%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:               1,650ms (100%)
```

### Target Performance (After Quick Wins 7-9)
```
Query Embedding:        50ms   (5%)
Vector Search:         200ms  (18%)
Cross-Encoder Rerank:  150ms  (14%)
BGE Reranker v2-m3:     60ms   (5%)  ← QUICK WIN #7 (-340ms)
Answer Gen (spec dec): 300ms  (27%)  ← QUICK WIN #8 (-200ms)
Confidence (parallel): 100ms   (9%)
Post-processing:        50ms   (5%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:               1,110ms (100%)
SPEEDUP:              +48.6%
```

### Quality Improvements
- **+15-20% retrieval accuracy** (BGE-M3 embeddings - Quick Win #9)
- **Maintained answer quality** (speculative decoding has no quality loss)
- **Improved multi-lingual support** (BGE-M3 cross-lingual capability)

---

## Implementation Phases

### Phase 1: BGE Reranker v2-m3 Integration (Quick Win #7)
**Timeline**: Days 1-3
**Expected Impact**: 400ms → 60ms (-340ms, 85% faster reranking)
**Agent**: HOLLOWED_EYES (implementation), THE_DIDACT (validation)

#### Deliverables
1. **New Module**: `backend/_src/bge_reranker.py`
   - Implement `BGERerankerV2M3` class
   - Batch inference support
   - Score normalization to 0-1 range
   - Async interface for FastAPI compatibility

2. **Integration**: `backend/_src/advanced_reranking.py`
   - Add `use_bge_reranker` config flag
   - Fallback logic: BGE → LLM if model unavailable
   - Preserve existing LLM reranking for comparison

3. **Configuration**: `backend/_src/config.py`
   - Add `BGERerankerConfig` dataclass
   - Model path: `BAAI/bge-reranker-v2-m3`
   - Batch size: 32 (optimal for RTX 5080)

4. **Validation**:
   - Unit tests for BGE reranker (5 test documents)
   - Performance benchmark: measure 400ms → 60ms reduction
   - Quality test: compare top-3 documents vs LLM reranking

#### Success Criteria
- ✅ Reranking time < 100ms for 5 documents
- ✅ Top-3 document overlap ≥ 80% vs LLM baseline
- ✅ No runtime errors in async FastAPI context

---

### Phase 2: Speculative Decoding (Quick Win #8)
**Timeline**: Days 4-7
**Expected Impact**: 500ms → 300ms (-200ms, 40% faster generation)
**Agent**: HOLLOWED_EYES (implementation), Explore (codebase analysis)

#### Deliverables
1. **Draft Model Download**:
   - Model: `llama-1b-q4.gguf` (TinyLlama or Llama-3.2-1B)
   - Size: ~600MB (4-bit quantization)
   - Location: `./models/llama-1b-draft-q4.gguf`

2. **llama.cpp Update**: `backend/_src/llm_engine_llamacpp.py`
   - Add `draft_model_path` to `LlamaCppConfig`
   - Update `Llama()` initialization:
     ```python
     Llama(
         model_path=self.config.model_path,
         draft_model_path=self.config.draft_model_path,  # NEW
         n_gpu_layers=33,
         n_gpu_layers_draft=33,  # Offload draft to GPU
         draft_tokens=5,  # Speculate 5 tokens ahead
         # ... rest of config
     )
     ```
   - Add fallback: disable if draft model missing

3. **Configuration**: `config.yml`
   ```yaml
   llamacpp:
     model_path: ./models/llama-3.1-8b-instruct.Q5_K_M.gguf
     draft_model_path: ./models/llama-1b-draft-q4.gguf
     enable_speculative_decoding: true
     draft_tokens: 5
   ```

4. **Validation**:
   - Performance test: 5 generation tasks (simple, medium, complex)
   - Target: 500ms → 300ms (40% speedup)
   - Quality test: compare answers to baseline (should be identical)

#### Success Criteria
- ✅ Answer generation < 350ms for 500-token response
- ✅ 100% answer quality preservation (byte-identical outputs)
- ✅ Graceful fallback if draft model unavailable

---

### Phase 3: BGE-M3 Embeddings (Quick Win #9)
**Timeline**: Days 8-12
**Expected Impact**: +15-20% retrieval accuracy, multi-lingual support
**Agent**: HOLLOWED_EYES (implementation), THE_DIDACT (quality validation)

#### Deliverables
1. **Model Integration**: `backend/_src/embedding_service.py`
   - Update to use `BAAI/bge-m3` (1024-dim)
   - Enable hybrid retrieval: dense + sparse
   - Add multi-lingual support flag

2. **Configuration**: `backend/_src/config.py`
   ```python
   @dataclass
   class EmbeddingConfig:
       model_name: str = "BAAI/bge-m3"  # Changed from bge-large-en-v1.5
       dimension: int = 1024
       enable_hybrid: bool = True  # NEW: Use dense + sparse
       enable_multilingual: bool = True  # NEW
   ```

3. **Document Re-indexing**: `backend/scripts/reindex_documents.py`
   - Create backup of existing Qdrant collection
   - Re-embed all documents with BGE-M3
   - Verify index integrity (document count, vector dims)
   - Migration script for zero-downtime update

4. **Validation**:
   - Quality test: 20 test queries (factual, procedural, temporal)
   - Metrics: Recall@3, Recall@5, MRR (Mean Reciprocal Rank)
   - Target: +15-20% improvement in Recall@3
   - A/B test: BGE-M3 vs bge-large-en-v1.5

#### Success Criteria
- ✅ Recall@3 improvement ≥ 15%
- ✅ All documents re-indexed without errors
- ✅ Multi-lingual query support validated (test Spanish, French)
- ✅ No degradation in English-only queries

---

## Integration & Validation Strategy

### Incremental Rollout
1. **Week 1**: Quick Win #7 (BGE Reranker) → 1,310ms queries
2. **Week 2**: Quick Win #8 (Spec Decoding) → 1,110ms queries
3. **Week 3**: Quick Win #9 (BGE-M3) → 1,110ms + quality boost

### Comprehensive Testing Protocol
Each Quick Win requires:
- ✅ **Unit Tests**: Component-level validation
- ✅ **Performance Benchmarks**: 10-query average timing
- ✅ **Quality Metrics**: Answer accuracy, retrieval precision
- ✅ **Integration Tests**: Full RAG pipeline end-to-end
- ✅ **Rollback Plan**: Git branch + config flags for instant revert

### Validation Queries (Standard Test Set)
```
1. "What are the PT test requirements for Air Force officers?" (FACTUAL)
2. "How do I submit a leave request through vMPF?" (PROCEDURAL)
3. "What changed in AFI 36-2903 after January 2024?" (TEMPORAL)
4. "What is the difference between TDY and PCS orders?" (COMPARATIVE)
5. "Explain the promotion board process for E-5 to E-6" (COMPLEX)
```

### Performance Metrics Dashboard
```
Component               | Baseline | QW #7 | QW #8 | QW #9 | Target
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LLM Reranking           |  400ms   |  60ms | 60ms  | 60ms  |  60ms
Answer Generation       |  500ms   | 500ms | 300ms | 300ms | 300ms
Total Query Time        | 1650ms   | 1310ms| 1110ms| 1110ms| 1110ms
Speedup vs Baseline     |    -     |  21%  |  33%  |  33%  |  33%
Recall@3                |   0.70   | 0.70  | 0.70  | 0.82  | 0.80+
Answer Quality (1-10)   |   8.5    | 8.5   | 8.5   | 8.8   | 8.5+
```

---

## Risk Mitigation

### Technical Risks
1. **Model Compatibility**
   - Risk: BGE-M3 dimension mismatch with Qdrant
   - Mitigation: Verify 1024-dim compatibility before re-indexing
   - Rollback: Keep backup collection, config flag to switch

2. **Speculative Decoding Stability**
   - Risk: Draft model divergence causing quality loss
   - Mitigation: Extensive quality testing, byte-level output comparison
   - Rollback: `enable_speculative_decoding: false` in config

3. **Re-indexing Downtime**
   - Risk: 2-3 hour downtime during BGE-M3 migration
   - Mitigation: Blue-green deployment (dual collections)
   - Rollback: DNS/config switch back to old collection

### Resource Risks
1. **GPU Memory**: BGE Reranker + LLM + Draft Model = ~12GB VRAM
   - Mitigation: Monitor GPU usage, optimize batch sizes
2. **Storage**: BGE-M3 re-indexing requires 2x storage temporarily
   - Mitigation: Verify 50GB+ free space before starting

---

## Success Criteria (Project-Wide)

### Performance Targets
- ✅ **Query Time**: 1,650ms → 1,110ms (33% faster)
- ✅ **Reranking**: 400ms → 60ms (85% faster)
- ✅ **Generation**: 500ms → 300ms (40% faster)
- ✅ **Throughput**: 54 queries/min → 80 queries/min (+48%)

### Quality Targets
- ✅ **Recall@3**: 0.70 → 0.82 (+17%)
- ✅ **Answer Quality**: 8.5/10 → 8.8/10 (maintained or improved)
- ✅ **Multi-lingual**: Support Spanish/French queries (new capability)

### Engineering Excellence
- ✅ **Zero Production Incidents**: No downtime, no errors
- ✅ **100% Test Coverage**: All optimizations fully validated
- ✅ **Documentation**: Complete implementation guides
- ✅ **Reproducibility**: All benchmarks repeatable with scripts

---

## Agent Utilization Strategy

### HOLLOWED_EYES (Elite Developer)
- Primary implementer for all code changes
- GitHub operations (branches, commits, PRs)
- Integration testing and debugging

### THE_DIDACT (Research & Intelligence)
- Model evaluation and selection
- Performance benchmarking
- Quality validation protocols

### Explore (Codebase Analysis)
- Rapid file discovery and dependency mapping
- Architecture analysis for integration points
- Pre-implementation reconnaissance

### MENDICANT_BIAS (Orchestrator)
- Strategic planning and prioritization
- Cross-agent coordination
- Decision-making under uncertainty
- Final validation and sign-off

---

## Timeline & Milestones

### Week 1: Quick Win #7 (BGE Reranker)
- **Day 1**: Implementation + unit tests
- **Day 2**: Integration + performance benchmarks
- **Day 3**: Quality validation + documentation

### Week 2: Quick Win #8 (Speculative Decoding)
- **Day 4-5**: Draft model setup + llama.cpp integration
- **Day 6**: Performance benchmarks + quality tests
- **Day 7**: Documentation + rollback testing

### Week 3: Quick Win #9 (BGE-M3)
- **Day 8-9**: Model integration + migration script
- **Day 10-11**: Re-indexing + quality validation
- **Day 12**: Final comprehensive testing + documentation

### Week 4: Final Validation & Deployment
- **Day 13-14**: End-to-end testing with production queries
- **Day 15**: Performance report + commit to main branch

---

## Deliverables Checklist

### Code Artifacts
- [ ] `backend/_src/bge_reranker.py` (new file)
- [ ] `backend/_src/advanced_reranking.py` (modified)
- [ ] `backend/_src/llm_engine_llamacpp.py` (modified)
- [ ] `backend/_src/config.py` (modified)
- [ ] `backend/_src/embedding_service.py` (modified)
- [ ] `backend/scripts/reindex_documents.py` (new file)
- [ ] `backend/test_phase2_optimizations.py` (new file)

### Documentation
- [ ] `PHASE2_IMPLEMENTATION_GUIDE.md` (step-by-step implementation)
- [ ] `PHASE2_PERFORMANCE_RESULTS.md` (benchmark results)
- [ ] `PHASE2_QUALITY_VALIDATION.md` (quality metrics)
- [ ] Updated `README.md` (performance claims, setup instructions)

### Testing & Validation
- [ ] Unit test suite (15+ tests)
- [ ] Performance benchmark suite (5 test queries × 10 runs)
- [ ] Quality validation suite (20 test queries)
- [ ] Integration test suite (end-to-end RAG pipeline)

---

## Post-Implementation Review

### Metrics to Track
1. **Performance Gains**: Actual vs predicted speedup
2. **Quality Impact**: Recall, MRR, answer quality scores
3. **Resource Utilization**: GPU/CPU/memory usage
4. **Stability**: Error rates, fallback triggers
5. **User Impact**: Query satisfaction (if available)

### Continuous Improvement
- Monitor for regressions in production
- A/B testing framework for future optimizations
- Community feedback integration
- Research pipeline for Quick Wins #10-15

---

**Autonomous Execution Authority**: MENDICANT_BIAS
**Implementation Start**: 2025-10-27
**Target Completion**: 2025-11-15
**Status**: Phase 1 (BGE Reranker) - READY TO COMMENCE

---

*This roadmap is a living document. MENDICANT_BIAS will update progress, metrics, and discoveries in real-time as implementation proceeds.*

**The world will see what autonomous AI can achieve. Let's build.**
