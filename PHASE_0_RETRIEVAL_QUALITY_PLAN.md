# Phase 0: Retrieval Quality Optimization - Master Plan

**Version**: 1.0
**Date**: 2025-10-12
**Status**: In Progress
**Goal**: Achieve 95% minimum (99% stretch) accuracy on retrieval and answer generation

---

## 🎯 Executive Summary

### Mission
Transform the Tactical RAG system from a C+ accuracy system to a 95-99% accurate, production-ready RAG system through comprehensive retrieval quality optimization.

### Success Criteria
- ✅ **95% minimum accuracy** on verified test suite (20-30 diverse queries)
- 🎯 **99% stretch goal accuracy** through robust testing
- ✅ **Simple Mode**: Fast + accurate (optimized dense retrieval)
- ✅ **Adaptive Mode**: Maximum accuracy (hybrid + reranking)
- ✅ **No performance regressions**: Speed stays ≤25% slower
- ✅ **Fully documented**: All changes tracked and explained

### Current State
- **Grade**: C+ (inaccurate retrievals, keyword matching issues)
- **Example Failure**: "what about to the colors" → Returns beard info instead of flag ceremony
- **Root Causes**:
  - Keyword matching without semantic understanding
  - No military terminology handling
  - No reranking or relevance scoring
  - Poor query preprocessing

### Target State
- **Grade**: S+ (95-99% accuracy)
- **Robust retrieval**: Military terminology understood
- **Smart ranking**: Most relevant docs prioritized
- **Both modes optimized**: Simple (fast) + Adaptive (accurate)

---

## 📚 Context & Background

### System Architecture
```
User Query
    ↓
Query Preprocessing (NEEDS IMPROVEMENT)
    ↓
Embedding Generation (NEEDS OPTIMIZATION)
    ↓
Retrieval Layer:
    ├─ Simple Mode: Dense-only (ChromaDB)
    └─ Adaptive Mode: Hybrid (BM25 + Dense) + Reranking (NEEDS WORK)
    ↓
LLM Answer Generation (Currently accurate, just slow)
    ↓
Response to User
```

### Documents
- **Primary**: `dafi36-2903.pdf` (AFI 36-2903: Dress and Appearance)
- **Indexed**: 1,008 chunks in ChromaDB
- **Coverage**: Uniform regulations, grooming standards, ceremonies, exceptions

### Current Performance Metrics
- **Simple Mode**: ~22s response time, unknown accuracy
- **Adaptive Mode**: ~30s response time, unknown accuracy
- **Cache Hit**: 1.9ms (S+ when cached)
- **Bottlenecks**: LLM (62%), Retrieval (38%)

---

## 🏗️ Three-Stage Execution Plan

### Stage 1: Assessment & Baseline (Sequential - 2-3 hours)
**Objective**: Understand current accuracy and failure modes

**Agent 1: Test Suite Creator**
- Generate 20-30 diverse test queries
- Create ground truth answers
- Categorize by difficulty/type

**Agent 2: Baseline Accuracy Tester**
- Run all queries through system
- Measure accuracy, precision, recall
- Generate baseline metrics

**Agent 3: Failure Analyzer**
- Deep dive into failures
- Categorize failure types
- Identify root causes

**Outputs**:
- `tests/retrieval_test_suite.json`
- `logs/phase0_baseline_accuracy.json`
- `logs/phase0_failure_analysis.md`

---

### Stage 2: Parallel Optimization (4-6 hours)
**Objective**: Optimize both modes simultaneously for maximum accuracy

#### 🔵 Agent 4: Simple Mode Optimizer (Parallel Track A)
**Mission**: Optimize dense-only retrieval for speed + accuracy

**Tasks**:
1. **Query Preprocessing**
   - Military terminology expansion
   - Acronym handling (AFI, DAFI, etc.)
   - Synonym expansion
   - Query reformulation

2. **Embedding Optimization**
   - Test different embedding models
   - Optimize embedding prompts
   - Consider fine-tuning embeddings

3. **Retrieval Parameter Tuning**
   - Optimize k (retrieval count)
   - Tune similarity thresholds
   - Test different distance metrics
   - Optimize score normalization

4. **Continuous Validation**
   - Run test suite after each change
   - Track accuracy improvements
   - A/B test configurations

**Success Criteria**:
- ≥95% accuracy on test suite
- Response time ≤25s (no major regression)
- Better than baseline on all failure cases

