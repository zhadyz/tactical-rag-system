# Tactical RAG FastAPI Backend

FastAPI backend that wraps and exposes the existing RAG engine through REST API endpoints.

## Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI app with CORS and lifespan management
│   ├── api/
│   │   ├── query.py         # Query endpoints (/api/query, /api/conversation/clear)
│   │   └── settings.py      # Settings endpoints (/api/settings)
│   ├── core/
│   │   └── rag_engine.py    # RAG Engine wrapper (imports from _src/)
│   └── models/
│       └── schemas.py       # Pydantic request/response models
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container image definition
└── test_api.py             # Comprehensive test suite
```

## Features

### Endpoints

- **GET /api/health** - Health check with component status
- **POST /api/query** - Process queries with simple or adaptive mode
- **POST /api/conversation/clear** - Clear conversation memory
- **GET /api/settings** - Get current runtime settings
- **PUT /api/settings** - Update runtime settings
- **POST /api/settings/reset** - Reset settings to defaults
- **GET /docs** - Interactive Swagger API documentation
- **GET /redoc** - ReDoc API documentation

### Query Modes

1. **Simple Mode** (Default)
   - Direct dense vector search
   - Fast and consistent (~8-15 seconds)
   - Best for most queries

2. **Adaptive Mode**
   - Automatic query classification
   - Strategy routing (simple/hybrid/advanced)
   - Best for complex questions
   - Variable response time

### Key Features

- **Conversation Memory** - Multi-turn conversations with context
- **Multi-Stage Caching** - Exact, normalized, and semantic caching (via Redis)
- **Source Attribution** - All answers include source documents with scores
- **Runtime Configuration** - Adjust retrieval parameters on-the-fly
- **GPU Support** - Optional CUDA acceleration for reranking

## Quick Start

### Prerequisites

- Python 3.11+
- Ollama running with models loaded
- Redis (for caching)
- ChromaDB vector database populated (from existing indexing)

### Option 1: Local Development

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Set environment variables
export OLLAMA_HOST=http://localhost:11434
export RAG_VECTOR_DB_DIR=../chroma_db
export RAG_DOCUMENTS_DIR=../documents
export RAG_CACHE__USE_REDIS=true
export RAG_CACHE__REDIS_HOST=localhost
export RAG_CACHE__REDIS_PORT=6379

# 3. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Test the API
python test_api.py
```

### Option 2: Docker

```bash
# 1. Build the image
docker build -t tactical-rag-backend:latest -f backend/Dockerfile .

# 2. Run the container
docker run -d \
  --name rag-backend \
  -p 8000:8000 \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -e RAG_CACHE__REDIS_HOST=redis \
  -v $(pwd)/chroma_db:/app/chroma_db \
  -v $(pwd)/documents:/app/documents \
  tactical-rag-backend:latest

# 3. Check health
curl http://localhost:8000/api/health

# 4. Test query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Can I grow a beard?","mode":"simple","use_context":false}'
```

### Option 3: Docker Compose (Recommended)

See `docker-compose.backend.yml` for full stack setup with Ollama, Redis, and backend.

## API Usage Examples

### Health Check

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "message": "All systems operational",
  "components": {
    "vectorstore": "ready",
    "llm": "ready",
    "bm25_retriever": "ready",
    "cache": "ready",
    "conversation_memory": "ready"
  }
}
```

### Simple Query

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can I grow a beard?",
    "mode": "simple",
    "use_context": false
  }'
```

Response:
```json
{
  "answer": "Yes, according to AFI 36-2903, male Airmen are authorized...",
  "sources": [
    {
      "file_name": "AFI36-2903.pdf",
      "file_type": "pdf",
      "relevance_score": 0.95,
      "excerpt": "Male Airmen are authorized to wear beards...",
      "metadata": {"page_number": 12}
    }
  ],
  "metadata": {
    "strategy_used": "simple_dense",
    "query_type": "simple",
    "mode": "simple",
    "processing_time_ms": 1250.5
  },
  "explanation": null,
  "error": false
}
```

### Adaptive Query

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the grooming standards and why are they important?",
    "mode": "adaptive",
    "use_context": true
  }'
```

### Update Settings

```bash
curl -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "simple_k": 7,
    "rerank_weight": 0.8
  }'
