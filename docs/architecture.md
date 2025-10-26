# Apollo Architecture

This document provides a detailed overview of Apollo's system architecture, components, and data flow.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                      │
│  ┌────────────────┐              ┌─────────────────┐       │
│  │ Tauri Desktop  │              │  Web Browser    │       │
│  │  (React 19)    │──────────────│   (Optional)    │       │
│  └────────┬───────┘              └────────┬────────┘       │
└───────────┼─────────────────────────────────┼──────────────┘
            │                                 │
┌───────────┼─────────────────────────────────┼──────────────┐
│           │         APPLICATION LAYER       │              │
│           ▼                                 ▼              │
│  ┌──────────────────────────────────────────────────┐     │
│  │       FastAPI Backend (Port 8000)                │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │     │
│  │  │Query API │  │Documents │  │Settings  │       │     │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘       │     │
│  │       └─────────────┼─────────────┘             │     │
│  │                     ▼                            │     │
│  │  ┌────────────────────────────────────────┐     │     │
│  │  │        RAG Engine (Core Logic)         │     │     │
│  │  │  ┌──────────────┐  ┌────────────────┐  │     │     │
│  │  │  │ Classifier   │  │ Multi-Layer    │  │     │     │
│  │  │  │              │  │ Cache (L1-L5)  │  │     │     │
│  │  │  └──────────────┘  └────────────────┘  │     │     │
│  │  └────────────────────────────────────────┘     │     │
│  └──────────────────────────────────────────────────┘     │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────┼───────────────────────────────┐
│                   DATA & INFERENCE LAYER                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Qdrant   │  │  Redis   │  │Embedding │  │   LLM    │  │
│  │ Vector   │  │  Cache   │  │ Service  │  │  Engine  │  │
│  │   DB     │  │          │  │(BGE-1024)│  │(Llama3.1)│  │
│  │ (6333)   │  │ (6379)   │  │  (GPU)   │  │  (GPU)   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└────────────────────────────────────────────────────────────┘
```

## Component Overview

### Presentation Layer

#### Tauri Desktop Application

**Technology**: React 19 + TypeScript + Tauri v2.9

**Responsibilities**:
- User interface rendering
- Local state management (Zustand)
- WebSocket connection to backend
- File upload handling
- Settings persistence

**Performance**: ~100MB RAM footprint

#### Web Browser (Optional)

**Technology**: Standard modern browser (Chrome, Firefox, Safari)

**Use Case**: Lightweight access without desktop app installation

**Access**: `http://localhost:8000` (when backend is running)

### Application Layer

#### FastAPI Backend

**Technology**: Python 3.11 + FastAPI + Uvicorn

**Port**: 8000

**Key Features**:
- Async I/O for high throughput (30-40 req/s)
- Automatic OpenAPI documentation
- CORS middleware for web access
- Rate limiting (30 req/min per IP)
- Input sanitization and validation

**API Endpoints**:
- `/api/health` - Health check
- `/api/query` - Query processing
- `/api/query/stream` - Streaming responses (SSE)
- `/api/documents/*` - Document management
- `/api/cache/*` - Cache management
- `/api/settings/*` - Configuration

#### RAG Engine

**Location**: `backend/app/core/rag_engine.py`

**Core Functionality**:

1. **Query Classification**
   - Analyzes query complexity
   - Routes to appropriate strategy (simple/hybrid/adaptive)

2. **Multi-Layer Caching** (L1-L5)
   - L1: Exact query match (in-memory)
   - L2: Normalized query (in-memory)
   - L3: Semantic similarity (Redis)
   - L4: Embedding vectors (Redis)
   - L5: LLM results (Redis)

3. **Retrieval Pipeline**
   - Embedding generation
   - Hybrid search (dense + sparse)
   - Reciprocal Rank Fusion
   - Cross-encoder reranking

4. **LLM Integration**
   - Context assembly
   - Prompt engineering
   - GPU-accelerated inference

### Data & Inference Layer

#### Qdrant Vector Database

**Version**: 1.8.0

**Port**: 6333 (HTTP), 6334 (gRPC)

**Configuration**:
```yaml
Storage: Persistent (data/qdrant)
Collection: documents
Vector Dimension: 1024
Index Type: HNSW (M=16, ef_construct=128)
```

**Features**:
- **Hybrid Search**: Dense (semantic) + Sparse (BM25)
- **HNSW Indexing**: Fast approximate nearest neighbor search
- **Prefetch Fusion**: Reciprocal Rank Fusion for result merging
- **In-Memory Payload**: Fast metadata retrieval

**Performance**: 3-5ms search latency

#### Redis Cache

**Version**: 7.2-alpine

**Port**: 6379

**Configuration**:
```yaml
Max Memory: 8GB
Eviction Policy: allkeys-lru
Persistence: RDB snapshots
```

**Cache Layers**:

| Layer | Storage | Purpose | TTL |
|-------|---------|---------|-----|
| L3 | Redis Hash | Semantic similarity | 1 hour |
| L4 | Redis Hash | Embedding vectors | 24 hours |
| L5 | Redis String | LLM results | 1 hour |

**Performance**: <1ms for L4/L5 lookups

#### Embedding Service

**Model**: BAAI/bge-large-en-v1.5

**Dimensions**: 1024

**Technology**: HuggingFace Transformers + GPU

**Configuration**:
```yaml
Batch Size: 64 (16GB VRAM)
Device: CUDA
Precision: FP16
```

**Performance**:
- Single embedding: 20-30ms
- Batch (64): 25ms average per item
- Throughput: 2K-3K documents/second