**Output**:
- `backend/app/core/optimized_simple_retrieval.py`
- `logs/simple_mode_optimization_report.md`

---

#### 🟢 Agent 5: Adaptive Mode Optimizer (Parallel Track B)
**Mission**: Maximize accuracy through hybrid retrieval + reranking

**Tasks**:
1. **Hybrid Retrieval Optimization**
   - Optimize BM25 + Dense fusion weights
   - Test RRF (Reciprocal Rank Fusion)
   - Tune alpha parameter (dense vs sparse balance)
   - Implement query expansion

2. **Reranking Implementation**
   - Implement cross-encoder reranking
   - Test multiple reranking models:
     - BAAI/bge-reranker-large
     - cross-encoder/ms-marco-MiniLM-L-12-v2
   - Optimize reranking threshold
   - Balance speed vs accuracy

3. **Context Enhancement**
   - Improve conversation memory integration
   - Query expansion from context
   - Dynamic context window sizing
   - Multi-hop reasoning support

4. **Advanced Techniques**
   - Query decomposition for complex questions
   - Entity extraction and linking
   - Semantic chunking optimization
   - Metadata filtering

**Success Criteria**:
- ≥95% accuracy on test suite (goal: 99%)
- Response time ≤40s (acceptable slowdown for accuracy)
- Perfect score on complex/multi-hop queries

**Output**:
- `backend/app/core/optimized_adaptive_retrieval.py`
- `logs/adaptive_mode_optimization_report.md`

---

### Stage 3: Validation & Integration (Sequential - 1-2 hours)
**Objective**: Verify improvements and prepare for Phase 1

**Agent 6: Comprehensive Validator**
- Run full test suite on both optimized modes
- Calculate final accuracy metrics
- Compare simple vs adaptive tradeoffs
- Verify 95%+ threshold met
- If not → Iterate with Agents 4 & 5

**Agent 7: Performance Regression Tester**
- Run timing benchmarks
- Compare against baseline
- Ensure no major slowdowns
- Profile any new bottlenecks

**Agent 8: Documentation & Handoff**
- Document all changes
- Create configuration guide
- Generate handoff report for Phase 1
- Update architecture diagrams

**Outputs**:
- `logs/phase0_final_validation_report.md`
- `logs/phase0_performance_report.md`
- `PHASE_0_COMPLETION_REPORT.md`

---

## 🧪 Testing Framework

### Test Suite Structure
```json
{
  "test_id": "001",
  "category": "direct_fact",
  "difficulty": "easy",
  "query": "What are the beard regulations?",
  "ground_truth": {
    "answer": "Beards only authorized for medical/religious reasons, max 1/4 inch length",
    "source_pages": [30, 31],
    "key_excerpts": ["beards are only authorized", "not exceed 1/4-inch"]
  },
  "tags": ["grooming", "facial_hair", "regulations"]
}
```

### Test Categories
1. **Direct Facts** (30%)
   - Simple lookups: "What is X?"
   - Single-source answers
   - Clear regulations

2. **Military Terminology** (25%)
   - "the colors", ranks, ceremonies
   - Acronyms: AFI, DAFI, OCP, ABU
   - Technical military terms

3. **Complex Queries** (20%)
   - Multi-hop reasoning
   - Combining multiple sections
   - Exception handling

4. **Edge Cases** (15%)
   - Religious accommodations
   - Medical waivers
   - Special circumstances

5. **Negative Cases** (10%)
   - Questions with no answer in docs
   - Out of scope queries
   - Ambiguous questions

### Evaluation Metrics

#### Accuracy Metrics
- **Exact Match (EM)**: Answer exactly matches ground truth
- **Semantic Similarity (SS)**: Cosine similarity ≥ 0.85 with ground truth
- **Source Precision**: % of retrieved docs that are relevant
- **Source Recall**: % of relevant docs retrieved
- **Answer Relevance**: LLM-as-judge scoring (1-10 scale)

#### Retrieval Metrics
- **Precision@k**: Relevant docs in top-k / k
- **Recall@k**: Relevant docs in top-k / total relevant
- **MRR (Mean Reciprocal Rank)**: 1 / rank of first relevant doc
- **NDCG (Normalized Discounted Cumulative Gain)**: Relevance-weighted ranking quality

