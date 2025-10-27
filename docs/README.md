# ATLAS Protocol Documentation

**Production-grade technical documentation for developers**

Version: 4.0.0 | Last Updated: January 2025

---

## Quick Navigation

### 🚀 Getting Started
- [**Installation**](./getting-started/installation.mdx) - System requirements, Docker/manual setup
- [**Quick Start**](./getting-started/quickstart.mdx) - 5-minute walkthrough
- [**Configuration**](./getting-started/configuration.mdx) - Complete config.yml reference

### 📦 Deployment
- [**Docker Deployment**](./deployment/docker.mdx) - Production Docker setup
- [**Kubernetes Deployment**](./deployment/kubernetes.mdx) - K8s + Helm charts

### 🔧 Advanced
- [**Model Management**](./advanced/model-management.mdx) - Swap models, quantization, benchmarking

### 📚 API
- [**API Reference**](./api/endpoints.mdx) - Complete REST API documentation

---

## Documentation Structure

```
docs/
├── README.md                              # This file
├── getting-started/
│   ├── installation.mdx                   # System setup (Docker/manual/desktop)
│   ├── quickstart.mdx                     # 5-minute first query tutorial
│   └── configuration.mdx                  # config.yml deep dive
├── deployment/
│   ├── docker.mdx                         # Docker Compose production setup
│   └── kubernetes.mdx                     # Kubernetes + Helm deployment
├── advanced/
│   └── model-management.mdx               # Model swapping, quantization, benchmarking
└── api/
    └── endpoints.mdx                      # REST API reference
```

---

## What's Covered

### ✅ Installation Guide
- **3 installation methods**: Docker (recommended), Manual, Desktop App
- **GPU configuration**: NVIDIA setup, CUDA compatibility
- **Troubleshooting**: Common issues (OOM, GPU not detected, slow startup)
- **System requirements**: CPU/GPU/RAM recommendations
- **Environment variables**: Complete reference

### ✅ Quick Start Guide
- **5-minute tutorial**: Health check → First query → Document upload
- **Query modes explained**: Simple vs Adaptive
- **Streaming responses**: Server-Sent Events examples
- **Conversation context**: Multi-turn dialogue
- **Code examples**: Python, JavaScript, Go, cURL

### ✅ Configuration Guide
- **Complete config.yml reference**: Every parameter documented
- **Hardware-specific configs**: RTX 3060, 4090, 5080, CPU-only, M1/M2/M3
- **Performance presets**: Speed, Quality, Balanced
- **Vector store setup**: Qdrant vs ChromaDB
- **Embedding models**: bge-large-en-v1.5, MiniLM, e5-large
- **Speculative decoding**: 30-50% latency reduction

### ✅ Docker Deployment Guide
- **Multi-stage Dockerfile explained**: CUDA setup, model pre-caching
- **docker-compose.yml breakdown**: Resource allocation, networking
- **Production best practices**: Security, logging, health checks
- **Scaling strategies**: Vertical (GPU upgrade), Horizontal (load balancing)
- **Backup & recovery**: Automated backups, restore procedures
- **Monitoring**: Prometheus metrics, Grafana dashboards

### ✅ Kubernetes Deployment Guide
- **Helm chart structure**: Complete K8s deployment
- **GPU node configuration**: NVIDIA device plugin, node labeling
- **Persistent volumes**: Models, documents, Qdrant storage
- **Horizontal Pod Autoscaler**: CPU/Memory/Custom metrics
- **Ingress configuration**: NGINX, TLS, cert-manager
- **Production checklist**: Pre/post-deployment verification

### ✅ Model Management Guide
- **Supported models**: Llama 3.1/3.2, Mistral, Mixtral, Qwen, Phi
- **Quantization explained**: Q4_K_M, Q5_K_M, Q6_K, Q8_0 comparison
- **Model hot-swapping**: Zero-downtime model changes
- **Custom model integration**: Convert PyTorch → GGUF
- **Speculative decoding**: Setup and benchmarking
- **Performance vs accuracy trade-offs**: VRAM-limited scenarios

### ✅ API Reference
- **Complete endpoint documentation**: /api/query, /api/query/stream, /api/documents/upload
- **Request/response schemas**: TypeScript-style type definitions
- **Error codes**: HTTP status codes and error handling
- **Rate limiting**: 30-100 req/min depending on environment
- **Code examples**: Python, JavaScript, Go, cURL for every endpoint
- **Postman collection**: Downloadable API collection

---

## Key Features Documented

### 🚀 Performance Optimizations
- **GPU acceleration**: 80-100 tok/s (vs 4 tok/s CPU)
- **Speculative decoding**: 500ms → 300ms (1.7x speedup)
- **Model pre-caching**: 78s → 23s startup time
- **Redis caching**: L1/L2/L4 cache layers
- **Query latency**: 600-1200ms (simple mode)

### 🎯 RAG Pipeline
- **Vector store**: Qdrant (production) or ChromaDB (legacy)
- **Embeddings**: BAAI/bge-large-en-v1.5 (1024 dimensions)
- **Reranking**: LLM-based (RTX 5080) or BGE cross-encoder (RTX 4090)
- **Query modes**: Simple (fast) vs Adaptive (intelligent routing)
- **Context window**: Up to 128K tokens (Llama 3.1)

### 📊 Monitoring & Observability
- **Prometheus metrics**: Query duration, tokens/s, cache hit ratio
- **Grafana dashboards**: GPU utilization, vector store performance
- **Health checks**: Component-level status
- **Logging**: JSON structured logs, rotation, compression

### 🔒 Security & Reliability
- **Rate limiting**: Per-IP request throttling
- **Prompt injection detection**: Pattern-based security
- **Input sanitization**: XSS prevention
- **Resource limits**: OOM prevention, CPU/memory caps
- **Backup strategies**: Automated Qdrant/Redis backups

---

## For Developers

### Testing the Docs

All code examples are **copy-paste ready** and tested against:
- ATLAS Protocol v4.0.0
- Docker 24.0+
- Kubernetes 1.25+
- Python 3.11+
- Node.js 18+

### Contributing

Found an issue or want to improve the docs?

1. **Open an issue**: [GitHub Issues](https://github.com/yourusername/apollo-rag/issues)
2. **Submit a PR**: Documentation is in MDX format
3. **Discord**: Join our [developer community](https://discord.gg/apollo-rag)

---

## What's Next?

### Planned Documentation (v4.1)

- [ ] **Security Hardening Guide**: API keys, OAuth, RBAC
- [ ] **Performance Tuning**: Advanced optimizations
- [ ] **Monitoring Deep Dive**: Custom Grafana dashboards
- [ ] **Multi-Tenancy**: Isolate users/organizations
- [ ] **Hybrid Search**: BM25 + vector search tuning
- [ ] **Custom Embeddings**: Fine-tune models for your domain
- [ ] **Observability**: OpenTelemetry, Jaeger tracing

---

## Support

- 📖 **Documentation**: You're here!
- 💬 **Discord**: [discord.gg/apollo-rag](https://discord.gg/apollo-rag)
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/apollo-rag/issues)
- 📧 **Email**: support@apollo.onyxlab.ai

---

## License

Documentation licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

ATLAS Protocol code licensed under MIT License

---

**Built with ❤️ by the ATLAS Protocol team**
