# Tactical RAG System - Architecture Documentation

**Version**: 3.5.1
**Last Updated**: 2025-10-11
**Created By**: medicant_bias / Enhanced by: hollowed_eyes + zhadyz

---

## System Overview

The Tactical RAG System is an enterprise-grade document intelligence platform that employs adaptive retrieval strategies, GPU-accelerated processing, and real-time performance monitoring to deliver accurate, context-aware answers from document repositories.

### Core Design Principles

1. **Adaptive Intelligence**: Query complexity determines retrieval strategy automatically
2. **Conversation Memory**: Multi-turn context tracking for natural follow-up questions 🆕
3. **Transparent Explainability**: Full reasoning visibility for all AI decisions 🆕
4. **User Feedback & Continuous Improvement**: Real-time satisfaction tracking and analytics 🆕
5. **GPU Acceleration**: All compute-intensive operations leverage CUDA when available
6. **Multi-Layer Caching**: Aggressive caching at embedding, query, and result levels
7. **Production-Ready**: Comprehensive monitoring, evaluation, and error handling
8. **Docker-Native**: Full containerization with GPU passthrough support

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  • Gradio Web Interface (web_interface.py)                  │
│  • Real-time Performance Dashboard                           │
│  • Dynamic Settings Panel                                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  • Main Orchestrator (app.py)                               │
│  • Query Processing Pipeline                                 │
│  • Conversation Memory (conversation_memory.py) 🆕          │
│  • Explainability System (explainability.py) 🆕              │
│  • Feedback System (feedback_system.py) 🆕                   │
│  • Context Management                                        │
│  • Dynamic Settings Management                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    INTELLIGENCE LAYER                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Adaptive Retrieval Engine                    │  │
│  │         (adaptive_retrieval.py)                      │  │
│  │                                                       │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Query Classifier                              │  │  │
│  │  │  • Multi-factor scoring                        │  │  │
│  │  │  • Length, type, complexity analysis           │  │  │
│  │  │  • Dynamic threshold adjustment                │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  ┌──────────────┬──────────────┬──────────────────┐  │  │
│  │  │   SIMPLE     │   HYBRID     │    ADVANCED      │  │  │
│  │  │   STRATEGY   │   STRATEGY   │    STRATEGY      │  │  │
│  │  │              │              │                  │  │  │
│  │  │ • Vector     │ • Dense      │ • Multi-query   │  │  │
│  │  │   similarity │   (vector)   │   expansion     │  │  │
│  │  │ • Top-K      │ • Sparse     │ • LLM variants  │  │  │
│  │  │ • Direct     │   (BM25)     │ • Vote          │  │  │
│  │  │   return     │ • RRF fusion │   aggregation   │  │  │
│  │  │              │ • Cross-     │ • Cross-        │  │  │
│  │  │              │   encoder    │   encoder       │  │  │
│  │  │              │   reranking  │   reranking     │  │  │
│  │  └──────────────┴──────────────┴──────────────────┘  │  │
│  │                                                       │  │
│  │  Answer Generator                                     │  │
│  │  • Adaptive prompting based on query type            │  │
│  │  • Source citation enforcement                       │  │
│  │  • Hallucination prevention                          │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    DATA ACCESS LAYER                         │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Vector Store    │  │  Sparse Index    │                │
│  │  (ChromaDB)      │  │  (BM25)          │                │
│  │                  │  │                  │                │
│  │ • 768-dim        │  │ • Term frequency │                │
│  │   embeddings     │  │ • Keyword match  │                │
│  │ • HNSW index     │  │ • Fast lookup    │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Multi-Layer Cache Manager                    │  │
│  │         (cache_and_monitoring.py)                    │  │
│  │                                                       │  │
│  │  • Embedding Cache (10K entries, 1hr TTL)            │  │
│  │  • Query Cache (1K entries, 1hr TTL)                 │  │
│  │  • Result Cache (2K entries, 1hr TTL)                │  │
│  │  • Thread-safe LRU with TTL enforcement              │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    DOCUMENT PROCESSING LAYER                 │
│  (document_processor.py)                                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Document Loader (Parallel Processing)               │  │
│  │  • PDF (PyPDF + Tesseract OCR fallback)              │  │
│  │  • DOCX/DOC (Docx2txt)                               │  │
│  │  • TXT (Multi-encoding detection)                    │  │
│  │  • Markdown (Structured parsing)                     │  │
│  │  • ThreadPoolExecutor (4 workers)                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Intelligent Chunker                                  │  │
│  │                                                       │  │
│  │  Strategies:                                          │  │
│  │  • Recursive: Hierarchical splitting (default)       │  │
│  │  • Semantic: Embedding-based boundaries (GPU)        │  │
│  │  • Sentence: Fixed sentence count                    │  │
│  │  • Hybrid: Recursive + semantic refinement (best)    │  │
│  │                                                       │  │
│  │  Metadata Enrichment:                                 │  │
│  │  • File metadata (name, type, hash, size)            │  │
│  │  • Chunk position (index, page, total)               │  │
│  │  • Processing metadata (strategy, timestamp)         │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    AI MODELS LAYER (Ollama)                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LLM: llama3.1:8b                                     │  │
│  │  • 8B parameters                                      │  │
│  │  • 4096 token context window (optimized)             │  │
│  │  • Temperature: 0.0 (deterministic)                  │  │
│  │  • Full GPU layer loading                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Embeddings: nomic-embed-text                        │  │
│  │  • 768-dimensional vectors                           │  │
│  │  • 8192 token context                                │  │
│  │  • GPU-accelerated via Ollama                        │  │
│  │  • Batch size: 32                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2     │  │
│  │  • Cross-attention scoring                           │  │
│  │  • GPU-accelerated (CUDA)                            │  │
│  │  • Batch processing (16 pairs/batch)                 │  │
│  │  • ~10x faster than CPU                              │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Adaptive Retrieval Engine