```

### Clear Conversation

```bash
curl -X POST http://localhost:8000/api/conversation/clear
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `RAG_VECTOR_DB_DIR` | `./chroma_db` | Vector database directory |
| `RAG_DOCUMENTS_DIR` | `./documents` | Documents directory |
| `RAG_CACHE__USE_REDIS` | `true` | Enable Redis caching |
| `RAG_CACHE__REDIS_HOST` | `multi-agent-redis` | Redis host |
| `RAG_CACHE__REDIS_PORT` | `6379` | Redis port |
| `RAG_LLM__MODEL_NAME` | `llama3.1:8b` | LLM model name |
| `RAG_EMBEDDING__MODEL_NAME` | `nomic-embed-text` | Embedding model |

### Runtime Settings (via API)

Configurable via `/api/settings`:

- `simple_k` (1-50): Results for simple queries
- `hybrid_k` (5-40): Results for hybrid queries
- `advanced_k` (5-30): Results for advanced queries
- `rerank_weight` (0.0-1.0): Reranker weight
- `rrf_constant` (1-100): RRF fusion constant
- `simple_threshold` (0-10): Simple classification threshold
- `moderate_threshold` (0-10): Moderate classification threshold

## Testing

Run the comprehensive test suite:

```bash
# Make sure backend is running first
python backend/test_api.py
```

The test suite covers:
1. Root endpoint
2. Health check
3. Simple query
4. Adaptive query
5. Get settings
6. Update settings
7. Reset settings
8. Clear conversation
9. Conversation context (follow-up questions)

## Integration with Frontend

This backend is designed to be consumed by a React frontend. Key integration points:

### Query Processing
```javascript
const response = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    question: userQuestion,
    mode: 'simple',  // or 'adaptive'
    use_context: true
  })
});
const data = await response.json();
```

### Health Monitoring
```javascript
const health = await fetch('http://localhost:8000/api/health');
const status = await health.json();
// Update UI based on status.components
```

### Settings Management
```javascript
// Get current settings
const settings = await fetch('http://localhost:8000/api/settings');

// Update settings
await fetch('http://localhost:8000/api/settings', {
  method: 'PUT',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({simple_k: 7, rerank_weight: 0.8})
});
```

## Architecture Notes

### RAG Engine Wrapper (`core/rag_engine.py`)

- **No modifications to existing code** - Only imports and wraps
- Initializes: Vectorstore, BM25, LLM, Cache, Conversation Memory
- Provides async API for FastAPI
- Manages conversation state and caching transparently

### Existing RAG Components Used

From `_src/` directory:
- `config.py` - Configuration management
- `adaptive_retrieval.py` - Core retrieval engine with GPU acceleration
- `conversation_memory.py` - Multi-turn conversation tracking
- `cache_next_gen.py` - Multi-stage caching system

### Performance Considerations

- **Caching**: Multi-stage cache dramatically reduces latency for repeated queries
- **GPU Acceleration**: Reranking uses CUDA if available
- **Async Operations**: All I/O operations are async for better concurrency
- **Connection Pooling**: HTTP clients use connection pooling

## Troubleshooting

### Backend won't start

1. Check Ollama is running: `curl http://localhost:11434/api/version`
2. Check vector database exists: `ls chroma_db/`
3. Check Redis is running: `redis-cli ping`
4. Check logs: Look for initialization errors

### Queries are slow

1. Check cache hit rate: `GET /api/health` (check Redis status)
2. Verify GPU usage: Look for "Reranker using GPU" in logs
3. Check Ollama performance: `ollama ps`

### Import errors

Make sure `_src/` directory is in the correct location relative to `backend/app/`.
The Dockerfile copies it to `/app/_src`.

## Production Deployment

### Security Considerations

1. **CORS**: Restrict `allow_origins` in production
2. **Authentication**: Add auth middleware (JWT, API keys)
3. **Rate Limiting**: Add rate limiting middleware
4. **HTTPS**: Use reverse proxy (nginx, traefik)
5. **Secrets**: Use environment variables, not hardcoded values

### Scaling

- **Horizontal**: Multiple backend instances behind load balancer
- **Redis**: Shared Redis for caching across instances
- **Ollama**: Dedicated Ollama server(s) with load balancing

### Monitoring

- **Logs**: Centralized logging (ELK, Loki)
- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry integration
- **Health Checks**: Kubernetes/Docker health checks

## License

Same as parent Tactical RAG project.

## Support

For issues or questions, contact Abdul.baril@us.af.mil