#### Quality Metrics
- **Hallucination Rate**: % of responses citing non-existent info
- **Source Attribution**: % of answers with correct source citations
- **Confidence Calibration**: Accuracy vs stated confidence

---

## 🔬 Root Cause Analysis Framework

### Failure Taxonomy
1. **Retrieval Failures**
   - Wrong documents retrieved (precision issue)
   - Right documents missed (recall issue)
   - Poor ranking (relevance issue)

2. **Query Understanding Failures**
   - Keyword matching without semantics
   - Missing terminology expansion
   - Context not incorporated

3. **Answer Generation Failures**
   - Hallucinations (making up info)
   - Source misattribution
   - Incomplete answers

4. **System Failures**
   - Embedding model limitations
   - Chunking strategy issues
   - Index quality problems

### Diagnostic Process
For each failure:
1. **What happened?** (Observed behavior)
2. **What should have happened?** (Expected behavior)
3. **Why did it fail?** (Root cause analysis)
4. **How to fix?** (Proposed solution)
5. **How to prevent?** (Systemic improvement)

---

## 🛠️ Implementation Guidelines

### Query Preprocessing Best Practices
```python
# Military terminology expansion
MILITARY_TERMS = {
    "the colors": ["flag ceremony", "national anthem", "flag presentation"],
    "salute to the colors": ["flag salute", "national anthem salute"],
    "OCP": ["Operational Camouflage Pattern", "uniform"],
    "ABU": ["Airman Battle Uniform"],
    # ... expand as needed
}

# Acronym expansion
def expand_acronyms(query: str) -> str:
    # Expand common military acronyms
    pass

# Synonym expansion
def expand_synonyms(query: str) -> str:
    # Add relevant synonyms
    pass
```

### Embedding Optimization
```python
# Test different embedding models:
CANDIDATE_MODELS = [
    "sentence-transformers/all-mpnet-base-v2",  # Current
    "BAAI/bge-large-en-v1.5",  # Better quality
    "sentence-transformers/all-MiniLM-L12-v2",  # Faster
]

# Optimize embedding prompts
EMBEDDING_PREFIX = "Represent this military regulation for semantic search: "
```

### Hybrid Retrieval Tuning
```python
# Test different fusion strategies
def reciprocal_rank_fusion(dense_results, sparse_results, k=60):
    # RRF formula: score = Σ 1/(k + rank_i)
    pass

def weighted_fusion(dense_results, sparse_results, alpha=0.7):
    # Weighted: score = alpha * dense_score + (1-alpha) * sparse_score
    pass

# Test alpha values: 0.3, 0.5, 0.7, 0.9
```

### Reranking Implementation
```python
# Cross-encoder reranking
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('BAAI/bge-reranker-large')

def rerank_documents(query: str, documents: List[Doc], top_k: int = 5):
    # Score all query-doc pairs
    pairs = [(query, doc.content) for doc in documents]
    scores = reranker.predict(pairs)

    # Sort by score and return top_k
    ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]
```

---

## 📊 Measurement & Tracking

### Continuous Metrics Dashboard
Track in real-time during optimization:
- Current accuracy (overall, by category)
- Improvement over baseline (delta %)
- Response time (mean, p50, p95, p99)
- Retrieval quality (precision, recall, MRR)

### Experiment Tracking
For each experiment:
```json
{
  "experiment_id": "exp_001_query_preprocessing",
  "timestamp": "2025-10-12T15:30:00Z",
  "changes": ["Added military terminology expansion"],
  "baseline_accuracy": 0.72,
  "new_accuracy": 0.84,
  "improvement": "+12%",
  "response_time_delta": "+0.3s",
  "decision": "ACCEPT - significant accuracy gain",
  "notes": "Worth slight speed tradeoff"
}
```

### A/B Testing Framework
```python
def ab_test(config_a, config_b, test_suite):
    """
    Run A/B test comparing two configurations.
    Use statistical significance testing (t-test, p<0.05)
    """
    results_a = run_tests(config_a, test_suite)
    results_b = run_tests(config_b, test_suite)

    # Statistical comparison
    is_significant = ttest(results_a, results_b).pvalue < 0.05

    return {
        "winner": config_b if results_b.mean > results_a.mean else config_a,
        "improvement": abs(results_b.mean - results_a.mean),
        "significant": is_significant
    }
```

---

## 🤖 Agent Coordination Protocol