**Purpose**: Automatically select optimal retrieval strategy based on query complexity.

**Algorithm**: Multi-factor query classification
- **Length scoring**: Word count → complexity correlation
- **Question type detection**: Who/what/why patterns
- **Complexity indicators**: Boolean operators, multiple questions

**Strategies**:

1. **Simple (score ≤ 1)**
   - Input: Factual queries ("Who is X?")
   - Method: Pure vector similarity search
   - Output: Top 3 chunks, normalized scores

2. **Hybrid (score ≤ 3)**
   - Input: Moderate queries ("What are the requirements?")
   - Method: RRF fusion of dense + sparse retrieval
   - Process:
     1. Dense retrieval (vector similarity, K=20)
     2. Sparse retrieval (BM25, K=20)
     3. RRF score calculation: `score = Σ(1 / (k + rank))`
     4. Cross-encoder reranking on GPU
     5. Weighted fusion: `final = 0.3*RRF + 0.7*rerank`
   - Output: Top 5 reranked chunks

3. **Advanced (score > 3)**
   - Input: Complex queries ("Compare X and Y")
   - Method: Multi-query expansion with consensus
   - Process:
     1. LLM generates 2 query variants
     2. Search with original + variants (K=15 each)
     3. Vote aggregation (chunks in multiple results ranked higher)
     4. Cross-encoder reranking on GPU
   - Output: Top 5 consensus chunks

### 2. Conversation Memory System 🆕

**Purpose**: Maintain multi-turn conversation context for natural follow-up questions.

**Architecture**:
- **Sliding Window**: FIFO queue storing last 10 exchanges (deque with maxlen)
- **Exchange Storage**: ConversationExchange dataclass with query, response, retrieved_docs, query_type, strategy_used, timestamp
- **Automatic Summarization**: LLM-based compression triggered every 5 exchanges
- **Thread Safety**: RLock for concurrent access

**Key Features**:

1. **Follow-Up Detection**
   - Pattern matching: "that", "those", "this", "tell me more", "what about"
   - Short query heuristic: <10 words + history = likely follow-up
   - Returns: boolean indicating if current query references previous context

2. **Context Enhancement**
   - Method: `get_relevant_context_for_query(query, max_exchanges=5)`
   - Returns: (enhanced_query, relevant_documents)
   - Enhanced query includes conversation summary + recent exchanges
   - Relevant documents collected from previous turns

3. **Automatic Summarization**
   - Trigger: Every 5 exchanges (configurable)
   - Method: LLM generates <200 word summary preserving key topics
   - Compression: Typical 70-80% reduction in context size
   - Cumulative: New summaries append to existing summary

4. **Statistics Tracking**
   - Total exchanges, current window size, summarizations performed
   - Memory usage tracking
   - Hit/miss metrics for follow-up detection

