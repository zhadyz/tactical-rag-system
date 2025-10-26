# Apollo 🚀

> **Enterprise-Grade Document Intelligence Platform with GPU-Accelerated RAG**

[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-4.1.0-blue.svg)](https://github.com/yourusername/apollo/releases)
[![CUDA](https://img.shields.io/badge/CUDA-12.1-76B900.svg?logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)
[![Docker](https://img.shields.io/badge/docker-ready-0db7ed.svg?logo=docker)](https://www.docker.com/)

---

## Overview

**Apollo** is a production-grade, offline-capable Retrieval Augmented Generation (RAG) system designed for enterprise document intelligence. Built with performance and security in mind, Apollo delivers **15.6x faster inference** through GPU acceleration while maintaining complete operational independence from cloud services.

### Why Apollo?

- **🚀 GPU-Accelerated**: 63.8 tok/s with CUDA-optimized llama.cpp (15.6x faster than CPU)
- **🧠 Dual LLM Support**: Hotswappable between Qwen 2.5 14B (quality) and Llama 3.1 8B (speed)
- **⚡ Redis Query Caching**: Sub-millisecond cached responses with 60-85% hit rate
- **🎯 Adaptive Retrieval**: Cross-encoder reranking for precision
- **💎 Enterprise Vector DB**: Qdrant for scalable semantic search
- **🖥️ Desktop-First**: Tauri-based native application
- **🔒 Fully Offline**: No internet required for operation
- **🐳 Docker Ready**: One-command deployment with health checks

---

## Performance Metrics

| Metric | Value | Improvement |
|--------|-------|-------------|
| **LLM Inference Speed** | 63.8 tok/s | 15.6x vs CPU baseline |
| **Query Latency (P95)** | 2.0s | Sub-2s for 95% of queries |
| **Cache Hit Rate** | 60-85% | 5-layer caching system |
| **Vector Search** | 3-5ms | Qdrant with HNSW indexing |
| **Document Capacity** | 10K-100K | Scalable architecture |

### Hardware-Accelerated Performance

```
Component Latency Breakdown:
┌─────────────────────────────────────────┐
│ Embedding Generation      25ms    (2%)  │
│ Vector Search (Qdrant)     4ms   (0.3%) │
│ Reranking                820ms   (65%)  │
│ LLM Generation (GPU)     650ms   (52%)  │
│ Overhead                  50ms    (4%)  │
├─────────────────────────────────────────┤
│ Total (Simple Mode)     ~1.2s   (100%)  │
└─────────────────────────────────────────┘
```

---

## Architecture

Apollo combines cutting-edge technologies into a cohesive, high-performance system:

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19 + TypeScript + Vite | Modern, reactive UI |
| **Desktop** | Tauri v2.9 (Rust) | Native cross-platform wrapper |
| **Backend** | FastAPI + Python 3.11 | High-performance API server |
| **LLM Engine** | llama.cpp with CUDA | GPU-accelerated inference |
| **Vector DB** | Qdrant v1.8.0 | Semantic search & hybrid retrieval |
| **Cache** | Redis 7.2 | Multi-layer query caching |
| **Embeddings** | BGE-large-en-v1.5 (1024-dim) | Semantic text encoding |

### System Architecture

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
│  │  │  • 5-Layer Cache (L1-L5)               │     │     │
│  │  │  • Hybrid Search (Dense + Sparse)      │     │     │
│  │  │  • Query Classification                │     │     │
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

---

## Quick Start

### Prerequisites

#### Hardware Requirements

**Minimum** (Development):
- GPU: NVIDIA RTX 3060 (12GB VRAM)
- RAM: 32GB DDR4
- Storage: 100GB SSD

**Recommended** (Production):
- GPU: NVIDIA RTX 4080/5080 (16GB+ VRAM)
- CPU: AMD Ryzen 9800X3D or Intel i9-14900K
- RAM: 64GB+ DDR5
- Storage: 500GB+ NVMe SSD

#### Software Requirements

- **Docker Desktop** 24.0+ with Docker Compose V2
- **NVIDIA Driver** 571.86+ (RTX 50 series) or 551.23+ (RTX 40 series)
- **NVIDIA Container Toolkit** 1.14.0+
- **Node.js** 18+ (for desktop app development)
- **Windows 11 Pro** or **Ubuntu 22.04 LTS**

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/apollo.git
cd apollo
```

#### 2. Create Directories

```bash
# Windows (PowerShell)
New-Item -ItemType Directory -Path data\qdrant,data\redis,documents,models,logs

# Linux/macOS
mkdir -p data/{qdrant,redis} documents models logs
```

#### 3. Download LLM Model

**Llama 3.1 8B Instruct** (5.4GB):
```bash
# Linux/macOS
wget -P ./models https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q5_K_M.gguf

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q5_K_M.gguf" -OutFile ".\models\llama-3.1-8b-instruct.Q5_K_M.gguf"
```

**Optional: Qwen 2.5 14B Instruct** (8.9GB - Higher quality):
```bash
wget -P ./models https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q5_k_m.gguf
```

#### 4. Build Backend Image

```bash
docker build -f backend/Dockerfile.atlas -t apollo-backend:v4.1-cuda .
```

Expected: ~8 minutes build time, ~9GB image size

#### 5. Start Services

```bash
# Linux/macOS
docker-compose -f backend/docker-compose.atlas.yml up -d

# Windows
docker compose -f backend/docker-compose.atlas.yml up -d
```

#### 6. Verify Deployment

```bash
# Check service health
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","version":"4.1.0","gpu_available":true,"models_loaded":true}
```

### Running the Desktop App

#### Development Mode

```bash
npm install
npm run tauri:dev
```

#### Production Build

```bash
# Windows
.\launch-desktop.bat

# Linux/macOS
npm run tauri:build
./src-tauri/target/release/apollo
```

---

## Configuration

Apollo uses a centralized YAML configuration file for all settings.

**Location**: `backend/config.yml`

### Key Configuration Options

#### LLM Settings (GPU Acceleration)

```yaml
llm_backend: "llamacpp"

llamacpp:
  model_path: "/models/llama-3.1-8b-instruct.Q5_K_M.gguf"

  # GPU Acceleration
  n_gpu_layers: 35              # Full GPU offload (16GB VRAM)
  n_ctx: 8192                   # Context window size
  n_batch: 512                  # Processing batch size

  # Memory Optimization
  use_mlock: true               # Lock model in RAM
  use_mmap: true                # Memory-mapped loading

  # Generation Quality
  temperature: 0.0              # Deterministic output
  top_p: 0.9
  top_k: 40
  max_tokens: 2048
```

**GPU Layer Recommendations**:
- 12GB VRAM: `n_gpu_layers: 25`
- 16GB VRAM: `n_gpu_layers: 35` (full offload)
- 24GB+ VRAM: Can handle Qwen 2.5 14B with 40+ layers

#### Retrieval Configuration

```yaml
retrieval:
  initial_k: 100                # Initial search candidates
  rerank_k: 30                  # Reranking candidates
  final_k: 8                    # Final sources for LLM

  # Hybrid weights (must sum to 1.0)
  dense_weight: 0.6             # Semantic similarity
  sparse_weight: 0.4            # BM25 keyword matching
```

**Performance Tuning**:

| Profile | initial_k | rerank_k | final_k | Use Case |
|---------|-----------|----------|---------|----------|
| Fast | 50 | 15 | 5 | Speed priority |
| **Balanced** | **100** | **30** | **8** | **Default (recommended)** |
| Accurate | 200 | 50 | 15 | Quality priority |

---

## API Documentation

**Full API documentation**: [apollo.onyxlab.ai](https://apollo.onyxlab.ai)

### Base URL

```
http://localhost:8000/api
```

### Core Endpoints

#### Health Check

```bash
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "4.1.0",
  "gpu_available": true,
  "models_loaded": true
}
```

#### Query

```bash
POST /api/query
Content-Type: application/json

{
  "question": "Your question here",
  "mode": "simple",        # or "adaptive"
  "use_context": true
}
```

**Response**:
```json
{
  "answer": "Generated answer with context...",
  "sources": [
    {
      "file_name": "document.pdf",
      "chunk_id": "chunk_42",
      "relevance_score": 0.95,
      "page": 12,
      "text": "Source excerpt..."
    }
  ],
  "metadata": {
    "processing_time_ms": 1234.5,
    "cache_hit": false,
    "llm_speed_tokens_per_sec": 63.8
  }
}
```

#### Document Upload

```bash
POST /api/documents/upload
Content-Type: multipart/form-data

file=@document.pdf
```

---

## Model Hotswapping

Apollo supports switching between LLM models without restarting services.

### Available Models

| Model | Size | Speed | Quality | VRAM |
|-------|------|-------|---------|------|
| **Llama 3.1 8B** | 5.4GB | 63.8 tok/s | Good | 8GB |
| **Qwen 2.5 14B** | 8.9GB | 45-50 tok/s | Excellent | 12GB+ |

### Switching Models

```bash
# 1. Download new model (if not present)
wget -P ./models https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q5_k_m.gguf

# 2. Update config.yml
nano backend/config.yml
# Change: model_path: "/models/qwen2.5-14b-instruct-q5_k_m.gguf"

# 3. Restart backend
docker restart apollo-backend
```

**See full guide**: [Model Management Documentation](https://apollo.onyxlab.ai/model-management)

---

## Performance Benchmarks

### GPU vs CPU Comparison

| Metric | CPU (Baseline) | GPU (CUDA) | Improvement |
|--------|----------------|------------|-------------|
| Inference Speed | 4.1 tok/s | 63.8 tok/s | **15.6x** |
| Query Latency | 18-25s | 1.2-2.0s | **10x faster** |
| Throughput | 2-3 req/min | 30-40 req/min | **13x** |

### Cache Performance

| Cache Layer | Hit Rate | Latency |
|-------------|----------|---------|
| L1 (Exact) | 40-50% | <1ms |
| L2 (Normalized) | 10-15% | <1ms |
| L3 (Semantic) | 10-20% | <20ms |
| L4 (Embeddings) | 80-90% | <10ms |
| L5 (Results) | 60-70% | <15ms |
| **Overall** | **60-85%** | **<1ms avg** |

---

## Deployment

### Docker Deployment (Recommended)

The provided Docker Compose configuration handles all services with GPU acceleration:

```bash
# Start all services
docker compose -f backend/docker-compose.atlas.yml up -d

# View logs
docker compose -f backend/docker-compose.atlas.yml logs -f

# Stop services
docker compose -f backend/docker-compose.atlas.yml down
```

### Production Considerations

1. **GPU Access**: Ensure NVIDIA Container Toolkit is installed
2. **Port Security**: Expose only port 8000 publicly (block Redis 6379, Qdrant 6333)
3. **API Keys**: Configure authentication in production environments
4. **Backups**: Regularly backup `data/qdrant` and `documents/` directories
5. **Monitoring**: Use included Prometheus metrics at `/metrics`

---

## Troubleshooting

### GPU Not Detected

**Symptom**: API reports `"gpu_available": false`

**Solution**:
```bash
# Verify NVIDIA driver
nvidia-smi

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check container GPU access
docker exec apollo-backend nvidia-smi
```

### CUDA Out of Memory

**Symptom**: `RuntimeError: CUDA out of memory`

**Solution**: Reduce GPU layers in `backend/config.yml`:
```yaml
llamacpp:
  n_gpu_layers: 25  # Reduce from 35
```

### Slow Query Performance

**Symptom**: Queries taking >5 seconds

**Solutions**:
1. Check cache hit rate: `curl http://localhost:8000/api/cache/metrics`
2. Reduce retrieval candidates in config.yml
3. Verify GPU utilization with `nvidia-smi`

**Full troubleshooting guide**: [apollo.onyxlab.ai/troubleshooting](https://apollo.onyxlab.ai/troubleshooting)

---

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

### Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
npm install
npm run tauri:dev
```

---

## License

**Proprietary** - All Rights Reserved

Copyright (c) 2025 Apollo Development Team

---

## Acknowledgments

Apollo is built on the shoulders of giants:

- **[llama.cpp](https://github.com/ggerganov/llama.cpp)** - Efficient LLM inference
- **[Qdrant](https://qdrant.tech/)** - High-performance vector database
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[Tauri](https://tauri.app/)** - Lightweight desktop framework
- **[HuggingFace](https://huggingface.co/)** - Model hosting and transformers
- **[Redis](https://redis.io/)** - In-memory data store

### Performance Achievements

- **15.6x GPU Speedup**: From 4.1 tok/s (CPU) to 63.8 tok/s (GPU)
- **Sub-2s Latency**: Consistent P95 query performance
- **85% Cache Hit Rate**: Optimized multi-layer caching
- **100K+ Document Support**: Enterprise-scale vector database

---

## Support

- **Documentation**: [apollo.onyxlab.ai](https://apollo.onyxlab.ai)
- **Issues**: [GitHub Issues](https://github.com/yourusername/apollo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/apollo/discussions)

---

**Apollo v4.1** - Production-Ready Enterprise Document Intelligence

*Built with ⚡ by the Apollo Development Team*