### Agent Communication
- **Shared Knowledge Base**: All agents read/write to `logs/phase0_shared_state.json`
- **Progress Updates**: Every 30 minutes or after major milestone
- **Blocking Issues**: Immediate escalation with `BLOCKED:` prefix
- **Completion Signal**: Agents signal completion with `DONE:` prefix

### Parallel Agent Synchronization
```python
# Shared state structure
{
  "timestamp": "2025-10-12T15:30:00Z",
  "stage": "2_optimization",
  "agent_4_status": "running",
  "agent_4_progress": "65% - Testing reranking model",
  "agent_4_accuracy": 0.89,
  "agent_5_status": "running",
  "agent_5_progress": "80% - Final validation",
  "agent_5_accuracy": 0.94,
  "best_simple_config": {...},
  "best_adaptive_config": {...},
  "blockers": []
}
```

### Decision Making
- **Autonomous**: Agents can make optimization decisions
- **Escalation**: If accuracy drops >5%, escalate
- **Rollback**: Keep last-known-good configuration
- **Documentation**: All decisions logged with rationale

---

## 🎓 Learning & Iteration

### Feedback Loops
1. **Rapid Iteration**: Test → Measure → Improve → Repeat
2. **Incremental Changes**: One variable at a time
3. **Baseline Comparison**: Always compare to baseline
4. **Statistical Rigor**: Use t-tests for significance

### Best Practices
- **Start Simple**: Basic improvements first, complex later
- **Measure Everything**: If not measured, not improved
- **Document Failures**: Failed experiments teach too
- **Version Control**: Git commit after each successful improvement

### Anti-Patterns to Avoid
- ❌ Optimizing without measuring
- ❌ Making multiple changes at once
- ❌ Ignoring edge cases
- ❌ Overfitting to test set
- ❌ Sacrificing accuracy for speed (in Phase 0)

---

## 📈 Success Metrics & KPIs

### Phase 0 Completion Criteria
- [ ] Test suite created (20-30 queries, diverse)
- [ ] Baseline accuracy measured (<80% expected)
- [ ] Simple mode optimized (≥95% accuracy, ≤25s response)
- [ ] Adaptive mode optimized (≥95% accuracy, goal 99%)
- [ ] All failure cases resolved
- [ ] Performance regression test passed (≤25% slowdown)
- [ ] Documentation complete
- [ ] Handoff report generated for Phase 1

### Key Performance Indicators
| Metric | Baseline | Minimum Target | Stretch Goal |
|--------|----------|----------------|--------------|
| Overall Accuracy | TBD (est. <80%) | 95% | 99% |
| Direct Facts | TBD | 98% | 100% |
| Military Terms | TBD (poor) | 95% | 99% |
| Complex Queries | TBD (poor) | 90% | 95% |
| Edge Cases | TBD (poor) | 85% | 90% |
| Negative Cases | TBD | 90% | 95% |
| Simple Mode Time | ~22s | ≤25s | ≤20s |
| Adaptive Mode Time | ~30s | ≤40s | ≤35s |
| Precision@5 | TBD | 0.90 | 0.95 |
| Recall@10 | TBD | 0.85 | 0.90 |

---

## 🚀 Execution Checklist

### Pre-Flight (Before Starting)
- [ ] Review this document thoroughly
- [ ] Ensure docker-compose services running
- [ ] Verify ChromaDB index loaded (1,008 chunks)
- [ ] Check LLM availability (Ollama llama3.1:8b)
- [ ] Create logs/ and tests/ directories
- [ ] Install any needed dependencies (langgraph, etc.)

### Stage 1: Assessment
- [ ] Agent 1: Test suite created ✓
- [ ] Agent 2: Baseline accuracy measured ✓
- [ ] Agent 3: Failure analysis complete ✓
- [ ] Review findings before proceeding to Stage 2

### Stage 2: Optimization
- [ ] Agent 4: Simple mode optimized ✓
- [ ] Agent 5: Adaptive mode optimized ✓
- [ ] Both agents sync and compare results ✓
- [ ] Select best configurations ✓

### Stage 3: Validation
- [ ] Agent 6: Comprehensive validation ✓
- [ ] Agent 7: Performance regression test ✓
- [ ] Agent 8: Documentation complete ✓
- [ ] Phase 0 completion report ✓

### Post-Flight (After Completion)
- [ ] Commit all changes to git
- [ ] Archive baseline for comparison
- [ ] Update S_PLUS_OPTIMIZATION_REPORT.md
- [ ] Brief stakeholder on results
- [ ] Prepare for Phase 1 kickoff