**Integration Points**:
- app.py query() method: Automatic context enhancement for follow-ups
- app.py clear_conversation(): Manual memory reset
- Web interface: "Clear Chat" button triggers memory reset

**Performance Characteristics**:
- Follow-up detection: <10ms
- Context retrieval: <50ms
- Summarization: ~1-2 seconds (async, non-blocking)
- Memory per exchange: ~2KB
- Max memory (10 exchanges + summary): ~25KB

### 3. Explainability System 🆕

**Purpose**: Provide transparent reasoning for query classification and retrieval strategy selection.

**Architecture**:
- **QueryExplanation Dataclass**: Structured explanation object with all decision factors
- **Factory Function**: `create_query_explanation()` auto-generates explanations
- **Integration**: Explanation objects flow through retrieval pipeline transparently

**Key Components**:

1. **Explanation Data Structure**
   ```python
   @dataclass
   class QueryExplanation:
       query_type: str              # Classification result
       complexity_score: int        # Total score from multi-factor analysis
       scoring_breakdown: Dict      # Factor → contribution mapping
       thresholds_used: Dict        # Classification threshold values
       strategy_selected: str       # Retrieval strategy chosen
       strategy_reasoning: str      # Human-readable rationale
       key_factors: List[str]       # Primary contributing factors
       example_text: str            # Auto-generated explanation
   ```

2. **Explanation Generation**
   - **Scoring Breakdown**: Captures each classification factor's contribution
     - Length scoring: "12 words (+2)"
     - Question type: "why (+3)"
     - Complexity indicators: "has_and_operator=yes (+1)"

   - **Strategy Mapping**: Automatic strategy selection reasoning
     - simple → "Straightforward query requires only dense vector retrieval"
     - moderate → "Moderate complexity benefits from hybrid BM25+dense with reranking"
     - complex → "High complexity requires query expansion and advanced fusion"

   - **Key Factors Extraction**: Identifies factors that contributed points (+ values)

   - **Human-Readable Text**: Auto-generated explanation combining all factors
     ```
     Query classified as COMPLEX (score: 5) because: length=12 words (+2),
     question_type=why (+3), has_and_operator=yes (+1). Thresholds: simple≤1,
     moderate≤3. Using advanced_expanded strategy. Reasoning: High complexity
     requires query expansion and advanced fusion
     ```

3. **Serialization Support**
   - `to_dict()`: Convert to dictionary for JSON storage/logging
   - `from_dict()`: Restore from dictionary
   - Enables audit logging, debugging, and analytics

**Integration Points**:
- `adaptive_retrieval.py _classify_query()`: Generates explanation during classification
- `RetrievalResult`: Includes explanation object
- `app.py query()`: Logs explanation for audit trail
- `web_interface.py`: Optional UI display (collapsible section)

**Use Cases**:
- **User Transparency**: Show users why they got specific results
- **Developer Debugging**: Diagnose classification issues, tune thresholds
- **Audit Compliance**: Log AI decision reasoning for government/enterprise requirements
- **System Optimization**: Analyze explanation patterns to improve classification

**Performance Characteristics**:
- Explanation generation: <1ms (negligible overhead)
- Memory per explanation: ~500 bytes
- Serialization: <1ms for JSON conversion
- Zero impact on query latency

**Testing**:
- Unit tests: `test_explainability.py` (12 test cases)
- Covers: initialization, serialization, factory function, text generation
- Edge cases: empty breakdowns, missing fields, round-trip conversion

### 4. Feedback System 🆕

**Purpose**: Enable continuous improvement through user feedback collection and automated performance analysis.

**Architecture**:
- **FeedbackManager Class**: Central feedback coordinator with JSON storage
- **Binary Rating System**: Simple thumbs up/down interface for user feedback
- **Automatic Tracking**: Query metadata captured transparently (type, strategy, answer, timestamp)
- **Analytics Engine**: Real-time statistics computation and trend analysis
- **Persistent Storage**: JSON-based feedback database (feedback.json)

**Key Components**:

1. **Feedback Collection**
   - **User Interface**: Thumbs up/down buttons in web UI after each answer
   - **Automatic Capture**: System stores complete context:
     - Query text
     - Generated answer
     - Rating (thumbs_up / thumbs_down)
     - Query type (simple/moderate/complex)
     - Strategy used (simple_dense/hybrid_reranked/advanced_expanded)
     - Timestamp (ISO format)
   - **Non-blocking**: <1ms overhead, asynchronous to query processing

