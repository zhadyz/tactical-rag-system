# Tactical RAG: Document Intelligence System

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
![React](https://img.shields.io/badge/React-18.3-61dafb.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178c6.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Production-grade Retrieval-Augmented Generation (RAG) system** for intelligent document querying with enterprise UI, real-time streaming, and performance monitoring. Designed for offline deployment in field environments.

## 🎯 Overview

Tactical RAG enables natural language querying of large document collections using state-of-the-art RAG techniques. The system features a modern React frontend, FastAPI backend, and GPU-accelerated LLM inference via Ollama.

**Key Capabilities:**
- **Intelligent Document Q&A**: Natural language queries with source citations
- **Multi-Query Fusion**: Automatic query decomposition for comprehensive retrieval
- **Real-Time Streaming**: Token-by-token response streaming
- **Performance Analytics**: Built-in metrics dashboard
- **Offline Operation**: Fully air-gapped deployment support

---

## 🚀 Version 3.9 - Production Release

### What's New

**Enterprise UI Transformation**
- Modern React/TypeScript frontend with real-time updates
- Streaming response support with token-by-token display
- Performance metrics dashboard with query history
- Dark mode support
- Responsive document management interface

**Production Hardening**
- Error boundaries for fault isolation
- Performance tracking and analytics
- CORS configuration for multi-port access
- Production-grade Docker compose configuration
- Comprehensive logging infrastructure

**Multi-Query Fusion**
- Automatic query decomposition into sub-queries
- Parallel retrieval from multiple perspectives
- Result synthesis for comprehensive answers
- Improved recall on complex questions

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (React)                   │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │   Chat     │  │ Documents  │  │ Performance  │  │
│  │  Interface │  │ Management │  │  Dashboard   │  │
│  └────────────┘  └────────────┘  └──────────────┘  │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP/SSE
┌───────────────────────┴─────────────────────────────┐
│              Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────┐  │
│  │          RAG Engine                           │  │
│  │  ┌────────────┐  ┌────────────┐              │  │
│  │  │  Retrieval │  │    LLM     │              │  │
│  │  │   (Qdrant) │  │  (Ollama)  │              │  │
│  │  └────────────┘  └────────────┘              │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

### Prerequisites

- **Docker** & Docker Compose
- **NVIDIA GPU** with CUDA 12.1+ (recommended)
- **16GB+ RAM** (32GB recommended)
- **50GB+ Storage**

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/tactical-rag.git
cd tactical-rag

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Access the interface
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### First Time Setup

1. **Upload Documents**
   - Navigate to "Documents" tab
   - Upload PDF, TXT, or MD files
   - Click "Index Documents" to process

2. **Configure Settings**
   - Select LLM model (Qwen2.5 14B recommended)
   - Adjust temperature (0.0-1.0)
   - Enable streaming responses

3. **Start Querying**
   - Enter questions in natural language
   - View answers with source citations
   - Check performance metrics in dashboard

---

## 📊 Features

### Core Capabilities

**Document Processing**
- PDF, TXT, Markdown support
- Automatic text extraction and chunking
- Semantic embedding with BGE-M3
- Vector storage in Qdrant

**Intelligent Retrieval**
- Multi-query fusion for comprehensive recall
- Semantic search with reranking
- Source citation tracking
- Configurable chunk size and overlap

**Answer Generation**
- GPU-accelerated LLM inference
- Real-time streaming responses
- Context-aware answers
- Temperature control

### User Interface

**Chat Interface**
- Real-time streaming display
- Source citations with file references
- Query history
- Copy to clipboard

**Document Management**
- Drag-and-drop upload
- Multi-file batch processing
- Index status tracking
- Document deletion

**Performance Dashboard**
- Query timing breakdown
- Cache hit rate analytics
- Average response time
- Performance trend visualization

---

## 🛠️ Configuration

### Environment Variables

```bash
# LLM Configuration
OLLAMA_BASE_URL=http://ollama:11434
LLM_MODEL=qwen2.5:14b              # or llama3.1:8b
LLM_TEMPERATURE=0.0

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-m3

# Vector Database
VECTOR_STORE_TYPE=qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Server Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### config.yml

```yaml
retrieval:
  top_k: 5                    # Documents to retrieve
  chunk_size: 500             # Characters per chunk
  chunk_overlap: 100          # Overlap between chunks

llm:
  model: "qwen2.5:14b"
  temperature: 0.0
  max_tokens: 2048

multi_query:
  enabled: true
  num_queries: 3              # Sub-queries to generate
```

---

## 🔧 Development

### Project Structure

```
tactical-rag/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # RAG engine
│   │   └── main.py           # Application entry
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API client
│   │   └── store/            # State management
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

### Technology Stack

**Frontend**
- React 18.3 + TypeScript
- Zustand for state management
- Tailwind CSS for styling
- Server-Sent Events for streaming

**Backend**
- FastAPI 0.115+
- LangChain for RAG orchestration
- Qdrant for vector storage
- Ollama for LLM inference

**Infrastructure**
- Docker + Docker Compose
- NVIDIA Container Toolkit
- Redis (optional caching)

---

## 📈 Performance

### Benchmarks

**Query Performance**
- Cold query: ~8-15 seconds
- Warm query (cached): < 1 second
- Streaming latency: ~50ms first token

**Throughput**
- Concurrent users: 10+
- Documents: 1000+ PDFs
- Index time: ~2s per document

**Resource Usage**
- GPU VRAM: 8-12GB (Qwen2.5 14B)
- System RAM: 16GB minimum
- Storage: ~500MB per 1000 docs

---

## 🚢 Deployment

### Production Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.production.yml up -d

# Monitor logs
docker-compose logs -f backend

# Check health
curl http://localhost:8000/api/health
```

### Scaling Considerations

- **GPU**: Required for LLM inference
- **Vector DB**: Qdrant scales to billions of vectors
- **Caching**: Redis recommended for multi-user deployments
- **Load Balancing**: Use nginx for frontend distribution

---

## 🔒 Security

- **Offline Operation**: No external API calls
- **Local Processing**: All data stays on-premises
- **CORS Protection**: Configurable origins
- **Input Validation**: Sanitized user inputs
- **File Upload Limits**: Configurable size restrictions

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with tests

---

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

## 🙏 Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - RAG orchestration
- [Ollama](https://ollama.ai/) - Local LLM inference
- [Qdrant](https://qdrant.tech/) - Vector database
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework
