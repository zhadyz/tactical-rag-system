# Tactical RAG System - Architecture Documentation

**Version**: 3.5
**Last Updated**: 2025-10-11
**Created By**: MEDICANT_BIAS

---

## System Overview

The Tactical RAG System is an enterprise-grade document intelligence platform that employs adaptive retrieval strategies, GPU-accelerated processing, and real-time performance monitoring to deliver accurate, context-aware answers from document repositories.

### Core Design Principles

1. **Adaptive Intelligence**: Query complexity determines retrieval strategy automatically
2. **GPU Acceleration**: All compute-intensive operations leverage CUDA when available
3. **Multi-Layer Caching**: Aggressive caching at embedding, query, and result levels
4. **Production-Ready**: Comprehensive monitoring, evaluation, and error handling
5. **Docker-Native**: Full containerization with GPU passthrough support

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

### 2. Document Processing Pipeline

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

### 3. Caching Infrastructure

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

### 4. Performance Monitoring

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

### 5. Evaluation Framework

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

## Roadmap

See `state.json` for current improvement priorities and task assignments.

**Planned Enhancements**:
1. Multi-turn conversation memory
2. Explainability (query classification reasoning)
3. Feedback loops (user ratings, learning)
4. Multi-modal support (tables, figures)
5. Security hardening (audit logs, access control)

---

**Document Version**: 1.0
**Status**: Production-ready baseline
**Next Review**: After each improvement milestone