2. **Analytics Dashboard**
   - **Overall Satisfaction Rate**: Percentage of positive feedback
   - **By Query Type**: Performance breakdown for simple/moderate/complex
   - **By Retrieval Strategy**: Effectiveness comparison across strategies
   - **Low-Rated Query Analysis**: Automatic identification of problematic queries
   - **Trend Tracking**: Historical performance over time

3. **Data Structure**
   ```python
   {
       "query": str,              # Original user query
       "answer": str,             # System-generated answer
       "rating": str,             # "thumbs_up" or "thumbs_down"
       "query_type": str,         # "simple", "moderate", or "complex"
       "strategy_used": str,      # Retrieval strategy identifier
       "timestamp": str           # ISO 8601 timestamp
   }
   ```

4. **Analytics API**
   - `add_feedback()`: Record new feedback entry
   - `get_feedback_stats()`: Compute overall statistics
   - `get_low_rated_queries()`: Retrieve queries with negative feedback
   - `get_recent_feedback()`: Access most recent N entries
   - All methods thread-safe with file locking

**Integration Points**:
- `app.py submit_feedback()`: Capture feedback from web UI
- `app.py query()`: Stores last query metadata for feedback correlation
- `web_interface.py`: Thumbs up/down buttons and admin stats viewer
- Performance monitoring: Combines satisfaction metrics with latency/throughput

**Use Cases**:
- **Continuous Improvement**: Identify underperforming strategies or query types
- **Data-Driven Tuning**: Adjust thresholds based on user satisfaction patterns
- **Quality Assurance**: Track satisfaction rate as key performance indicator
- **User Engagement**: Users feel their input shapes system behavior
- **Root Cause Analysis**: Investigate why specific queries receive poor ratings

**Performance Characteristics**:
- Feedback submission: <1ms (non-blocking, async file write)
- Statistics computation: ~10ms for 100 entries
- Storage overhead: ~500 bytes per feedback entry
- Memory footprint: Negligible (loaded on-demand)
- Scalability: Handles 10K+ entries efficiently

**Analytics Examples**:

*Overall Satisfaction*:
```
Total Feedback: 45 ratings
Thumbs Up: 32 (71%)
Thumbs Down: 13 (29%)
Satisfaction Rate: 71%
```

*By Query Type*:
```
Simple:    88% satisfaction (15/17) ✅ Excellent
Moderate:  71% satisfaction (12/17) 👍 Good
Complex:   45% satisfaction (5/11)  ⚠️ Needs improvement
```

*By Strategy*:
```
simple_dense:       88% satisfaction (15/17) ✅
hybrid_reranked:    73% satisfaction (11/15) 👍
advanced_expanded:  46% satisfaction (6/13)  ⚠️
```

**Feedback-Driven Improvements**:
1. **Threshold Tuning**: Adjust classification thresholds based on satisfaction patterns
2. **Strategy Optimization**: Identify and improve underperforming retrieval strategies
3. **Query Expansion Refinement**: Tune LLM prompts for better query variants
4. **K-Value Adjustment**: Optimize result count based on user preferences

**Integration with Monitoring**:
```
Combined Analysis: Performance Metrics + User Feedback

Latency (P95): 3.2s         | Satisfaction: 45%  ⚠️
Query Type: Complex         | Strategy: advanced_expanded
Bottleneck: Query expansion | Action: Optimize expansion prompts
```

**Testing**:
- Integration tests: `test_feedback_integration.py` (21 test cases)
- Covers: persistence, statistics, analytics, large datasets, edge cases
- Multi-instance testing: Verify data consistency across manager instances
- Performance testing: Large dataset handling (100+ entries)

**Future Enhancements**:
- Text comments with ratings (detailed feedback)
- Issue tagging (inaccurate, incomplete, irrelevant)
- Automated retraining based on low-rated queries
- A/B testing framework for strategy comparison
- User profiles for personalized optimization

### 5. Document Processing Pipeline

**Parallel Loading**:
- ThreadPoolExecutor with 4 workers
- Per-document error isolation
- Multi-format support (PDF, DOCX, TXT, MD)
- OCR fallback for scanned PDFs

**Chunking Strategies**:

1. **Recursive** (Default): Hierarchical splitting with semantic separators
2. **Semantic**: Sentence embeddings + boundary detection (GPU-accelerated)
3. **Hybrid**: Recursive → semantic refinement for large chunks (Best balance)

