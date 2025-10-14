# Project Structure Overview

## Directory Tree

```
Tactical RAG/V3.5/
│
├── frontend/                          # React Frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── components/               # Reusable UI components
│   │   ├── pages/                    # Page components
│   │   ├── services/                 # API client services
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── context/                  # React context providers
│   │   ├── types/                    # TypeScript type definitions
│   │   ├── utils/                    # Helper functions
│   │   ├── App.tsx                   # Root component
│   │   └── main.tsx                  # Entry point
│   ├── public/                       # Static assets
│   ├── Dockerfile                    # Frontend container build
│   ├── nginx.conf                    # Nginx web server config
│   ├── package.json                  # Node dependencies
│   ├── vite.config.ts               # Vite build configuration
│   └── tsconfig.json                # TypeScript configuration
│
├── backend/                           # FastAPI Backend
│   ├── app/
│   │   ├── routers/                  # API route handlers
│   │   │   ├── health.py            # Health check endpoints
│   │   │   ├── query.py             # Query processing endpoints
│   │   │   ├── documents.py         # Document management
│   │   │   ├── settings.py          # Settings management
│   │   │   ├── cache.py             # Cache management
│   │   │   └── feedback.py          # Feedback endpoints
│   │   ├── models/                   # Pydantic models
│   │   │   ├── query.py             # Query request/response models
│   │   │   ├── document.py          # Document models
│   │   │   └── settings.py          # Settings models
│   │   ├── services/                 # Business logic
│   │   │   ├── rag_service.py       # RAG engine wrapper
│   │   │   └── cache_service.py     # Cache service
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── config.py                 # Configuration management
│   │   └── dependencies.py           # Dependency injection
│   ├── Dockerfile                    # Backend container build
│   ├── requirements.txt              # Python dependencies
│   └── README_INTEGRATION.md         # Integration notes
│
├── _src/                              # Existing RAG System (Core Engine)
│   ├── app.py                        # Legacy Gradio interface
│   ├── config.py                     # System configuration
│   ├── adaptive_retrieval.py         # Adaptive retrieval engine
│   ├── cache_and_monitoring.py       # Caching and monitoring
│   ├── cache_next_gen.py            # Next-gen caching system
│   ├── document_processor.py         # Document processing
│   ├── conversation_memory.py        # Conversation history
│   ├── feedback_system.py           # User feedback system
│   ├── explainability.py            # Explainable AI features
│   ├── example_generator.py         # Example question generator
│   ├── evaluate.py                  # Evaluation metrics
│   ├── performance_monitor.py       # Performance monitoring
│   ├── benchmark_suite.py           # Performance benchmarks
│   ├── index_documents.py           # Document indexing
│   └── web_interface.py             # Web UI components
│
├── _config/                          # Deployment Configuration
│   ├── Dockerfile                   # Legacy container build
│   ├── deploy.ps1                   # Deployment script
│   └── startup.sh                   # Container startup script
│
├── docs/                             # Documentation
│   ├── api-contract.yaml            # OpenAPI 3.0 specification
│   ├── DEVELOPMENT.md               # Development setup guide
│   ├── cors-setup.md                # CORS configuration guide
│   ├── PROJECT_STRUCTURE.md         # This file
│   ├── ARCHITECTURE.md              # System architecture
│   └── DEMO_SCRIPT.md               # Demo walkthrough
│
├── documents/                        # Document Storage
│   └── *.pdf, *.docx, *.txt        # Indexed documents
│
├── chroma_db/                        # Vector Database
│   └── [ChromaDB files]             # Persisted embeddings
│
├── logs/                             # Application Logs
│   ├── rag_system.log               # Main system log
│   └── *.json                       # Performance logs
│
├── tests/                            # Test Suite
│   ├── test_integration.py          # Integration tests
│   ├── test_performance.py          # Performance tests
│   └── test_*.py                    # Various test files
│
├── .env.example                     # Environment variables template
├── docker-compose.yml               # Service orchestration
├── requirements_FROZEN.txt          # Python dependencies (frozen)
├── README.md                        # Main project README
└── CHANGELOG_v3.7.md               # Version changelog
```

## Service Architecture

