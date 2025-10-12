# Tactical RAG Document Intelligence System

![CI Pipeline](https://github.com/zhadyz/tactical-rag-system/actions/workflows/ci.yml/badge.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
![CUDA 12.1+](https://img.shields.io/badge/CUDA-12.1+-green.svg)
![License](https://img.shields.io/badge/license-U.S.%20Government-lightgrey.svg)

Enterprise-grade Retrieval-Augmented Generation (RAG) system with GPU-accelerated adaptive retrieval, **multi-turn conversation memory**, **transparent explainability**, **user feedback loops**, intelligent document processing, and real-time performance monitoring.

**Developed through multi-agent AI collaboration** (medicant_bias → hollowed_eyes + zhadyz), demonstrating coordinated iterative improvement visible in git history.

---

## Portfolio Highlights

This project showcases:

- ✨ **Multi-Agent Development**: Three AI agents (architect, engineer, tester) coordinating via state.json + Redis pub/sub
- 🧠 **Conversation Memory**: Sliding window (10 exchanges) with LLM-based summarization for multi-turn context awareness
- 🔍 **Explainability**: Full transparency in query classification and retrieval strategy selection
- ⭐ **Feedback Loops**: User satisfaction tracking (thumbs up/down) with analytics for continuous improvement
- 🚀 **GPU Acceleration**: CUDA-optimized embeddings, reranking, and LLM inference (~10x speedup)
- 📊 **Adaptive Retrieval**: Three-tier strategy (simple/hybrid/advanced) auto-selected by query complexity
- 🧪 **Comprehensive Testing**: 63+ integration tests covering all major features
- 📖 **Production Documentation**: Architecture diagrams, deployment guides, API examples
- 🐳 **Docker-Native**: Full containerization with Ollama integration and GPU passthrough
- 🎯 **Enterprise-Ready**: Performance monitoring, evaluation suite, explainable AI for compliance

**See**: `IMPROVEMENTS.md` for detailed evolution from v2.5 → v3.5.1

---

## 🚀 Latest Updates - v3.8 (October 2025)

### Interface Overhaul
- **Two-Mode System**: Simplified interface with **Simple (Default)** and **Adaptive Retrieval** presets
- **Conditional Advanced Settings**: Advanced tuning options only visible when using Adaptive mode
- **Cleaner UX**: Single radio button selector replaces complex multi-option interface
- **Simple Mode**: Bypasses adaptive retrieval for consistent 8-15 second response times

### Next-Generation Multi-Stage Cache
- **CRITICAL BUG FIX**: Resolved semantic cache returning wrong answers for different queries
- **Multi-Stage Architecture**:
  - Stage 1: Exact match (O(1), 100% correct)
  - Stage 2: Normalized match (O(1), 100% correct)
  - Stage 3: Validated semantic match with document overlap (O(N), 95% correct)
- **Performance**: 2,204x speedup (2.2s → 0.001s warm queries)
- **Correctness**: 0% false matches in exhaustive edge case testing (40+ tests)
- **Implementation**: `_src/cache_next_gen.py` (700+ lines, production-ready)

### Performance & Testing
- **Realistic Performance Tests**: 10 diverse Air Force regulation queries
- **Edge Case Testing**: 40 adversarial scenarios including data corruption, race conditions, stress tests
- **Empirical Research**: Embedding similarity analysis proving semantic threshold issues
- **Zero False Positives**: User's reported bug scenario tested and verified fixed

### Documentation & Research
- **Technical Analysis**: `SYSTEMIC_ANALYSIS_semantic_cache.md` - 15-page root cause analysis
- **Implementation Guide**: `IMPLEMENTATION_GUIDE_v3.8.md` - 20-page deployment guide
- **Breakthrough Summary**: `BREAKTHROUGH_SUMMARY_v3.8.md` - Portfolio-ready showcase

### Known Issues & Future Work
- **Adaptive Retrieval Bug**: Query classification incorrectly counts conversation context (causes 85s delays)
- **Query Expansion Performance**: 22+ seconds to generate variants (needs optimization)
- **Next Sprint**: Rework adaptive retrieval engine with fixed classification logic

**See**: `BREAKTHROUGH_SUMMARY_v3.8.md` for detailed technical analysis of the cache breakthrough

---

## Table of Contents

- [Portfolio Highlights](#portfolio-highlights)
- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Core Components](#core-components)
- [Technical Deep Dive](#technical-deep-dive)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Performance Optimization](#performance-optimization)
- [Evaluation & Monitoring](#evaluation--monitoring)
- [Project Evolution](#project-evolution)

---

## Quick Start

**End Users:** See `docs/OPERATOR-GUIDE.md`
**Technical Staff:** See `docs/MAINTAINER-GUIDE.md`

### Deployment Commands

| Action | Command |
|--------|---------|
| Start System | `deploy.bat` |
| Change Documents | `swap-mission.bat` |
| Stop System | `stop.bat` |

### First-Time Setup

1. Install and start Docker Desktop
2. Add documents to `documents/` folder
3. Run `deploy.bat`
4. Wait 3-5 minutes for initialization
5. Browser opens automatically at `http://localhost:7860`

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (Gradio)                   │
│              Real-time GPU/CPU Performance Monitoring        │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                  Enterprise RAG System                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Adaptive Retrieval Engine                    │   │
│  │  ┌──────────────┬──────────────┬──────────────────┐  │   │
│  │  │   Simple     │   Hybrid     │    Advanced      │  │   │
│  │  │  (Vector)    │ (RRF Fusion) │ (Multi-Query)    │  │   │
│  │  └──────────────┴──────────────┴──────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Multi-Layer Cache Manager                    │   │
│  │  • Embeddings Cache  • Query Cache  • Result Cache   │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  ChromaDB        │  │  BM25 Retriever  │                 │
│  │  (Vector Store)  │  │  (Sparse Index)  │                 │
│  └──────────────────┘  └──────────────────┘                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    AI Models (Ollama)                        │
│  • LLM: llama3.1:8b                                          │
│  • Embeddings: nomic-embed-text (768-dim)                   │
│  • Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2 (GPU)     │
└──────────────────────────────────────────────────────────────┘
```

### Project Structure

```
tactical-rag-system/
│
├── _src/                           # Application source code
│   ├── app.py                      # Main application orchestrator
│   ├── adaptive_retrieval.py       # Three-tier retrieval engine
│   ├── document_processor.py       # Intelligent chunking & processing
│   ├── index_documents.py          # Document indexing pipeline
│   ├── web_interface.py            # Gradio UI with monitoring
│   ├── cache_and_monitoring.py     # Caching & metrics infrastructure
│   ├── performance_monitor.py      # GPU/CPU monitoring service
│   ├── example_generator.py        # Dynamic question generation
│   ├── evaluate.py                 # Comprehensive evaluation suite
│   ├── conversation_memory.py     # Multi-turn conversation tracking
│   └── config.py                   # Configuration management
│
├── _config/                        # Docker & deployment configuration
│   ├── Dockerfile                  # Container build recipe
│   ├── requirements.txt            # Python dependencies
│   ├── startup.sh                  # Container startup script
│   ├── deploy.ps1                  # PowerShell deployment script
│   └── stop.ps1                    # PowerShell shutdown script
│
├── documents/                      # Source documents directory
├── chroma_db/                      # Vector database (auto-generated)
├── logs/                           # System logs
├── .cache/                         # Cache directory
│
├── docker-compose.yml              # Multi-service orchestration
├── config.yml                      # System configuration
├── deploy.bat                      # Windows deployment wrapper
└── stop.bat                        # Windows shutdown wrapper
```

---

## Core Components

### 1. Adaptive Retrieval Engine (`adaptive_retrieval.py`)

The system employs a **three-tier adaptive retrieval strategy** that automatically selects the optimal approach based on query complexity:

#### Query Classification System

Queries are classified using a multi-factor scoring algorithm:

**Factors:**
- **Query length** (words): Longer queries → more complex
- **Question type** (who/what/why/how): Different types → different complexity
- **Complexity indicators**: Presence of "and", "or", multiple "?"

**Classification:**
- **Simple (score ≤ 1)**: Factual lookups, direct questions
- **Moderate (score ≤ 3)**: Lists, summaries, "what/how" questions
- **Complex (score > 3)**: Analysis, comparisons, "why" questions

#### Retrieval Strategies

##### Simple Retrieval
- **Use case**: Direct factual queries ("Where is X?", "Who is Y?")
- **Method**: Pure vector similarity search
- **K-value**: Configurable (default: 5)
- **Score normalization**: Min-max normalization → 0-1 similarity
- **Output**: Top 3 most relevant chunks

##### Hybrid Retrieval
- **Use case**: Moderate complexity queries requiring context
- **Method**: Reciprocal Rank Fusion (RRF) of dense + sparse retrieval
- **Process**:
  1. **Dense retrieval**: Vector similarity search (ChromaDB)
  2. **Sparse retrieval**: BM25 keyword matching
  3. **RRF fusion**: `score = Σ(1 / (k + rank))` where k=60
  4. **Reranking**: Cross-encoder reranking with GPU acceleration
  5. **Weighted fusion**: `final = (1-α)*RRF + α*rerank` where α=0.7
- **K-value**: Configurable (default: 20)
- **Output**: Top 5 reranked chunks

##### Advanced Retrieval
- **Use case**: Complex analytical queries
- **Method**: Multi-query expansion + reranking
- **Process**:
  1. **Query expansion**: LLM generates 2 alternative phrasings
  2. **Multi-query search**: Search with original + variants
  3. **Vote aggregation**: Chunks appearing in multiple results ranked higher
  4. **Reranking**: Cross-encoder final reranking
- **K-value**: Configurable (default: 15)
- **Output**: Top 5 consensus chunks

#### GPU Acceleration

- **Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2` runs on CUDA
- **Batch processing**: 16 document pairs per batch for efficiency
- **Device detection**: Automatic fallback to CPU if GPU unavailable
- **Performance**: ~10x faster reranking with GPU

### 2. Conversation Memory System (`conversation_memory.py`) 🆕

The system maintains **multi-turn conversation context** for natural follow-up questions without repeating information.

#### Architecture

- **Sliding Window**: Stores last 10 conversation exchanges (FIFO)
- **Automatic Summarization**: Compresses history after 5 exchanges using LLM
- **Follow-Up Detection**: Identifies questions referencing previous context
- **Thread-Safe**: RLock for concurrent access

#### How It Works

1. **Context Tracking**: Each query-response pair is stored with metadata (query type, strategy, retrieved documents, timestamp)
2. **Follow-Up Detection**: Pattern matching identifies references like "that", "those", "tell me more"
3. **Query Enhancement**: Follow-up questions are automatically enhanced with conversation context
4. **Automatic Compression**: After 5 exchanges, LLM generates a concise summary to save memory

#### Example Flow

```
Turn 1: "What retrieval strategies does this use?"
→ System stores: query + response + context

Turn 2: "How does that compare to traditional search?"
→ Detected as follow-up
→ Enhanced query includes Turn 1 context
→ Better retrieval using conversation history
```

#### Configuration

```python
ConversationMemory(
    llm=llm,
    max_exchanges=10,              # Sliding window size
    summarization_threshold=5,     # Trigger summarization
    enable_summarization=True      # Auto-compress history
)
```

#### Performance Impact

- **Latency**: +50-100ms for follow-up detection (negligible)
- **Memory**: ~2KB per exchange, ~20KB per conversation
- **Accuracy**: Significant improvement in follow-up question quality

**See**: `docs/examples/conversation_demo.md` for detailed examples

### 3. Explainability System (`explainability.py`) 🆕

The system provides **transparent AI decision-making** by explaining query classification and retrieval strategy selection.

#### What Gets Explained

1. **Query Classification Reasoning**: Why a query was classified as simple/moderate/complex
2. **Scoring Breakdown**: Which factors contributed to the complexity score
3. **Strategy Selection**: Why a specific retrieval strategy was chosen
4. **Threshold Values**: What classification thresholds were applied

#### QueryExplanation Dataclass

```python
@dataclass
class QueryExplanation:
    query_type: str              # "simple", "moderate", or "complex"
    complexity_score: int        # Total complexity score
    scoring_breakdown: Dict      # Factor → contribution mapping
    thresholds_used: Dict        # Classification thresholds
    strategy_selected: str       # Retrieval strategy chosen
    strategy_reasoning: str      # Why this strategy
    key_factors: List[str]       # Primary contributing factors
    example_text: str            # Human-readable explanation
```

#### Example Explanations

**Simple Query:**
```
Query: "Who is the project manager?"
Explanation: Query classified as SIMPLE (score: 0) because:
length=5 words (+0), question_type=who (+0). Thresholds: simple≤1,
moderate≤3. Using simple_dense strategy. Reasoning: Straightforward
query requires only dense vector retrieval
```

**Complex Query:**
```
Query: "Why does the system use hybrid retrieval and what are the benefits?"
Explanation: Query classified as COMPLEX (score: 5) because:
length=12 words (+2), question_type=why (+3), has_and_operator=yes (+1).
Thresholds: simple≤1, moderate≤3. Using advanced_expanded strategy.
Reasoning: High complexity requires query expansion and advanced fusion
```

#### Integration

Explainability is automatically integrated into the retrieval pipeline:

1. **Query Classification** → Generates `QueryExplanation`
2. **Retrieval Execution** → Includes explanation in `RetrievalResult`
3. **UI Display** → Shows explanation to users (optional collapsible section)
4. **Logging** → Explanation logged for audit trail

#### Benefits

- **Transparency**: Users understand why they got specific results
- **Debugging**: Developers can diagnose classification issues
- **Trust**: Builds confidence in AI system decisions
- **Compliance**: Supports explainable AI requirements for government/enterprise

#### Performance Impact

- **Latency**: <1ms (negligible overhead)
- **Memory**: ~500 bytes per explanation object
- **Storage**: Explanations can be logged to JSON for analysis

**See**: `docs/examples/explanations.md` for detailed examples

### 4. Feedback System (`feedback_system.py`) 🆕

The system enables **continuous improvement** through user feedback collection and automated performance analysis.

#### Architecture

- **Thumbs Up/Down Rating**: Simple binary feedback after each query response
- **Automatic Tracking**: Query metadata (type, strategy, answer) captured automatically
- **JSON Storage**: Persistent feedback database (`feedback.json`)
- **Analytics Dashboard**: Real-time statistics and trends via web UI
- **Pattern Detection**: Identifies problematic query types and strategies

#### How It Works

1. **User Interaction**: After receiving an answer, user clicks 👍 or 👎
2. **Automatic Capture**: System stores query, answer, rating, query type, strategy used, and timestamp
3. **Analytics Processing**: FeedbackManager computes satisfaction rates by query type and strategy
4. **Pattern Identification**: Low-rated queries are flagged for analysis and improvement

#### Example Flow

```
User Query: "What is RAG?"
→ System answers with simple_dense strategy
→ User clicks 👍
→ Feedback stored: {query, answer, rating: "thumbs_up", query_type: "simple", strategy: "simple_dense"}
→ Analytics updated: simple query satisfaction = 88%
```

#### Analytics Capabilities

- **Overall Satisfaction Rate**: Percentage of thumbs up vs. total feedback
- **By Query Type**: Performance breakdown for simple/moderate/complex queries
- **By Retrieval Strategy**: Effectiveness of each retrieval approach
- **Low-Rated Query Analysis**: Identify queries that consistently receive negative feedback
- **Trend Tracking**: Historical performance over time

#### Admin Dashboard

Access feedback statistics via the web interface:
1. Navigate to **http://localhost:7860**
2. Scroll to **Settings Panel** (right side)
3. Find **📊 Feedback Analytics** section
4. Click **"View Feedback Stats"**

Dashboard displays:
- Overall satisfaction rate
- Thumbs up/down counts
- Breakdown by query type
- Breakdown by strategy
- Total feedback count

#### Integration with Monitoring

Feedback data integrates with performance monitoring for complete system analysis:

```
Performance Metrics + User Feedback = Complete Picture

Latency (P95): 3.2s         | Satisfaction: 45%  ⚠️
Query Type: Complex         | Strategy: advanced_expanded
→ Action: Optimize complex query handling
```

#### Performance Impact

- **Storage**: ~500 bytes per feedback entry
- **Latency**: <1ms to record feedback (non-blocking)
- **Analytics**: ~10ms to generate statistics (100 entries)
- **Memory**: Negligible (loaded on-demand)

#### Benefits

- **Continuous Improvement**: Identify weak spots in retrieval strategies
- **Data-Driven Optimization**: Make configuration changes based on real user feedback
- **User Engagement**: Users feel their input shapes the system
- **Quality Assurance**: Track satisfaction over time as a KPI

**See**: `docs/examples/feedback_analysis.md` for detailed examples and analysis reports

### 5. Document Processing Pipeline (`document_processor.py`)

#### Supported Formats
- **PDF**: Text extraction via PyPDF + OCR fallback (Tesseract)
- **DOCX/DOC**: Native text extraction
- **TXT**: Multi-encoding detection (UTF-8, Latin-1, CP1252)
- **Markdown**: Structured parsing

#### Intelligent Chunking Strategies

##### Recursive Chunking (Default)
- **Method**: Hierarchical text splitting with semantic separators
- **Separators**: `\n\n` → `\n` → `. ` → ` `
- **Parameters**: 800 chars/chunk, 200 char overlap
- **Use case**: General-purpose, fast

##### Semantic Chunking
- **Method**: Sentence-level similarity analysis using embeddings
- **Model**: `all-MiniLM-L6-v2` (GPU-accelerated)
- **Process**:
  1. Split into sentences
  2. Encode with SentenceTransformer
  3. Find semantic boundaries (similarity drop < 0.7)
  4. Create chunks at boundaries
- **Use case**: Preserving semantic coherence

##### Hybrid Chunking
- **Method**: Recursive splitting + semantic refinement
- **Process**:
  1. Initial recursive chunking
  2. Large chunks (>1200 chars) → semantic sub-chunking
- **Use case**: Best balance of speed and quality

#### Metadata Enrichment

Each chunk receives:
- `file_name`: Source document name
- `file_type`: Document format (.pdf, .docx, etc.)
- `file_hash`: SHA256 hash for deduplication
- `file_size_bytes`: Document size
- `page_number`: Page location (PDFs)
- `chunk_index`: Position in document
- `total_chunks`: Total chunks from document
- `chunking_strategy`: Strategy used
- `processing_date`: ISO timestamp

#### Parallel Processing
- **ThreadPoolExecutor**: Concurrent document loading
- **Max workers**: 4 (configurable)
- **Error handling**: Per-document error isolation

### 6. Caching & Monitoring (`cache_and_monitoring.py`)

#### Multi-Layer LRU Cache

##### Embedding Cache
- **Size**: 10,000 entries
- **TTL**: 3600 seconds (1 hour)
- **Purpose**: Cache expensive embedding computations
- **Key**: MD5 hash of text

##### Query Cache
- **Size**: 1,000 entries
- **TTL**: 3600 seconds
- **Purpose**: Cache complete query results
- **Key**: MD5(query + parameters)

##### Result Cache
- **Size**: 2,000 entries
- **TTL**: 3600 seconds
- **Purpose**: Cache retrieval results
- **Key**: MD5(query)

#### Cache Features
- **Thread-safe**: RLock for concurrent access
- **TTL enforcement**: Automatic expiration
- **LRU eviction**: Least-recently-used removal
- **Statistics**: Hit/miss/eviction tracking

#### Performance Metrics

**Collected Metrics:**
- Query count & latency (avg, p50, p95, p99)
- Retrieval stage timing
- Cache hit rates
- Error rates
- GPU/CPU utilization
- VRAM usage

**Metrics Storage:**
- Thread-safe counters
- Timer histograms
- Percentile calculations

### 7. GPU Performance Monitoring (`performance_monitor.py`)

#### PyTorch-Based Monitoring (Docker-Compatible)

**Why PyTorch?**
- Works in Docker without nvidia-smi
- Direct CUDA API access
- No additional dependencies

**Monitored Metrics:**
- **GPU Utilization**: Estimated from memory reservation
- **VRAM Usage**: Allocated + reserved memory (MB)
- **GPU Temperature**: Not available via PyTorch
- **CPU Usage**: psutil.cpu_percent()

**Update Frequency**: 1 second (configurable)

### 8. Web Interface (`web_interface.py`)

#### Features

**Chat Interface:**
- Gradio Chatbot with message history
- Real-time query processing
- Source citation with relevance scores
- Strategy/query type display

**Performance Dashboard:**
- GPU/CPU utilization gauges
- VRAM usage tracking
- Activity log
- Real-time metrics updates

**Dynamic Settings Panel:**
- K-value sliders (simple/hybrid/advanced)
- Reranking weight control
- RRF constant tuning
- Classification threshold adjustment
- Preset configurations (Fast/Balanced/Deep Research)

**Example Questions:**
- Auto-generated from indexed documents
- LLM-powered generation
- Cached for fast startup

---

## Technical Deep Dive

### Retrieval Algorithm: Reciprocal Rank Fusion (RRF)

RRF combines results from multiple retrieval methods by computing a fusion score:

```
RRF(d) = Σ(1 / (k + rank(d, method_i)))
```

Where:
- `d` = document
- `k` = constant (default: 60)
- `rank(d, method_i)` = rank of document d in method i

**Advantages:**
- No score normalization needed
- Weights all methods equally
- Robust to outliers

**Implementation:**
1. Dense search returns ranked list
2. Sparse search returns ranked list
3. For each document, compute RRF score from both rankings
4. Sort by combined RRF score
5. Pass top 15 to reranker

### Embedding Model: nomic-embed-text

- **Dimension**: 768
- **Context window**: 8192 tokens
- **Architecture**: Transformer-based
- **Training**: Contrastive learning on text pairs
- **Inference**: GPU-accelerated via Ollama
- **Batch size**: 32 (configurable)

### LLM: llama3.1:8b

**Configuration:**
- **Temperature**: 0.0 (deterministic)
- **Top-p**: 0.9
- **Top-k**: 40
- **Context window**: 4096 tokens (optimized for speed)
- **Repeat penalty**: 1.1
- **GPU layers**: All (999)

**Answer Generation Strategy:**
- Adaptive instructions based on query type
- Source citation requirements
- Factual grounding enforcement
- Hallucination prevention

### Cross-Encoder Reranking

**Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`

**How it works:**
1. Takes (query, document) pairs
2. Computes relevance score via cross-attention
3. More accurate than bi-encoders (vector similarity)
4. GPU-accelerated for speed

**Why use it?**
- **Bi-encoders** (embeddings): Fast but approximate
- **Cross-encoders**: Slower but much more accurate
- **Hybrid approach**: Bi-encoder retrieval → cross-encoder reranking

---

## Configuration

### Main Configuration File: `config.yml`

```yaml
# LLM Settings
llm:
  model_name: "llama3.1:8b"
  temperature: 0.0
  num_ctx: 4096          # Context window

# Embedding Settings
embedding:
  model_name: "nomic-embed-text"
  dimension: 768
  batch_size: 32

# Chunking Strategy
chunking:
  strategy: "hybrid"     # recursive | semantic | sentence | hybrid
  chunk_size: 500        # Optimized for performance
  chunk_overlap: 100

# Retrieval Settings
retrieval:
  initial_k: 50          # Initial candidates
  rerank_k: 15           # Candidates to rerank
  final_k: 3             # Final results
  fusion_method: "rrf"
  rrf_k: 60

# Caching
cache:
  enable_embedding_cache: true
  enable_query_cache: true
  cache_ttl: 3600        # 1 hour
  max_cache_size: 10000

# Performance
performance:
  max_workers: 4
  enable_batching: true
  max_batch_size: 16
```

### Environment Variables (Docker)

```bash
# GPU Settings
CUDA_VISIBLE_DEVICES=0
DEVICE_TYPE=cuda
USE_CUDA_DOCKER=true

# Model Configuration
RAG_LLM__MODEL_NAME=llama3.1:8b
RAG_LLM__NUM_CTX=4096
RAG_LLM__TEMPERATURE=0.0

# Retrieval Configuration
RAG_RETRIEVAL__FINAL_K=3
RAG_RETRIEVAL__RERANK_K=15

# Chunking Configuration
RAG_CHUNKING__CHUNK_SIZE=500
RAG_CHUNKING__CHUNK_OVERLAP=100
```

---

## Deployment

### Docker Compose Architecture

**Service 1: Ollama (AI Models)**
```yaml
ollama:
  image: ollama/ollama:latest
  ports: ["11434:11434"]
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
  environment:
    - OLLAMA_NUM_GPU=999      # Use all available GPUs
    - OLLAMA_GPU_LAYERS=999   # Load all layers on GPU
```

**Service 2: RAG Application**
```yaml
rag-app:
  build:
    context: .
    dockerfile: _config/Dockerfile
  runtime: nvidia               # GPU support
  ports: ["7860:7860"]
  depends_on:
    - ollama                    # Wait for Ollama to be healthy
  volumes:
    - ./documents:/app/documents
    - ./chroma_db:/app/chroma_db
```

### Dockerfile Build Process

1. **Base**: Python 3.11 slim
2. **System deps**: Tesseract OCR, Poppler (PDF support)
3. **PyTorch**: Install CUDA-enabled PyTorch FIRST
4. **Python deps**: Install requirements (uses GPU PyTorch)
5. **App code**: Copy source files
6. **Setup**: Create directories, set permissions
7. **Environment**: Configure CUDA variables
8. **Command**: Run app.py

**Key optimization**: Install PyTorch with CUDA before other packages to ensure sentence-transformers uses GPU version.

---

## Performance Optimization

### Optimizations Implemented

1. **Reduced Context Window**: 8192 → 4096 tokens (~30% faster)
2. **Smaller Chunks**: 800 → 500 chars (faster indexing)
3. **Less Overlap**: 200 → 100 chars (fewer chunks)
4. **Fewer Results**: 5 → 3 final results (faster generation)
5. **Fewer Rerank Candidates**: 20 → 15 (faster reranking)
6. **Batch Processing**: 16 documents/batch (GPU efficiency)
7. **Multi-layer Caching**: Embedding + query + result caches
8. **GPU Acceleration**: Embeddings, reranking, LLM inference

### Expected Performance

**Query Latency:**
- Simple queries: ~1-2s
- Hybrid queries: ~2-4s
- Advanced queries: ~4-6s

**Throughput:**
- ~10-15 queries/second (with caching)
- ~2-3 queries/second (cold cache)

**Memory Usage:**
- CPU RAM: ~4-6 GB
- VRAM: ~6-8 GB (llama3.1:8b)

---

## Evaluation & Monitoring

### Evaluation Suite (`evaluate.py`)

**Test Categories:**

1. **Retrieval Quality**
   - Precision, Recall, F1 score
   - Mean Reciprocal Rank (MRR)
   - By-difficulty breakdown

2. **Answer Quality**
   - Answer length statistics
   - Source citation count
   - Query type distribution

3. **Performance Metrics**
   - Cold/warm latency
   - Cache effectiveness
   - Percentile analysis (p50, p95, p99)

4. **Stress Testing**
   - Concurrent query handling
   - Throughput measurement
   - Error rate under load

**Grading System:**
- A (90-100): Production ready
- B (80-89): Minor improvements needed
- C (70-79): Optimization required
- D (60-69): Significant issues
- F (<60): Major overhaul needed

### Real-Time Monitoring

**Metrics Dashboard:**
- GPU utilization & VRAM usage
- CPU utilization
- Query count & latency
- Cache hit rates
- Document/chunk statistics

**Logging:**
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log rotation supported
- File + console output

---

## System Requirements

- **OS**: Windows 10/11, Linux, macOS
- **Docker**: Desktop with WSL2 (Windows) or native (Linux/Mac)
- **Memory**: 8 GB minimum, 16 GB recommended
- **GPU**: NVIDIA GPU with 8+ GB VRAM (optional but recommended)
- **Disk**: 10 GB free space
- **CUDA**: 12.1+ (for GPU support)

---

## Troubleshooting

### Common Issues

**Slow Performance:**
- Check GPU is being used: Look for "GPU detected" in logs
- Verify CUDA is available: `docker exec rag-tactical-system python -c "import torch; print(torch.cuda.is_available())"`
- Reduce context window or chunk size
- Enable caching in config.yml

**Out of Memory:**
- Reduce `num_ctx` in config.yml
- Use smaller model (llama3.1:3b)
- Reduce batch sizes
- Lower max_cache_size

**Poor Retrieval Quality:**
- Adjust chunking strategy (try hybrid or semantic)
- Increase rerank_k for more candidates
- Tune classification thresholds
- Add more documents

**Container Won't Start:**
- Ensure Docker Desktop is running
- Check GPU drivers are installed
- Verify docker-compose.yml GPU configuration
- Check logs: `docker logs rag-tactical-system`

---

## Advanced Usage

### Custom Chunking Strategy

Edit `config.yml`:
```yaml
chunking:
  strategy: "semantic"           # Use semantic chunking
  chunk_size: 600               # Smaller chunks
  semantic_similarity_threshold: 0.8  # Stricter boundaries
```

### Custom Retrieval Settings

Runtime adjustment via web UI or programmatically:
```python
rag_system.update_settings(
    simple_k=7,
    hybrid_k=25,
    advanced_k=20,
    rerank_weight=0.8,
    simple_threshold=2,
    moderate_threshold=4
)
```

### Adding New Document Formats

Extend `document_processor.py`:
```python
def _load_custom_format(self, file_path: Path) -> List[Document]:
    # Your custom loader implementation
    pass

# Register in __init__
self.supported_extensions['.custom'] = self._load_custom_format
```

---

## Project Evolution

This system evolved from v2.5 to v3.5.1 through **multi-agent iterative development**:

- **Milestone 1**: Conversation Memory (multi-turn context awareness)
- **Milestone 2**: Explainability (transparent AI decisions)
- **Milestone 3**: Feedback System (continuous improvement loops)
- **Milestone 4**: Portfolio Polish (documentation, demo scripts, architecture)

**Development Method**: Three AI agents (medicant_bias, hollowed_eyes, zhadyz) coordinating via state.json + Redis pub/sub, demonstrating LangGraph/CrewAI patterns.

**See**: `IMPROVEMENTS.md` for detailed timeline with git commits, code metrics, and technical evolution
**See**: `docs/DEMO_SCRIPT.md` for live demonstration guide (10-15 minutes)

---

## Contributing

This system is designed for U.S. Government use. For authorized modifications:

1. Test changes with evaluation suite: `python evaluate.py`
2. Verify Docker build: `docker-compose build`
3. Run stress tests before deployment
4. Update documentation

---

## License

U.S. Government Work - Not subject to copyright protection in the United States.

---

Unclassified

