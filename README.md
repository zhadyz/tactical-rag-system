# Forge

**An agentic retrieval-augmented generation system implementing fourteen state-of-the-art techniques within a single-GPU deployment constraint.**

[![Forge V5](https://img.shields.io/badge/Forge-V5.0-4f46e5.svg)](https://forge.onyxlab.ai)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://python.org)
[![Tauri 2.9](https://img.shields.io/badge/Tauri-2.9-FFC131.svg)](https://tauri.app)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178c6.svg)](https://www.typescriptlang.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1+-1C3C3C.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**[Documentation](https://forge.onyxlab.ai)** · **[Architecture](https://forge.onyxlab.ai/architecture/overview)** · **[Techniques](https://forge.onyxlab.ai/techniques/overview)** · **[API Reference](https://forge.onyxlab.ai/api-reference)**

---

## Abstract

Contemporary retrieval-augmented generation systems typically implement two to four retrieval techniques — hybrid search, reranking, and perhaps query expansion — operating within a fixed, single-pass pipeline. Forge challenges this paradigm by unifying fourteen distinct techniques into a coherent agentic architecture where the language model itself orchestrates retrieval decisions through iterative reasoning.

The system introduces three architectural departures from conventional RAG:

1. **Agentic retrieval** — a LangGraph state machine replaces the fixed retrieve-then-generate pipeline, enabling the model to select tools, evaluate intermediate results, and re-retrieve when evidence is insufficient.

2. **Multi-granularity indexing** — documents are decomposed into a four-level hierarchy (document summaries, section abstracts, semantic chunks, and atomic propositions), each level serving different query characteristics.

3. **Pre-generation verification** — a corrective retrieval gate evaluates document relevance before generation, while post-generation self-verification audits each claim against its cited sources.

All fourteen techniques operate within a 16GB VRAM budget through careful architectural partitioning: the language model occupies the GPU exclusively, while embedding, reranking, and vector operations execute on CPU with negligible latency impact.

---

## The Fourteen Techniques

Forge implements each technique to address a specific, empirically documented failure mode in retrieval-augmented generation:

### Retrieval Intelligence

| # | Technique | Failure Mode Addressed | Implementation |
|---|-----------|----------------------|----------------|
| 1 | **Agentic RAG** | Single-shot retrieval misses multi-hop evidence | LangGraph ReAct loop with 6 tools, max 3 iterations |
| 2 | **CRAG Quality Gate** | Irrelevant documents degrade generation quality | Cross-encoder scoring with CORRECT/AMBIGUOUS/INCORRECT classification |
| 3 | **Multi-Hop Reasoning** | Complex questions requiring cross-document synthesis | Agent decomposes queries and follows cross-references iteratively |

### Precision Indexing

| # | Technique | Failure Mode Addressed | Implementation |
|---|-----------|----------------------|----------------|
| 4 | **Contextual Retrieval** | Chunks lose meaning without surrounding context | LLM-generated context prefix prepended before embedding (Anthropic, 2024) |
| 5 | **Proposition Indexing** | Chunk-level granularity too coarse for factual queries | Dense-X atomic claim extraction indexed as L3 points |
| 6 | **Hierarchical 4-Level** | Single granularity cannot serve diverse query types | L0 summaries → L1 sections → L2 chunks → L3 propositions |

### Advanced Search

| # | Technique | Failure Mode Addressed | Implementation |
|---|-----------|----------------------|----------------|
| 7 | **BGE-M3 Tri-Modal Vectors** | Separate dense and sparse pipelines add complexity | Single model producing dense, sparse, and ColBERT representations |
| 8 | **ColBERT Late Interaction** | Dense vectors compress away token-level distinctions | Qdrant multi-vector MaxSim scoring for precision reranking |
| 9 | **Knowledge Graph** | Vector similarity cannot capture structural relationships | Entity-relationship extraction with Redis adjacency traversal |

### Answer Quality

| # | Technique | Failure Mode Addressed | Implementation |
|---|-----------|----------------------|----------------|
| 10 | **Self-Verification** | Generated claims may lack source support | Post-generation claim extraction and source matching |
| 11 | **6-Signal Confidence** | Binary confidence insufficient for nuanced reliability | Weighted composite of retrieval, CRAG, verification, and alignment signals |
| 12 | **Query Decomposition** | Multi-part questions retrieve poorly as single queries | Agent-driven decomposition into targeted sub-queries |
| 13 | **HyDE** | Queries and documents occupy different semantic spaces | Hypothetical document generation for improved embedding alignment |
| 14 | **Parent Expansion** | Retrieved chunks lack surrounding context | Automatic expansion to parent section upon retrieval |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FORGE V5                                 │
│                                                                   │
│  Desktop Shell (Tauri + React)                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Agent Reasoning Panel · Chat · Sources · Verification   │   │
│  └────────────────────────────┬─────────────────────────────┘   │
│                               │ SSE (11 event types)             │
│  Backend (FastAPI + LangGraph)│                                  │
│  ┌────────────────────────────┴─────────────────────────────┐   │
│  │                                                           │   │
│  │  ┌─────────────────────────────────────────────────┐     │   │
│  │  │            LangGraph Agent (7 nodes)             │     │   │
│  │  │                                                   │     │   │
│  │  │  analyze → retrieve ⟲ crag_gate → rerank         │     │   │
│  │  │                          ↓                        │     │   │
│  │  │                    generate → verify → finalize    │     │   │
│  │  │                                                   │     │   │
│  │  │  Tools: semantic_search · proposition_search      │     │   │
│  │  │         keyword_search · graph_traverse           │     │   │
│  │  │         chunk_read · section_read                 │     │   │
│  │  └─────────────────────────────────────────────────┘     │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────────┐     │   │
│  │  │  BGE-M3  │  │   CRAG   │  │  Self-Verification │     │   │
│  │  │  (CPU)   │  │   Gate   │  │  Claim Auditor     │     │   │
│  │  └──────────┘  └──────────┘  └────────────────────┘     │   │
│  └───────────────────────────────────────────────────────────┘   │
│                          │              │                         │
│  Infrastructure          │              │                         │
│  ┌───────────────────────┴──────────────┴───────────────────┐   │
│  │  Qdrant (dense + sparse + ColBERT) │ Redis (4-layer cache)│   │
│  │  llama.cpp (GPU, 10-14GB VRAM)     │ Knowledge Graph      │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### VRAM Budget (16GB)

| Component | Location | Memory |
|-----------|----------|--------|
| LLM (14B Q4_K_M) | GPU | 10–14 GB |
| KV Cache | GPU | 2–4 GB |
| BGE-M3 Embeddings | CPU | 2.3 GB RAM |
| ColBERT Reranker | CPU | 1 GB RAM |
| Cross-Encoder (CRAG) | CPU | 400 MB RAM |
| Qdrant + Redis | CPU/Disk | Variable |

The architectural insight: by restricting GPU allocation exclusively to LLM inference and executing all other operations on CPU, the system achieves competitive latency while remaining deployable on consumer hardware.

---

## Quick Start

```bash
# Clone and launch infrastructure
git clone https://github.com/zhadyz/tactical-rag-system.git && cd tactical-rag-system
docker compose -f backend/docker-compose.yml up -d qdrant redis

# Start the backend
cd backend && pip install -r requirements.txt
uvicorn forge.main:app --host 0.0.0.0 --port 8000

# Upload a document
curl -X POST http://localhost:8000/api/documents/upload -F "file=@document.pdf"

# Trigger the ingestion pipeline (hierarchical chunking + contextual enrichment + propositions + graph)
curl -X POST http://localhost:8000/api/ingest

# Query in agentic mode with streaming
curl -N http://localhost:8000/api/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key findings?", "mode": "agentic", "use_context": true}'
```

The streaming response emits eleven SSE event types: `agent_thinking`, `tool_call`, `tool_result`, `crag_evaluation`, `retrieval_complete`, `token`, `sources`, `verification`, `metadata`, `error`, and `done`.

---

## Ingestion Pipeline

Documents undergo a six-stage transformation before becoming queryable:

```
Document → Parse → Hierarchical Chunk → Contextual Enrich → Extract Propositions → Build Graph → Index
```

1. **Structure-Aware Parsing** — Preserves heading hierarchy, tables, and cross-references across PDF, DOCX, Markdown, and plaintext formats.

2. **Hierarchical Chunking** — Produces four levels: L0 document summaries (LLM-generated, 200–300 words), L1 section abstracts, L2 semantic chunks (similarity-based splitting, 200–2000 characters), and L3 atomic propositions.

3. **Contextual Enrichment** — For each L2 chunk, the LLM generates a 50–100 token context prefix situating the chunk within its document and section. This prefix is prepended before embedding, following Anthropic's contextual retrieval methodology which demonstrates 49% fewer retrieval failures.

4. **Proposition Extraction** — Each L2 chunk yields up to ten atomic, self-contained factual claims indexed as L3 points with parent references, enabling precision retrieval for factual queries.

5. **Knowledge Graph Construction** — Entities (regulations, roles, procedures) and relationships (authorizes, requires, references, supersedes) are extracted and stored in Qdrant payloads with a Redis adjacency list for traversal.

6. **Multi-Representation Indexing** — BGE-M3 produces dense, sparse, and ColBERT vectors in a single forward pass. All three representations are stored as Qdrant named vectors, eliminating the need for separate embedding and BM25 pipelines.

---

## Query Pipeline

### Agentic Mode

The LangGraph state machine executes a ReAct loop with seven nodes:

1. **Analyze** — Classify query type (factual, procedural, comparative, temporal, multi-hop, complex). Decompose multi-part questions into sub-queries.

2. **Retrieve** — The agent selects from six tools based on query characteristics:
   - `semantic_search` — Dense + sparse hybrid via BGE-M3
   - `proposition_search` — L3 atomic claim index for precision
   - `keyword_search` — Sparse-only for exact terms and identifiers
   - `graph_traverse` — Follow entity relationships
   - `chunk_read` — Expand a chunk with parent context
   - `section_read` — Read full L1 section

3. **CRAG Gate** — Cross-encoder scores each retrieved document. Documents classified as CORRECT (>0.7) proceed; AMBIGUOUS (0.3–0.7) are expanded to parent sections; INCORRECT (<0.3) are discarded. If fewer than two documents survive, the agent re-retrieves with a refined query (maximum one retry).

4. **Rerank** — ColBERT late interaction scoring via Qdrant multi-vector MaxSim, with cross-encoder fallback.

5. **Generate** — LLM produces a citation-aware response with explicit `[Source N]` references.

6. **Verify** — Claims are extracted from the generated answer and individually verified against source documents.

7. **Finalize** — Six-signal confidence score computed from retrieval quality, answer completeness, semantic alignment, source consistency, CRAG quality, and verification coverage.

### Direct Mode

For latency-sensitive queries, direct mode bypasses the agent loop: single-shot hybrid retrieval → reranking → generation. Typical response time under two seconds with warm cache.

---

## Streaming Protocol

Forge streams eleven event types via Server-Sent Events, providing full transparency into the agent's reasoning process:

```
agent_thinking  → "Classifying query as PROCEDURAL..."
tool_call       → semantic_search({ query: "...", k: 20 })
tool_result     → 15 documents, top score: 0.94, 45ms
crag_evaluation → 8 correct, 3 ambiguous, 1 rejected
retrieval_complete → 8 documents approved
token           → "Active" "duty" "members" ...
sources         → [{ content, score, metadata }]
verification    → 3 claims, 3/3 supported
metadata        → { confidence: 0.92, timing: {...} }
done
```

The frontend renders these events in real-time through an Agent Reasoning Panel, providing users with full observability into the retrieval and verification process.

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Desktop Shell | Tauri 2.9 + Rust | Cross-platform native wrapper |
| Frontend | React 19, TypeScript 5.6, Tailwind CSS | Agent reasoning UI, streaming display |
| State | Zustand 5 | Agent step lifecycle management |
| Backend | FastAPI, Python 3.11+ | API layer with rate limiting and injection detection |
| Agent | LangGraph 1.1 | ReAct state machine with tool orchestration |
| LLM | llama.cpp (CUDA) | GPU-accelerated inference, 80–100 tok/s |
| Embeddings | BGE-M3 (FlagEmbedding) | Tri-modal: dense + sparse + ColBERT |
| Vector DB | Qdrant | Named vectors, multi-vector, HNSW |
| Cache | Redis | 4-layer: exact, semantic, embedding, proposition |
| Reranking | ColBERT + Cross-Encoder | Token-level precision + CRAG quality gate |

---

## Project Structure

```
forge/
├── backend/forge/                    # Python backend (38 modules)
│   ├── ingestion/                   # 6-stage document processing pipeline
│   │   ├── parser.py               # Structure-aware document parsing
│   │   ├── chunker.py              # Hierarchical 4-level chunking
│   │   ├── contextual.py           # Anthropic contextual retrieval
│   │   ├── propositions.py         # Dense-X proposition extraction
│   │   ├── graph.py                # Knowledge graph construction
│   │   └── indexer.py              # BGE-M3 multi-representation indexing
│   ├── retrieval/                   # Agentic query pipeline
│   │   ├── agent.py                # LangGraph 7-node state machine
│   │   ├── tools.py                # 6 retrieval tools
│   │   ├── crag.py                 # Corrective retrieval quality gate
│   │   ├── reranker.py             # ColBERT + cross-encoder
│   │   └── verifier.py             # Post-generation claim verification
│   ├── generation/                  # Answer synthesis
│   │   ├── generator.py            # Citation-aware LLM generation
│   │   ├── confidence.py           # 6-signal confidence scoring
│   │   └── streaming.py            # 11-type SSE event protocol
│   ├── infrastructure/              # Shared services
│   │   ├── vectorstore.py          # Qdrant named vectors + ColBERT
│   │   ├── embeddings.py           # BGE-M3 tri-modal service
│   │   ├── cache.py                # 4-layer Redis cache
│   │   ├── llm.py                  # llama.cpp + Ollama factory
│   │   └── models.py               # Runtime model hotswapping
│   ├── container.py                 # Dependency injection
│   └── config.py                    # YAML-driven configuration
├── src/                             # React frontend
│   ├── components/Agent/            # Agent reasoning visualization
│   ├── hooks/useStreamingChat.ts    # 11-event SSE handler
│   └── store/useStore.ts            # Agent state management
├── src-tauri/                       # Tauri Rust shell
└── docs-site/                       # Documentation (forge.onyxlab.ai)
```

---

## Validation

Integration testing verifies the complete system without external services using Qdrant in-memory mode:

```
FORGE V5 END-TO-END TEST RESULTS
═══════════════════════════════════
  [PASS] Configuration
  [PASS] Schema Validation (11 event types)
  [PASS] VectorStore (4-level hierarchy, named vectors)
  [PASS] Document Parsing
  [PASS] Hierarchical Chunking (L0/L1/L2)
  [PASS] LangGraph Agent (CompiledStateGraph)
  [PASS] CRAG Quality Gate
  [PASS] Confidence Scoring (65.9%, 6 signals)
  [PASS] SSE Streaming (7 event types validated)
  [PASS] FastAPI Application (22 routes)

  10/10 passed, 0 failed
```

Additional validation:
- **Python**: 38 files, zero syntax errors, zero cross-module import mismatches
- **TypeScript**: Zero type errors across frontend
- **Vite Build**: 2,371 modules compiled in 3.3 seconds
- **Documentation**: 24 pages build cleanly via Next.js static export
- **Docker Compose**: Configuration validates without error

---

## Documentation

Comprehensive documentation is available at **[forge.onyxlab.ai](https://forge.onyxlab.ai)**, including:

- **[Getting Started](https://forge.onyxlab.ai/getting-started/quick-start)** — Installation, configuration, and first query
- **[Techniques](https://forge.onyxlab.ai/techniques/overview)** — Deep dives into each of the fourteen techniques
- **[Architecture](https://forge.onyxlab.ai/architecture/overview)** — System design, pipeline flows, and streaming protocol
- **[API Reference](https://forge.onyxlab.ai/api-reference)** — All twelve endpoints with request/response schemas

---

## License

MIT

---

<p align="center">
  <sub>Built by <b>hollowed_eyes</b> — demonstrating that no open-source system combines all fourteen techniques into a single, GPU-efficient pipeline.</sub>
</p>
