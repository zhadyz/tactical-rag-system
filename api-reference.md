# API Reference

Complete reference for Apollo's REST API endpoints.

## Base URL

```
http://localhost:8000/api
```

## Authentication

**Development**: No authentication required

**Production**: Add `X-API-Key` header:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/health
```

---

## Health & Status

### GET /health

Health check endpoint.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "4.1.0",
  "gpu_available": true,
  "models_loaded": true,
  "cache_connected": true,
  "vector_db_connected": true
}
```

---

## Query Operations

### POST /query

Submit a question and receive an answer with sources.

**Request Body**:
```json
{
  "question": "Your question here",
  "mode": "simple",  // "simple" | "adaptive"
  "use_context": true,
  "max_tokens": 2048
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | User question (max 10,000 chars) |
| `mode` | string | No | Query strategy: "simple" (default) or "adaptive" |
| `use_context` | boolean | No | Include retrieved context (default: true) |
| `max_tokens` | integer | No | Max LLM response length (default: 2048) |

**Response** (200 OK):
```json
{
  "answer": "According to the documents...",
  "sources": [
    {
      "file_name": "document.pdf",
      "chunk_id": "chunk_42",
      "relevance_score": 0.95,
      "page": 12,
      "text": "Source text excerpt..."
    }
  ],
  "metadata": {
    "processing_time_ms": 1234.5,
    "cache_hit": false,
    "strategy_used": "hybrid_search",
    "llm_tokens": 150,
    "llm_speed_tokens_per_sec": 63.8
  },
  "confidence": 0.89
}
```

**Error Responses**:

- `400 Bad Request`: Invalid input
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Processing failed

**Example**:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is GPU acceleration?",
    "mode": "simple"
  }'
```

### GET /query/stream

Stream query response using Server-Sent Events.

**Query Parameters**: Same as POST /query

**Response Stream** (SSE):
```
data: {"type":"token","content":"According"}
data: {"type":"token","content":" to"}
data: {"type":"sources","data":[{...}]}
data: {"type":"done","metadata":{...}}
```

**Event Types**:

| Type | Description |
|------|-------------|
| `token` | Individual LLM token |
| `sources` | Retrieved source documents |
| `done` | Processing complete with metadata |
| `error` | Error occurred |

**Example**:
```bash
curl -N http://localhost:8000/api/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"Test query","mode":"simple"}'
```

---

## Document Management

### POST /documents/upload

Upload a document for indexing.

**Content-Type**: `multipart/form-data`

**Form Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary | Yes | PDF, DOCX, or TXT file (max 50MB) |

**Response** (200 OK):
```json
{
  "file_name": "document.pdf",
  "chunks_created": 42,
  "processing_time_ms": 3456.7,
  "status": "indexed successfully"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/document.pdf"
```

### GET /documents/list

List all indexed documents.

**Response** (200 OK):
```json
{
  "documents": [
    {
      "file_name": "document.pdf",
      "chunks": 42,
      "indexed_at": "2025-10-26T12:00:00Z"
    }
  ],
  "total_documents": 1,
  "total_chunks": 42
}
```

### POST /documents/reindex

Trigger full database re-indexing from documents directory.

**Response** (200 OK):
```json
{
  "files_processed": 10,
  "total_chunks": 420,
  "processing_time_ms": 12345.6
}
```

---

## Cache Management

### GET /cache/metrics

Get cache performance metrics.

**Response** (200 OK):
```json
{
  "l1_hits": 1000,
  "l1_misses": 500,
  "l2_hits": 200,
  "l2_misses": 300,
  "l3_hits": 150,
  "l3_misses": 150,
  "l4_hits": 4500,
  "l4_misses": 500,
  "l5_hits": 3000,
  "l5_misses": 2000,
  "total_hit_rate": 0.75,
  "total_queries": 5000
}
```

### POST /cache/clear

Clear all caches (L1-L5).

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `layer` | string | No | Specific layer to clear: "L1", "L2", "L3", "L4", "L5", or "all" (default) |

**Response** (200 OK):
```json
{
  "status": "success",
  "caches_cleared": ["L1", "L2", "L3", "L4", "L5"]
}
```

---

## Settings & Configuration

### GET /settings

Get current system configuration.

**Response** (200 OK):
```json
{
  "llm_backend": "llamacpp",
  "model_name": "llama-3.1-8b-instruct.Q5_K_M.gguf",
  "embedding_model": "BAAI/bge-large-en-v1.5",
  "gpu_layers": 35,
  "cache_enabled": true
}
```

### POST /settings/model

Switch LLM model (hotswap).

**Request Body**:
```json
{
  "model_path": "/models/qwen2.5-14b-instruct-q5_k_m.gguf",
  "n_gpu_layers": 40
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "model_loaded": "qwen2.5-14b-instruct-q5_k_m.gguf",
  "gpu_layers": 40
}
```

---

## Rate Limiting

**Limits**:
- Query endpoint: 30 requests/minute per IP
- Global: 100 requests/minute

**Headers**:
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1730000000
```

**429 Response**:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 401 | Unauthorized (invalid API key) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

**Error Response Format**:
```json
{
  "error": "Error message",
  "detail": "Detailed explanation",
  "code": "ERROR_CODE"
}
```

---

[← Back to Architecture](architecture.md) | [Next: Configuration →](configuration.md)