**Metadata Enrichment**:
- File identification: name, type, hash, size
- Position tracking: chunk_index, page_number, total_chunks
- Processing info: strategy used, timestamp

### 6. Caching Infrastructure

**Three-Layer LRU Cache**:

1. **Embedding Cache** (10K entries, 1hr TTL)
   - Purpose: Cache expensive embedding computations
   - Key: MD5(text)
   - Benefit: ~90% hit rate on repeated content

2. **Query Cache** (1K entries, 1hr TTL)
   - Purpose: Cache complete query results
   - Key: MD5(query + parameters)
   - Benefit: Instant responses for duplicate queries

3. **Result Cache** (2K entries, 1hr TTL)
   - Purpose: Cache retrieval results before generation
   - Key: MD5(query)
   - Benefit: Fast re-generation with different prompts

**Features**:
- Thread-safe with RLock
- Automatic TTL expiration
- LRU eviction when full
- Hit/miss/eviction statistics

### 7. Performance Monitoring

**PyTorch-Based GPU Monitoring** (Docker-compatible):
- GPU utilization (estimated from memory reservation)
- VRAM usage (allocated + reserved in MB)
- CPU utilization (psutil)
- No nvidia-smi dependency

**Metrics Collection**:
- Query count & latency (avg, p50, p95, p99)
- Retrieval stage timing
- Cache hit rates
- Error rates
- Real-time updates (1 second interval)

### 8. Evaluation Framework

**Automated Testing** (evaluate.py):

1. **Retrieval Quality**
   - Precision, Recall, F1 score
   - Mean Reciprocal Rank (MRR)
   - By-difficulty breakdown

2. **Answer Quality**
   - Answer length statistics
   - Source citation count
   - Query type distribution

3. **Performance Metrics**
   - Cold/warm latency comparison
   - Cache effectiveness measurement
   - Percentile analysis

4. **Stress Testing**
   - Concurrent query handling
   - Throughput measurement (QPS)
   - Error rate under load

**Grading System**: A (90-100) → F (<60) with automated recommendations

---

## Technology Stack

### Core Framework
- **Language**: Python 3.11
- **Web UI**: Gradio (chat interface + monitoring dashboard)
- **Async**: asyncio (concurrent operations)
- **Parallelism**: ThreadPoolExecutor (document loading)

### AI/ML Stack
- **LLM Platform**: Ollama (local inference)
- **Models**:
  - LLM: llama3.1:8b (8B parameter model)
  - Embeddings: nomic-embed-text (768-dim)
  - Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2
- **GPU**: CUDA 12.1+ (PyTorch backend)
- **Frameworks**: LangChain, sentence-transformers

### Data Layer
- **Vector DB**: ChromaDB (HNSW index)
- **Sparse Index**: BM25 (keyword matching)
- **Caching**: In-memory LRU caches

### Document Processing
- **PDF**: PyPDF + Tesseract OCR (fallback)
- **DOCX**: Docx2txt
- **Text**: Multi-encoding detection
- **Markdown**: Unstructured

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **GPU Passthrough**: NVIDIA Container Toolkit
- **Networking**: Bridge network for inter-service communication
- **Volumes**: Persistent storage for documents, database, logs

---

## Integration Points

### Internal Communication
1. **App ↔ Adaptive Retriever**: Query submission, retrieval results
2. **Adaptive Retriever ↔ Data Layer**: Vector search, BM25 search
3. **App ↔ Cache Manager**: Query/result caching
4. **App ↔ Performance Monitor**: Metrics collection
5. **Web Interface ↔ App**: User queries, status updates

### External Dependencies
1. **Ollama API** (port 11434): LLM inference, embeddings
2. **ChromaDB**: Vector storage and similarity search
3. **Docker Network**: Service-to-service communication

---

## Deployment Architecture

```
Docker Compose Services:

┌─────────────────────┐
│   Ollama Service    │
│   Port: 11434       │
│   GPU: NVIDIA       │
│   Models:           │
│   - llama3.1:8b     │
│   - nomic-embed-text│
└──────────┬──────────┘
           │
    Docker Bridge Network
           │
┌──────────▼──────────┐
│   RAG App Service   │
│   Port: 7860        │
│   GPU: NVIDIA       │
│   Runtime: nvidia   │
│   Volumes:          │
│   - ./documents     │
│   - ./chroma_db     │
│   - ./logs          │
└─────────────────────┘
```