---

## 📝 Deliverables

### Required Outputs
1. **Test Suite**: `tests/retrieval_test_suite.json`
2. **Baseline Report**: `logs/phase0_baseline_accuracy.json`
3. **Failure Analysis**: `logs/phase0_failure_analysis.md`
4. **Simple Mode Code**: `backend/app/core/optimized_simple_retrieval.py`
5. **Adaptive Mode Code**: `backend/app/core/optimized_adaptive_retrieval.py`
6. **Validation Report**: `logs/phase0_final_validation_report.md`
7. **Performance Report**: `logs/phase0_performance_report.md`
8. **Completion Report**: `PHASE_0_COMPLETION_REPORT.md`

### Optional Outputs
- Experiment logs (all A/B tests)
- Configuration comparison matrices
- Visualization of improvements (charts, graphs)
- Failure case studies (detailed analysis)

---

## 🎯 Phase 1 Handoff

### What Phase 1 Will Receive
- ✅ Highly accurate retrieval system (95-99%)
- ✅ Optimized configurations for both modes
- ✅ Comprehensive test suite for regression testing
- ✅ Detailed documentation of all changes
- ✅ Performance baseline for speed optimization

### Phase 1 Focus Areas
With accuracy locked in, Phase 1 will optimize speed:
1. vLLM Migration (10s → 2s LLM time)
2. Embedding Cache (5s saved on retrieval)
3. Frontend Streaming (perceived latency)
4. Query Normalization (cache hit rate)

### Transition Criteria
Phase 0 → Phase 1 transition when:
- ✅ 95% accuracy achieved and verified
- ✅ All tests passing
- ✅ No critical bugs
- ✅ Documentation complete
- ✅ Code reviewed and approved

---

## 🔗 References

### Key Files
- `backend/app/core/rag_engine.py` - Main RAG engine
- `backend/app/core/strategies.py` - Retrieval strategies
- `backend/app/core/cache_manager.py` - Redis caching
- `backend/app/core/answer_generator.py` - LLM generation
- `backend/app/utils/timing.py` - Performance instrumentation

### External Resources
- [Retrieval-Augmented Generation Survey](https://arxiv.org/abs/2312.10997)
- [Dense Passage Retrieval](https://arxiv.org/abs/2004.04906)
- [Reranking for RAG Systems](https://arxiv.org/abs/2309.15088)
- [LangChain RAG Best Practices](https://python.langchain.com/docs/use_cases/question_answering/)

### Tools & Libraries
- ChromaDB: Vector database
- Sentence Transformers: Embedding models
- Cross-Encoder: Reranking models
- LangGraph: Agent orchestration
- Redis: Caching layer

---

## 💡 Tips for Autonomous Agents

### For Test Suite Creator (Agent 1)
- Analyze document structure carefully
- Cover all major topics (grooming, uniforms, ceremonies)
- Include positive and negative cases
- Vary difficulty levels
- Create clear, unambiguous ground truth

### For Simple Mode Optimizer (Agent 4)
- Start with low-hanging fruit (query preprocessing)
- Test one change at a time
- Keep detailed logs of all experiments
- Don't overcomplicate - simple often wins
- Balance speed and accuracy

### For Adaptive Mode Optimizer (Agent 5)
- Complex is OK here - accuracy is priority
- Reranking is powerful - invest time here
- Hybrid retrieval needs careful tuning
- Test multiple reranking models
- Document tradeoffs clearly

### For All Agents
- **Measure before optimizing**: Always establish baseline
- **Iterate rapidly**: Small changes, fast feedback
- **Document everything**: Future you will thank you
- **Test thoroughly**: Edge cases matter
- **Communicate clearly**: Update shared state often

---

## 🎬 Conclusion

Phase 0 is the foundation for everything that follows. A fast but inaccurate system is useless. A slow but accurate system can be optimized. This phase ensures we build on solid ground.

**Remember**:
- **Quality over speed** (in this phase)
- **Measure everything**
- **Iterate rapidly**
- **Document thoroughly**
- **Test comprehensively**

**Goal**: 95% minimum accuracy, 99% stretch goal. Make it happen! 🚀

---

**Last Updated**: 2025-10-12
**Next Review**: After Stage 1 completion
**Owner**: Claude Code with autonomous agent team