#### LLM Engine

**Backend**: llama.cpp with CUDA support

**Models**:
- **Llama 3.1 8B Instruct** (default): 5.4GB, 63.8 tok/s
- **Qwen 2.5 14B Instruct** (optional): 8.9GB, 45-50 tok/s

**Configuration**:
```yaml
GPU Layers: 35 (full offload at 16GB VRAM)
Context Window: 8192 tokens
Batch Size: 512
Temperature: 0.0 (deterministic)
```

**Performance**:
- Inference Speed: 63.8 tokens/second (GPU)
- First Token Latency: 50-100ms
- Memory Usage: 6GB VRAM (Llama 8B), 10GB VRAM (Qwen 14B)

## Data Flow

### Query Processing Pipeline

```
1. User Query Input
   │
   ├─> Input Validation & Sanitization
   │
   ├─> Cache Check (L1 → L2 → L3)
   │   └─> HIT? → Return cached result (60-85% of queries)
   │   └─> MISS? → Continue
   │
   ├─> Embedding Generation (25ms)
   │   └─> Query: "Can I grow a beard?"
   │   └─> Vector: [1024-dim embedding]
   │   └─> Cache in L4
   │
   ├─> Hybrid Vector Search (4ms)
   │   ├─> Dense Search (Semantic): Top 20 candidates
   │   ├─> Sparse Search (BM25 Keywords): Top 20 candidates
   │   └─> Reciprocal Rank Fusion → Top 30
   │
   ├─> Cross-Encoder Reranking (820ms)
   │   └─> Rerank 30 → Select Top 8 most relevant
   │
   ├─> LLM Answer Generation (650ms)
   │   ├─> Context Assembly (8 sources)
   │   ├─> Prompt Engineering
   │   └─> GPU Inference: 63.8 tokens/second
   │
   └─> Response Caching (L5)
       └─> Store for 1 hour
       └─> Return to user

Total Latency: 1.2-2.0 seconds (P50-P95)
```

### Document Ingestion Pipeline

```
1. Document Upload (PDF/DOCX/TXT)
   │
   ├─> File Validation (size, format)
   │
   ├─> Text Extraction
   │   ├─> PDF: PyPDF2
   │   ├─> DOCX: python-docx
   │   └─> TXT: Direct read
   │
   ├─> Chunking (SentenceTransformer)
   │   └─> Max Chunk Size: 512 tokens
   │   └─> Overlap: 50 tokens
   │
   ├─> Embedding Generation (GPU batch)
   │   └─> Batch Size: 64 chunks
   │   └─> Time: ~200ms per batch
   │
   ├─> Qdrant Upload
   │   └─> Create points with dense vectors
   │   └─> Add sparse vectors (BM25)
   │   └─> Attach metadata (filename, page, chunk_id)
   │
   └─> Index Status Update
       └─> Total indexed documents
       └─> Total chunks
```

## Communication Patterns

### Frontend ↔ Backend

**Protocol**: HTTP/REST + WebSocket (for streaming)

**Request Flow**:
```
Desktop App → HTTP POST → FastAPI → RAG Engine → Response
```

**Streaming Flow** (SSE):
```
Desktop App → HTTP GET (stream) → FastAPI → Generator → Tokens → Client
```

### Backend ↔ Qdrant

**Protocol**: HTTP (REST API)

**Operations**:
- `POST /collections/{name}/points/search` - Hybrid search
- `POST /collections/{name}/points` - Insert vectors
- `GET /collections/{name}` - Collection info

### Backend ↔ Redis

**Protocol**: Redis Protocol (TCP)

**Client**: redis-py with connection pooling

**Operations**:
- `GET/SET` - L5 result caching
- `HGET/HSET` - L3/L4 embedding caching
- `EXPIRE` - TTL management

### Backend ↔ GPU

**LLM Inference**: Direct Python bindings (llama-cpp-python)

**Embeddings**: HuggingFace Transformers with CUDA backend

## Scalability Considerations

### Horizontal Scaling

Apollo can be scaled horizontally by:

1. **Load Balancer** in front of multiple FastAPI instances
2. **Shared Redis** for distributed caching
3. **Shared Qdrant** cluster for vector storage
4. **GPU Node Pool** for LLM inference

### Vertical Scaling

Performance scales linearly with:

- **More VRAM**: Larger models, more GPU layers
- **More RAM**: Larger vector databases, more in-memory cache
- **Faster GPU**: Higher tok/s inference speed
- **More CPU Cores**: Faster parallel embedding generation

### Current Limits

| Resource | Limit | Reason |
|----------|-------|--------|
| Documents | 100K | Qdrant HNSW performance |
| Concurrent Queries | 40 req/s | FastAPI async workers |
| Max Query Length | 10K chars | Input validation |
| Document Size | 50MB | Upload timeout |

## Security Architecture

### Input Validation

- **Query Sanitization**: Remove null bytes, control characters
- **Length Limits**: Max 10,000 characters
- **Content Filtering**: Prompt injection detection

### Network Security

- **Internal Only**: Redis (6379), Qdrant (6333) not exposed
- **API Rate Limiting**: 30 req/min per IP
- **CORS Configuration**: Restrict origins in production

### Data Security

- **Local Storage**: All data stored on-premise
- **No Telemetry**: Zero external API calls
- **Encrypted At Rest**: OS-level disk encryption recommended

---

[← Back to Getting Started](getting-started.md) | [Next: API Reference →](api-reference.md)