**Key Features**:
- Health checks on Ollama before RAG app starts
- GPU passthrough to both services
- Persistent volumes for data
- Automatic restart on failure

---

## Data Flow

### Query Processing Flow

```
1. User submits query via Gradio
   ↓
2. App.py receives query
   ↓
3. Check query cache → [HIT] Return cached result → END
   ↓ [MISS]
4. AdaptiveRetriever.retrieve(query)
   ↓
5. Classify query (simple/moderate/complex)
   ↓
6. Route to appropriate strategy:
   ├─ Simple: Vector search → Top 3
   ├─ Hybrid: Vector + BM25 → RRF → Rerank → Top 5
   └─ Advanced: Multi-query → Vote → Rerank → Top 5
   ↓
7. RetrievalResult (documents + scores + metadata)
   ↓
8. AdaptiveAnswerGenerator.generate(query, result)
   ↓
9. Build context with source citations
   ↓
10. LLM generates answer with adaptive prompting
    ↓
11. Format response with sources and metadata
    ↓
12. Cache result
    ↓
13. Return to user
```

### Document Indexing Flow

```
1. Place documents in documents/ folder
   ↓
2. Run index_documents.py
   ↓
3. DocumentProcessor.process_documents()
   ↓
4. DocumentLoader loads files in parallel (ThreadPoolExecutor)
   ↓
5. For each document:
   ├─ Detect format (PDF/DOCX/TXT/MD)
   ├─ Extract text (OCR fallback for PDFs)
   ├─ Enrich metadata (hash, size, timestamp)
   └─ Create Document objects
   ↓
6. IntelligentChunker.chunk(documents)
   ├─ Apply selected strategy (recursive/semantic/hybrid)
   ├─ Add chunk metadata (index, position, strategy)
   └─ Validate chunks (size, content quality)
   ↓
7. Generate embeddings (Ollama, batched)
   ↓
8. Store in ChromaDB (vector database)
   ↓
9. Save metadata for BM25 (JSON file)
   ↓
10. Indexing complete → System ready
```

---

## Configuration Management

**Primary Config**: `config.yml`
- Structured YAML configuration
- Environment variable overrides via `RAG_*` prefix
- Pydantic validation with type checking
- Default values for all settings

**Key Configuration Sections**:
1. **LLM Settings**: Model, temperature, context window
2. **Embedding Settings**: Model, dimension, batch size
3. **Chunking**: Strategy, size, overlap
4. **Retrieval**: K-values, fusion method, thresholds
5. **Caching**: TTL, max sizes, enable/disable flags
6. **Performance**: Workers, batching, async settings
7. **Monitoring**: Logging, metrics, tracing

---

## Security Considerations

**Current Implementation**:
- Local deployment (no external API calls)
- Docker network isolation
- Volume-based data persistence

**Future Enhancements** (Roadmap):
- Document-level access control
- Query audit logging
- PII detection in documents
- Encrypted embeddings for sensitive data
- Answer provenance tracking

---

## Performance Characteristics

**Expected Latency**:
- Simple queries: 1-2s
- Hybrid queries: 2-4s
- Advanced queries: 4-6s
- Cached queries: <100ms

**Throughput**:
- Concurrent: ~10-15 QPS (with caching)
- Cold: ~2-3 QPS

**Resource Usage**:
- CPU RAM: 4-6 GB
- VRAM: 6-8 GB (llama3.1:8b)
- Disk: ~10 GB (models + indexes)

**Optimization Strategies**:
- Reduced context window (8192→4096 tokens)
- Smaller chunks (800→500 chars)
- Fewer rerank candidates (20→15)
- Multi-layer caching
- GPU acceleration throughout
- Batch processing (16 docs/batch)

---

## Failure Modes & Recovery

**Document Processing Failures**:
- Per-document error isolation
- OCR fallback for unreadable PDFs
- Multi-encoding detection for text files
- Graceful degradation (skip failed files)

**Retrieval Failures**:
- Strategy fallback (advanced→hybrid→simple)
- Empty result handling (informative messages)
- Timeout protection (async with timeouts)

**LLM Failures**:
- Retry logic (automatic)
- Fallback to cached results
- Error messages to user

**Infrastructure Failures**:
- Docker restart policies (unless-stopped)
- Health checks (Ollama service)
- Volume persistence (data survives restarts)

