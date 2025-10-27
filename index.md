# Apollo Documentation

Welcome to **Apollo** - the Enterprise Document Intelligence Platform with GPU-Accelerated RAG.

## What is Apollo?

Apollo is a production-grade, offline-capable Retrieval Augmented Generation (RAG) system that delivers **15.6x faster inference** through GPU acceleration. Built for enterprise document intelligence, Apollo combines state-of-the-art vector search, hybrid retrieval, multi-layer caching, and local LLM inference.

## Key Features

- 🚀 **GPU-Accelerated**: 63.8 tokens/second with CUDA-optimized llama.cpp
- 🧠 **Dual LLM Support**: Hotswappable between Qwen 2.5 14B and Llama 3.1 8B
- ⚡ **Redis Caching**: Sub-millisecond cached responses (60-85% hit rate)
- 🎯 **Adaptive Retrieval**: Cross-encoder reranking for precision
- 💎 **Enterprise Vector DB**: Qdrant for scalable semantic search
- 🖥️ **Desktop-First**: Tauri-based native application
- 🔒 **Fully Offline**: No internet required for operation

## Quick Links

- **[Getting Started](getting-started.md)** - Installation and first steps
- **[Architecture](architecture.md)** - System design and components
- **[API Reference](api-reference.md)** - Complete API documentation
- **[Configuration](configuration.md)** - Settings and tuning
- **[Performance](performance.md)** - Benchmarks and optimization
- **[Model Management](model-management.md)** - LLM hotswapping guide
- **[Deployment](deployment.md)** - Production deployment
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## Performance Overview

| Metric | Value |
|--------|-------|
| LLM Inference Speed | 63.8 tok/s (GPU) |
| Query Latency (P95) | 2.0s |
| Cache Hit Rate | 60-85% |
| Vector Search | 3-5ms |
| Document Capacity | 10K-100K |

## System Requirements

### Hardware (Production)
- GPU: NVIDIA RTX 4080/5080 (16GB+ VRAM)
- CPU: AMD Ryzen 9800X3D or Intel i9-14900K
- RAM: 64GB+ DDR5
- Storage: 500GB+ NVMe SSD

### Software
- Docker Desktop 24.0+
- NVIDIA Driver 571.86+
- NVIDIA Container Toolkit 1.14.0+
- Windows 11 Pro or Ubuntu 22.04 LTS

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/apollo.git
cd apollo

# 2. Download model
wget -P ./models https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q5_K_M.gguf

# 3. Start services
docker compose -f backend/docker-compose.atlas.yml up -d

# 4. Verify
curl http://localhost:8000/api/health
```

## Architecture Overview

```
Presentation Layer (Tauri Desktop / Web)
           ↓
Application Layer (FastAPI + RAG Engine)
           ↓
Data Layer (Qdrant + Redis + GPU LLM)
```

## Support

- **GitHub**: [Issues](https://github.com/yourusername/apollo/issues) | [Discussions](https://github.com/yourusername/apollo/discussions)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

**Apollo v4.1** - Built with ⚡ by the Apollo Development Team