### Docker Services

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: rag-network               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐       ┌──────────────┐                    │
│  │   Frontend   │──────▶│   Backend    │                    │
│  │   (React)    │       │   (FastAPI)  │                    │
│  │   Port 3000  │       │   Port 8000  │                    │
│  └──────────────┘       └───────┬──────┘                    │
│                                  │                            │
│                         ┌────────┴─────────┐                 │
│                         │                  │                 │
│                    ┌────▼─────┐     ┌─────▼────┐            │
│                    │  Ollama  │     │  Redis   │            │
│                    │ (LLM)    │     │ (Cache)  │            │
│                    │Port 11434│     │Port 6379 │            │
│                    └──────────┘     └──────────┘            │
│                                                               │
│  ┌──────────────┐                                            │
│  │ Gradio       │ (Optional - Legacy UI)                     │
│  │ (Legacy)     │                                            │
│  │ Port 7860    │                                            │
│  └──────────────┘                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Volumes:
├── ollama-data (LLM models)
├── redis-data (Cache persistence)
├── ./documents (Mounted to containers)
├── ./chroma_db (Vector DB persistence)
└── ./logs (Application logs)
```

### Data Flow

```
User Request Flow:
1. User → Frontend (React UI)
2. Frontend → Backend API (HTTP POST /api/query)
3. Backend → Cache (Redis) - Check for cached result
4. Backend → RAG Engine (_src/) - If cache miss
5. RAG Engine → Vector DB (ChromaDB) - Retrieve context
6. RAG Engine → Ollama (LLM) - Generate answer
7. RAG Engine → Cache (Redis) - Store result
8. Backend → Frontend - Return response
9. Frontend → User - Display answer
```

## Technology Stack

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **UI Library**: TBD (Tailwind CSS, Chakra UI, or MUI)
- **State Management**: TBD (Redux Toolkit, Zustand, or Context API)
- **HTTP Client**: Axios or Fetch API
- **Web Server**: Nginx (production)

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11
- **Validation**: Pydantic
- **Server**: Uvicorn
- **Documentation**: OpenAPI 3.0 (auto-generated)

### RAG Engine
- **LLM Interface**: LangChain + Ollama
- **Embeddings**: Ollama (nomic-embed-text)
- **Vector DB**: ChromaDB
- **Sparse Retrieval**: BM25
- **Cache**: Redis
- **Document Processing**: LangChain, PyPDF, python-docx

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **GPU Support**: NVIDIA Docker (CUDA 11.8)
- **Cache**: Redis 7
- **LLM Server**: Ollama

## Port Mapping

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| Frontend (Prod) | 3000 | HTTP | React app (Nginx) |
| Frontend (Dev) | 5173 | HTTP | Vite dev server |
| Backend | 8000 | HTTP | FastAPI REST API |
| Ollama | 11434 | HTTP | LLM inference server |
| Redis | 6379 | TCP | Cache server |
| Gradio (Legacy) | 7860 | HTTP | Original Gradio UI |

## File Patterns

### Frontend Files
```
*.tsx        # React components (TypeScript + JSX)
*.ts         # TypeScript modules
*.css        # Stylesheets
*.json       # Configuration files
```

### Backend Files
```
*.py         # Python modules
requirements.txt  # Python dependencies
.env         # Environment variables
```

### Documentation
```
*.md         # Markdown documentation
*.yaml       # YAML configuration/specs
```

## Environment Configuration

### Development
- Frontend dev server on 5173 (hot reload)
- Backend on 8000 (auto-reload with `--reload`)
- Local Ollama and Redis via Docker
- Source code mounted as volumes

### Production
- Frontend built and served by Nginx on 3000
- Backend in production container on 8000
- All services in Docker Compose
- No source mounting (built into images)

## Migration Status

### Completed (Integration Layer)
- ✅ Docker Compose updated with new services
- ✅ Frontend Dockerfile created
- ✅ Backend Dockerfile ready
- ✅ Nginx configuration for frontend
- ✅ API contract defined (OpenAPI spec)
- ✅ CORS documentation
- ✅ Development guide
- ✅ Integration tests
- ✅ Environment variable templates

### In Progress (Week 1)
- 🚧 Backend API implementation
- 🚧 Frontend component development
- 🚧 API client service

### Planned (Weeks 2-4)
- ⏳ State management implementation
- ⏳ Advanced UI features
- ⏳ End-to-end testing
- ⏳ Production deployment
- ⏳ Legacy UI deprecation

## Key Directories Explained

### `/frontend`
Contains the modern React UI that replaces the Gradio interface. Users interact with this via a web browser.

### `/backend`
FastAPI REST API that wraps the RAG engine and provides endpoints for the frontend. Acts as the bridge between UI and RAG system.

### `/_src`
The core RAG engine - contains all the AI/ML logic, document processing, retrieval strategies, and caching. This code is stable and battle-tested.

### `/_config`
Legacy deployment configuration. Will be gradually deprecated as we move to the new Docker Compose setup.

### `/docs`
Comprehensive documentation including API contracts, development guides, and architecture diagrams.

### `/documents`
User-uploaded documents that get indexed into the vector database.

### `/chroma_db`
Persistent storage for vector embeddings. This is where the semantic search happens.

### `/logs`
Application logs, performance metrics, and debugging information.

## Getting Started

### Quick Start (Full Stack)
```bash
docker-compose up --build
# Access: http://localhost:3000
```

### Development Mode
```bash
# Terminal 1: Infrastructure
docker-compose up ollama redis

# Terminal 2: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 3: Frontend
cd frontend && npm run dev
```

See `docs/DEVELOPMENT.md` for detailed setup instructions.

## References

- [Development Guide](./DEVELOPMENT.md)
- [API Contract](./api-contract.yaml)
- [CORS Setup](./cors-setup.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Main README](../README.md)