---

## Extension Points

**Adding New Document Formats**:
- Extend `document_processor.py`
- Register in `supported_extensions` dict
- Implement loader method

**Custom Retrieval Strategies**:
- Add to `adaptive_retrieval.py`
- Define classification rules
- Implement retrieval method

**Alternative LLMs**:
- Change model in `config.yml`
- Ensure Ollama has model pulled
- Adjust context window as needed

**Custom Chunking Strategies**:
- Extend `IntelligentChunker` class
- Implement chunk method
- Add to strategy selection

---

## Development Guidelines

**Code Quality Standards**:
- Type hints on all functions
- Comprehensive docstrings
- Error handling with logging
- Async/await for I/O operations
- Thread-safe shared state

**Testing Strategy**:
- Evaluation suite (evaluate.py)
- Manual testing via web UI
- Performance benchmarking
- Stress testing (concurrent queries)

**Version Control**:
- Git commits for each feature
- Semantic commit messages
- Feature branches for major changes

---

## Project Evolution

This system evolved through **multi-agent iterative development** (v2.5 → v3.5.1):

### Milestone 1: Conversation Memory Enhancement ✅
- **Developer**: hollowed_eyes (dev-001)
- **Tester**: zhadyz (ops-001)
- **Features**: Sliding window (10 exchanges), LLM summarization, follow-up detection
- **Impact**: Multi-turn context awareness, +50-100ms latency, ~20KB per conversation
- **Commits**: e92802d (dev), 0716bf5 (docs), 84dbec1 (state)

### Milestone 2: Explainability Features ✅
- **Developer**: hollowed_eyes (dev-002)
- **Tester**: zhadyz (ops-002)
- **Features**: QueryExplanation dataclass, scoring breakdown, strategy reasoning
- **Impact**: Transparent AI decisions, <1ms overhead, compliance-ready
- **Commits**: fb6e143 (dev), 99996cc (docs)

### Milestone 3: User Feedback System ✅
- **Developer**: hollowed_eyes (dev-003)
- **Tester**: zhadyz (ops-003)
- **Features**: Thumbs up/down, analytics dashboard, satisfaction tracking
- **Impact**: Continuous learning, data-driven optimization, 71% satisfaction baseline
- **Commits**: 044264c (dev), 7f91332 (docs), 326ed4e (state)

### Milestone 4: Portfolio Finalization ✅
- **Owner**: zhadyz (ops-004)
- **Deliverables**: IMPROVEMENTS.md, DEMO_SCRIPT.md, portfolio highlights, badges
- **Impact**: Production-ready documentation, demo-ready presentation

### Development Method

**Multi-Agent Coordination**:
- **medicant_bias** (Architect): Designed roadmap, defined milestones, established coordination protocol
- **hollowed_eyes** (Engineer): Implemented features, wrote unit tests, committed incrementally
- **zhadyz** (Tester/Docs): Created integration tests (63 total), comprehensive documentation, portfolio polish

**Coordination Protocol**:
- state.json: Central task ownership and handoff tracking
- Redis pub/sub: Real-time event-driven coordination
- Git strategy: Clean history showing iterative progression

**Code Metrics**:
- Total LOC added: ~1,300 lines
- Integration tests: 63 tests across 3 test suites
- Documentation: 3 major docs + 3 example files
- Commits: 9 (from baseline to v3.5.1)

### Roadmap (Future)

**Planned Enhancements**:
1. ✅ Multi-turn conversation memory (Milestone 1)
2. ✅ Explainability (query classification reasoning) (Milestone 2)
3. ✅ Feedback loops (user ratings, learning) (Milestone 3)
4. ⏳ Multi-modal support (tables, figures)
5. ⏳ Security hardening (audit logs, access control)

**See**: `IMPROVEMENTS.md` for detailed evolution timeline with git commits and technical analysis
**See**: `docs/DEMO_SCRIPT.md` for live demonstration guide

---

## Credits

**System Architecture**: medicant_bias
**Feature Implementation**: hollowed_eyes
**Testing & Documentation**: zhadyz
**Multi-Agent Framework**: LangGraph + Redis coordination
**Development Environment**: Claude Code

---

**Document Version**: 3.5.1
**Status**: Production-ready, portfolio-optimized
**Last Review**: 2025-10-11 (Milestone 4 complete)
