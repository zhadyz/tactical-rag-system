# Development Setup Guide

Complete guide for setting up the Tactical RAG development environment with React frontend and FastAPI backend.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Modes](#development-modes)
- [Project Structure](#project-structure)
- [Service Architecture](#service-architecture)
- [Testing Connectivity](#testing-connectivity)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker & Docker Compose** (v20.10+)
  - [Install Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Ensure Docker has access to GPU (NVIDIA runtime required)

- **Node.js** (v18+)
  - [Install Node.js](https://nodejs.org/)
  - Verify: `node --version`

- **Python** (v3.11+)
  - [Install Python](https://www.python.org/downloads/)
  - Verify: `python --version`

- **Git**
  - [Install Git](https://git-scm.com/downloads/)

### Hardware Requirements

- **GPU**: NVIDIA GPU with CUDA support (recommended)
  - RTX 3060 or better
  - 8GB+ VRAM
  - CUDA 11.8+ drivers

- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 20GB+ free space

### NVIDIA Docker Setup (Windows)

1. Install [NVIDIA GPU Drivers](https://www.nvidia.com/download/index.aspx)
2. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
3. Verify GPU access:
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
   ```

## Quick Start

### Option 1: Full Docker Stack (Recommended for Testing)

Start all services with Docker Compose:

```bash
# Clone the repository
git clone <repository-url>
cd "Tactical RAG/V3.5"

# Start all services (Ollama, Redis, Backend, Frontend)
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Legacy Gradio: http://localhost:7860 (if using --profile legacy)
```

**Wait for initialization:**
- Ollama: ~30 seconds
- Backend: ~60 seconds (includes model loading)
- Frontend: ~10 seconds

### Option 2: Hybrid Development (Recommended for Active Development)

Run backend services in Docker, frontend and backend locally for hot reload:

```bash
# Terminal 1: Start infrastructure (Ollama + Redis)
docker-compose up ollama redis

# Terminal 2: Start backend API (local, hot reload)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 3: Start frontend (local, hot reload)
cd frontend
npm install
npm run dev

# Access the application
# Frontend: http://localhost:5173 (Vite dev server)
# Backend API: http://localhost:8000
```

### Option 3: Backend Only (Existing Setup)

Keep using the existing Gradio interface:

```bash
# Start Ollama + Redis + Gradio
docker-compose up ollama redis rag-app

# Or run Gradio locally
python _src/app.py
```

## Development Modes

### Hot Reload Development

#### Frontend Hot Reload

```bash
cd frontend
npm run dev
```

- Changes to `.tsx`, `.ts`, `.css` files reload instantly
- Vite dev server on `http://localhost:5173`
- API proxied to backend automatically

#### Backend Hot Reload

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Changes to `.py` files reload automatically
- FastAPI auto-reload enabled
- Interactive API docs at `http://localhost:8000/docs`

### Production Build Testing

Test production builds locally:

```bash
# Build and run production containers
docker-compose -f docker-compose.yml up --build

# Or build individually
docker-compose build frontend
docker-compose build backend
```

## Project Structure

```
Tactical RAG/V3.5/
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API client services
│   │   └── App.tsx          # Main app component
│   ├── Dockerfile           # Frontend container build
│   ├── nginx.conf           # Nginx configuration
│   └── package.json
│
├── backend/                  # FastAPI backend (to be created)
│   ├── app/
│   │   ├── main.py          # FastAPI app entry
│   │   ├── routers/         # API route handlers
│   │   ├── models/          # Pydantic models
│   │   └── services/        # Business logic
│   ├── Dockerfile           # Backend container build
│   └── requirements.txt
│
├── _src/                     # Existing RAG system code
│   ├── app.py               # Legacy Gradio interface
│   ├── adaptive_retrieval.py
│   ├── cache_and_monitoring.py
│   └── ...
│
├── docs/                     # Documentation
│   ├── api-contract.yaml    # OpenAPI specification
│   ├── DEVELOPMENT.md       # This file
│   └── cors-setup.md        # CORS configuration
│
├── documents/                # Indexed documents
├── chroma_db/               # Vector database
├── logs/                    # Application logs
├── docker-compose.yml       # Service orchestration
└── .env.example            # Environment template
```

## Service Architecture

### Port Mapping

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | React UI (production build) |
| Frontend Dev | 5173 | Vite dev server |
| Backend | 8000 | FastAPI REST API |
| Ollama | 11434 | LLM inference server |
| Redis | 6379 | Cache layer |
| Gradio (Legacy) | 7860 | Original Gradio UI |

### Service Dependencies

```
Frontend → Backend → Ollama
                  → Redis
                  → ChromaDB
```

- **Frontend** depends on **Backend** API
- **Backend** depends on **Ollama**, **Redis**, and **ChromaDB**
- **Ollama** is independent (base service)
- **Redis** is independent (base service)

### Health Checks

All services include health checks:

```bash
# Check all services
docker-compose ps

# Check individual service health
curl http://localhost:8000/api/health    # Backend
curl http://localhost:3000/health        # Frontend
curl http://localhost:11434/api/version  # Ollama
redis-cli -h localhost -p 6379 ping      # Redis
```

## Testing Connectivity

### 1. Test Backend Health

```bash
# Health check
curl http://localhost:8000/api/health

# Expected response:
# {
#   "status": "healthy",
#   "services": {
#     "redis": true,
#     "ollama": true,
#     "chromadb": true,
#     "gpu": true
#   }
# }
```

### 2. Test Frontend Serving

```bash
# Frontend health
curl http://localhost:3000/health

# Expected: "healthy"
```

### 3. Test API Query Endpoint

```bash
# Simple query test
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can I grow a beard?",
    "mode": "simple",
    "use_context": false
  }'

# Expected: JSON response with answer and sources
```

### 4. Test Full Stack Integration

```bash
# Run integration test script
python test_integration.py

# Or manually test in browser
# 1. Open http://localhost:3000
# 2. Enter a question
# 3. Submit and verify response
```

## Common Tasks

### Index Documents

```bash
# Using Docker
docker-compose exec backend python -m app.scripts.index_documents

# Using local Python
cd backend
python -m app.scripts.index_documents
```

### Clear Cache

```bash
# Via API
curl -X POST http://localhost:8000/api/cache/clear \
  -H "Content-Type: application/json" \
  -d '{"cache_type": "all"}'

# Via Redis CLI
redis-cli -h localhost -p 6379 FLUSHALL
```

### View Logs

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama

# Local logs
tail -f logs/rag_system.log
```

### Update Dependencies

```bash
# Frontend
cd frontend
npm install
npm update

# Backend
cd backend
pip install -r requirements.txt --upgrade
```

### Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
python test_integration.py
```

## Troubleshooting

### Frontend Issues

#### Issue: "Cannot connect to backend"

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check CORS configuration in `backend/app/main.py`
3. Verify `VITE_API_URL` environment variable

#### Issue: "Module not found"

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Backend Issues

#### Issue: "CUDA out of memory"

**Solution:**
1. Reduce batch size in config
2. Use smaller model (llama3.1:8b → llama3.1:7b)
3. Restart Ollama container

#### Issue: "Redis connection refused"

**Solution:**
```bash
# Check Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Verify connection
redis-cli -h localhost -p 6379 ping
```

#### Issue: "ChromaDB not found"

**Solution:**
```bash
# Index documents first
python backend/app/scripts/index_documents.py

# Or use existing index
docker-compose up backend
```

### Docker Issues

#### Issue: "Port already in use"

**Solution:**
```bash
# Find process using port
netstat -ano | findstr :8000  # Windows
lsof -ti:8000  # Linux/Mac

# Kill process or change port in docker-compose.yml
```

#### Issue: "GPU not accessible"

**Solution:**
1. Verify NVIDIA Docker runtime:
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
   ```
2. Update Docker Desktop settings (Enable GPU)
3. Restart Docker daemon

#### Issue: "Build failing"

**Solution:**
```bash
# Clean Docker cache
docker-compose down -v
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up
```

### Performance Issues

#### Issue: Slow query responses

**Solution:**
1. Check Redis cache hit rate: `curl http://localhost:8000/api/cache/stats`
2. Monitor GPU usage: `nvidia-smi`
3. Reduce `k` values in settings
4. Use "simple" mode instead of "adaptive"

#### Issue: High memory usage

**Solution:**
1. Limit Docker memory in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 8G
   ```
2. Clear Redis cache periodically
3. Reduce `max_cache_size` in config

## Environment Variables Reference

### Backend (.env)

```bash
# Service endpoints
OLLAMA_HOST=http://localhost:11434
REDIS_HOST=localhost
REDIS_PORT=6379

# Paths
DOCUMENTS_DIR=./documents
VECTOR_DB_DIR=./chroma_db
CHROMA_PERSIST_DIRECTORY=./chroma_db

# API settings
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# GPU settings
CUDA_VISIBLE_DEVICES=0
DEVICE_TYPE=cuda
USE_CUDA_DOCKER=true

# Application settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
NODE_ENV=development
```

## Next Steps

1. **Week 1**: Complete backend API implementation
2. **Week 2**: Build React components
3. **Week 3**: Implement state management
4. **Week 4**: Testing and deployment

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Docker Documentation](https://docs.docker.com/)
- [Vite Documentation](https://vitejs.dev/)
- [Project README](../README.md)
- [API Contract](./api-contract.yaml)
- [CORS Setup](./cors-setup.md)

## Getting Help

- Check logs: `docker-compose logs -f`
- Review health endpoints
- Consult troubleshooting section above
- Open an issue on GitHub
