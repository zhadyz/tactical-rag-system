"""
LEGACY GRADIO INTERFACE - DEPRECATED
======================================

⚠️ This file is DEPRECATED and will be removed in a future version.

The Gradio UI has been replaced by a modern React + FastAPI architecture:
- Frontend: React with TypeScript (frontend/src/)
- Backend: FastAPI REST API (backend/app/)
- Docs: See docs/ARCHITECTURE.md for new stack

This file is kept temporarily for reference only. It is NOT used in production.

For the production RAG engine, see:
- backend/app/core/rag_engine.py (RAG logic, Gradio-free)
- backend/app/api/query.py (Query endpoints)
- frontend/src/components/Chat/ (Chat UI)

Original Description:
Enterprise RAG System - Redesigned Interface (v2)
Simplified UI with Simple and Adaptive modes
"""

import asyncio
import gradio as gr
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from datetime import datetime
import os
import torch

from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM  # Updated to use new langchain-ollama package (18-64x faster!)
from langchain_community.embeddings import OllamaEmbeddings
from langchain.docstore.document import Document
from langchain_community.retrievers import BM25Retriever

from config import SystemConfig, load_config
from adaptive_retrieval import AdaptiveRetriever, AdaptiveAnswerGenerator, RetrievalResult
from document_processor import DocumentProcessor, ProcessingResult
from cache_and_monitoring import CacheManager, PerformanceMonitor, Timer, PerformanceProfiler
from example_generator import ExampleGenerator
from conversation_memory import ConversationMemory
from feedback_system import FeedbackManager
from collection_metadata import CollectionMetadata
from llm_factory import create_llm, get_llm_type

# Import Qdrant store (only if use_qdrant is enabled)
try:
    from qdrant_store import QdrantVectorStore
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("Qdrant dependencies not installed. Install with: pip install qdrant-client")

os.makedirs('logs', exist_ok=True)
os.makedirs('.cache', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rag_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class VectorStoreAdapter:
    """
    Unified adapter for both ChromaDB and Qdrant
    Provides consistent interface regardless of backend
    """

    def __init__(self, vectorstore, store_type: str = "chroma"):
        self.vectorstore = vectorstore
        self.store_type = store_type

    async def similarity_search_with_score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Search for similar documents with scores
        Returns: List of (Document, score) tuples
        """
        if self.store_type == "chroma":
            # ChromaDB returns list of (doc, distance) - lower is better
            results = await asyncio.to_thread(
                self.vectorstore.similarity_search_with_score,
                query,
                k=k
            )
            # Convert distance to similarity (1 - distance)
            return [(doc, 1.0 - score) for doc, score in results]

        elif self.store_type == "qdrant":
            # Get query embedding first
            from langchain_community.embeddings import OllamaEmbeddings
            # Qdrant needs raw embeddings
            # Assumption: embeddings are available via vectorstore
            # This will be set during initialization
            if not hasattr(self, 'embeddings'):
                raise RuntimeError("Embeddings not set for Qdrant adapter")

            query_vector = await asyncio.to_thread(
                self.embeddings.embed_query,
                query
            )

            # Search in Qdrant
            search_results = await self.vectorstore.search(
                query_vector=query_vector,
                top_k=k
            )

            # Convert to LangChain Document format
            documents = []
            for result in search_results:
                doc = Document(
                    page_content=result.text,
                    metadata=result.metadata
                )
                documents.append((doc, result.score))

            return documents

        else:
            raise ValueError(f"Unknown store type: {self.store_type}")

    def set_embeddings(self, embeddings):
        """Set embeddings function for Qdrant"""
        self.embeddings = embeddings


class EnterpriseRAGSystem:
    """Complete enterprise RAG system with simple and adaptive modes"""

    # Default settings
    DEFAULT_SETTINGS = {
        'simple_k': 5,
        'hybrid_k': 20,
        'advanced_k': 15,
        'rerank_weight': 0.7,
        'simple_threshold': 1,
        'moderate_threshold': 3,
        'rrf_constant': 60
    }

    def __init__(self, config: SystemConfig):
        self.config = config
        self.vectorstore = None  # Will be VectorStoreAdapter (supports both ChromaDB and Qdrant)
        self.vectorstore_backend = None  # The actual backend (Chroma or QdrantVectorStore)
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.retrieval_engine: Optional[AdaptiveRetriever] = None
        self.answer_generator: Optional[AdaptiveAnswerGenerator] = None
        self.llm: Optional[OllamaLLM] = None
        self.embeddings = None  # Store embeddings for collection metadata
        self.collection_metadata: Optional[CollectionMetadata] = None
        self.cache_manager: Optional[CacheManager] = None
        self.monitor: Optional[PerformanceMonitor] = None
        self.profiler: Optional[PerformanceProfiler] = None
        self.conversation_memory: Optional[ConversationMemory] = None
        self.feedback_manager: Optional[FeedbackManager] = None
        self.initialized = False
        self.using_qdrant = False  # Track which backend is in use

        # Runtime settings
        self.runtime_settings = self.DEFAULT_SETTINGS.copy()

        # Current mode: "simple" or "adaptive"
        self.current_mode = "simple"

        # Track last query for feedback
        self.last_query_metadata = {
            "query": "",
            "answer": "",
            "query_type": None,
            "strategy_used": None
        }

        self.example_questions = [
            "What are the main requirements?",
            "Can you summarize the key policies?",
            "What procedures should I follow?",
            "What are the standards mentioned?"
        ]

        self.gpu_available = torch.cuda.is_available()
        if self.gpu_available:
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        else:
            logger.warning("No GPU detected - will use CPU")

        logger.info("Enterprise RAG System created")

    def set_mode(self, mode: str):
        """Set retrieval mode: 'simple' or 'adaptive'"""
        if mode in ["simple", "adaptive"]:
            self.current_mode = mode
            logger.info(f"Retrieval mode set to: {mode}")
        else:
            logger.warning(f"Invalid mode: {mode}")

    def update_settings(self, **kwargs):
        """Update runtime settings with validation"""
        for key, value in kwargs.items():
            if key in self.DEFAULT_SETTINGS:
                # Validate ranges
                if key.endswith('_k'):
                    value = max(1, min(50, int(value)))
                elif key.endswith('_weight'):
                    value = max(0.0, min(1.0, float(value)))
                elif key.endswith('_threshold'):
                    value = max(0, min(10, int(value)))
                elif key == 'rrf_constant':
                    value = max(1, min(100, int(value)))

                self.runtime_settings[key] = value
                logger.info(f"Setting updated: {key} = {value}")

        if self.retrieval_engine:
            self.retrieval_engine.runtime_settings = self.runtime_settings

    def reset_settings(self):
        """Reset to default settings"""
        self.runtime_settings = self.DEFAULT_SETTINGS.copy()
        if self.retrieval_engine:
            self.retrieval_engine.runtime_settings = self.runtime_settings
        logger.info("Settings reset to defaults")
        return self.runtime_settings

    async def initialize(self) -> Tuple[bool, str]:
        """Initialize the RAG system"""

        try:
            logger.info("=" * 60)
            logger.info("INITIALIZING ENTERPRISE RAG SYSTEM")
            logger.info("=" * 60)

            if self.gpu_available:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(f"\n🎮 GPU: {gpu_name} ({gpu_mem:.1f}GB)")

            logger.info("\n1. Initializing embedding model...")
            self.embeddings = OllamaEmbeddings(
                model=self.config.embedding.model_name,
                base_url=self.config.ollama_host
            )

            test_embed = await asyncio.to_thread(self.embeddings.embed_query, "test")
            logger.info(f"✓ Embedding model ready (dim: {len(test_embed)})")

            logger.info("\n2. Initializing infrastructure...")
            def embed_for_cache(text: str) -> List[float]:
                return self.embeddings.embed_query(text)

            self.cache_manager = CacheManager(self.config, embeddings_func=embed_for_cache)
            self.monitor = PerformanceMonitor(self.config, self.cache_manager)
            self.profiler = PerformanceProfiler(output_dir=Path("logs"))

            logger.info("\n3. Loading vector database...")

            # FEATURE FLAG: Choose between ChromaDB and Qdrant
            if self.config.use_qdrant:
                logger.info("🔷 Using Qdrant vector store")

                if not QDRANT_AVAILABLE:
                    return False, "Qdrant not available. Install with: pip install qdrant-client"

                # Initialize Qdrant client
                try:
                    self.vectorstore_backend = QdrantVectorStore(
                        host=self.config.qdrant.host,
                        port=self.config.qdrant.port,
                        collection_name=self.config.qdrant.collection_name,
                        vector_size=self.config.embedding.dimension
                    )

                    # Check if collection exists
                    if not self.vectorstore_backend.client.collection_exists(
                        self.config.qdrant.collection_name
                    ):
                        return False, f"Qdrant collection '{self.config.qdrant.collection_name}' not found. Please run migration first."

                    # Get collection info
                    info = self.vectorstore_backend.get_collection_info()
                    logger.info(f"✓ Qdrant connected: {info['points_count']} vectors in collection")

                    # Wrap in adapter
                    self.vectorstore = VectorStoreAdapter(self.vectorstore_backend, store_type="qdrant")
                    self.vectorstore.set_embeddings(self.embeddings)
                    self.using_qdrant = True

                except Exception as e:
                    logger.error(f"Failed to connect to Qdrant: {e}")
                    return False, f"Qdrant connection failed: {str(e)}"

            else:
                logger.info("🔶 Using ChromaDB vector store (default)")

                if not self.config.vector_db_dir.exists():
                    return False, "ChromaDB not found. Please run indexing first."

                self.vectorstore_backend = Chroma(
                    persist_directory=str(self.config.vector_db_dir),
                    embedding_function=self.embeddings
                )

                # Wrap in adapter
                self.vectorstore = VectorStoreAdapter(self.vectorstore_backend, store_type="chroma")
                logger.info("✓ ChromaDB loaded")
                self.using_qdrant = False

            # Initialize collection metadata for semantic scope detection
            logger.info("\n3.5. Initializing collection metadata...")
            try:
                from pathlib import Path as PathLib
                metadata_path = PathLib(self.config.scope_detection.metadata_path)

                self.collection_metadata = CollectionMetadata.load_or_compute(
                    vectorstore=self.vectorstore,
                    embeddings=self.embeddings,
                    llm=self.llm if hasattr(self, 'llm') and self.llm else None,  # May not be initialized yet
                    metadata_path=metadata_path,
                    force_recompute=self.config.scope_detection.force_recompute
                )
                logger.info(f"✓ Collection metadata ready: {self.collection_metadata.scope_summary[:60]}...")
            except Exception as e:
                logger.warning(f"⚠ Collection metadata initialization skipped: {e}")
                logger.warning("  Out-of-scope detection will be disabled")
                self.collection_metadata = None

            logger.info("\n4. Loading BM25 retriever...")
            metadata_file = self.config.vector_db_dir / "chunk_metadata.json"

            if metadata_file.exists():
                import json
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    texts = data['texts']
                    metadata = data['metadata']

                bm25_docs = [
                    Document(page_content=text, metadata=meta)
                    for text, meta in zip(texts, metadata)
                ]
                self.bm25_retriever = BM25Retriever.from_documents(bm25_docs)
                self.bm25_retriever.k = self.config.retrieval.initial_k
                logger.info(f"✓ BM25 retriever ready ({len(texts)} chunks)")
            else:
                logger.warning("⚠  BM25 metadata not found")
                self.bm25_retriever = BM25Retriever.from_documents([
                    Document(page_content="dummy")
                ])

            logger.info("\n5. Connecting to LLM...")

            # FEATURE FLAG: Use vLLM for 10-20x speedup or Ollama for compatibility
            self.llm = create_llm(self.config, test_connection=False)

            # Test LLM connection
            await asyncio.to_thread(self.llm.invoke, "Hello")

            llm_type = get_llm_type(self.llm)
            if llm_type == "vllm":
                logger.info("✓ LLM ready (vLLM - 10-20x faster)")
            else:
                logger.info("✓ LLM ready (Ollama - baseline)")

            logger.info("\n6. Initializing conversation memory...")
            self.conversation_memory = ConversationMemory(
                llm=self.llm,
                max_exchanges=10,
                summarization_threshold=5,
                enable_summarization=True
            )
            logger.info("✓ Conversation memory ready")

            logger.info("\n7. Initializing feedback system...")
            self.feedback_manager = FeedbackManager(storage_file="feedback.json")
            logger.info("✓ Feedback system ready")

            logger.info("\n8. Initializing retrieval engines...")
            self.retrieval_engine = AdaptiveRetriever(
                vectorstore=self.vectorstore,
                bm25_retriever=self.bm25_retriever,
                llm=self.llm,
                config=self.config,
                runtime_settings=self.runtime_settings
            )

            # Initialize answer generator with semantic scope detection
            self.answer_generator = AdaptiveAnswerGenerator(
                llm=self.llm,
                embeddings=self.embeddings,
                collection_metadata=self.collection_metadata,
                scope_config=self.config.scope_detection
            )
            logger.info("✓ Retrieval engines ready")

            logger.info("\n9. Generating example questions...")
            example_gen = ExampleGenerator(self.config, self.llm)
            self.example_questions = await example_gen.generate_examples(
                self.vectorstore,
                num_examples=4
            )
            logger.info(f"✓ Generated {len(self.example_questions)} examples")

            self.initialized = True

            logger.info("\n" + "=" * 60)
            logger.info("SYSTEM READY")
            logger.info("=" * 60)

            if self.gpu_available:
                gpu_mem_used = torch.cuda.memory_allocated(0) / 1024**2
                logger.info(f"GPU Memory in use: {gpu_mem_used:.1f}MB")

            return True, "System initialized successfully"

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False, f"Initialization failed: {str(e)}"

    async def query(self, question: str, use_context: bool = True) -> Dict:
        """Process query with selected mode"""

        if not self.initialized:
            return {
                "answer": "System not initialized",
                "sources": [],
                "error": True
            }

        start_time = asyncio.get_event_loop().time()

        if self.profiler:
            self.profiler.start_profile(question)

        try:
            # Check cache first
            cached_result = self.cache_manager.get_query_result(
                question,
                {"model": self.config.llm.model_name}
            )

            if cached_result:
                logger.info(f"Cache hit for query: {question[:50]}...")
                self.monitor.metrics.increment_counter("cache_hits")
                if self.profiler:
                    self.profiler.record_stage("cache_ms", 0)
                    self.profiler.complete_profile(success=True)
                return cached_result

            # Enhance query with conversation context
            enhanced_query = question
            if use_context and self.conversation_memory:
                enhanced_query, _ = self.conversation_memory.get_relevant_context_for_query(
                    question,
                    max_exchanges=3
                )

            # ROUTE BASED ON MODE
            retrieval_timer = Timer(self.monitor.metrics, "retrieval_total")
            with retrieval_timer:
                if self.current_mode == "simple":
                    # Simple mode: direct dense retrieval only
                    retrieval_result = await self._simple_retrieve(enhanced_query)
                else:
                    # Adaptive mode: full adaptive engine
                    # CRITICAL FIX: Pass original query for classification, enhanced for retrieval
                    retrieval_result = await self.retrieval_engine.retrieve(
                        query=enhanced_query,
                        original_query=question  # Use original query for classification
                    )

            if self.profiler:
                self.profiler.record_stage("retrieval_ms", retrieval_timer.elapsed * 1000)
                self.profiler.set_metadata(
                    query_type=retrieval_result.query_type if hasattr(retrieval_result, 'query_type') else "simple",
                    strategy_used=retrieval_result.strategy_used if hasattr(retrieval_result, 'strategy_used') else "simple_dense"
                )

            if not retrieval_result.documents:
                if self.profiler:
                    self.profiler.complete_profile(success=True)
                return {
                    "answer": "I couldn't find any relevant documents to answer your question.",
                    "sources": [],
                    "metadata": {
                        "strategy_used": "simple_dense" if self.current_mode == "simple" else retrieval_result.strategy_used,
                        "query_type": "simple" if self.current_mode == "simple" else retrieval_result.query_type,
                        "mode": self.current_mode
                    }
                }

            # Generate answer
            generation_timer = Timer(self.monitor.metrics, "generation")
            with generation_timer:
                answer = await self.answer_generator.generate(
                    question,
                    retrieval_result
                )

            if self.profiler:
                self.profiler.record_stage("llm_ms", generation_timer.elapsed * 1000)

            result = {
                "answer": answer,
                "sources": self._format_sources(retrieval_result),
                "metadata": {
                    "strategy_used": "simple_dense" if self.current_mode == "simple" else retrieval_result.strategy_used,
                    "query_type": "simple" if self.current_mode == "simple" else retrieval_result.query_type,
                    "mode": self.current_mode
                },
                "explanation": retrieval_result.explanation.to_dict() if hasattr(retrieval_result, 'explanation') and retrieval_result.explanation else None,
                "error": False
            }

            # Store in conversation memory
            if self.conversation_memory:
                self.conversation_memory.add(
                    query=question,
                    response=answer,
                    retrieved_docs=retrieval_result.documents,
                    query_type="simple" if self.current_mode == "simple" else retrieval_result.query_type,
                    strategy_used="simple_dense" if self.current_mode == "simple" else retrieval_result.strategy_used
                )

            # Cache result
            self.cache_manager.put_query_result(
                question,
                {"model": self.config.llm.model_name},
                result
            )

            # Store metadata for feedback
            self.last_query_metadata = {
                "query": question,
                "answer": answer,
                "query_type": "simple" if self.current_mode == "simple" else retrieval_result.query_type,
                "strategy_used": "simple_dense" if self.current_mode == "simple" else retrieval_result.strategy_used
            }

            elapsed = asyncio.get_event_loop().time() - start_time
            self.monitor.metrics.record_query(elapsed, success=True)

            if self.profiler:
                self.profiler.complete_profile(success=True)

            return result

        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)

            elapsed = asyncio.get_event_loop().time() - start_time
            self.monitor.metrics.record_query(elapsed, success=False)

            if self.profiler:
                self.profiler.complete_profile(success=False, error=str(e))

            return {
                "answer": f"An error occurred: {str(e)}",
                "sources": [],
                "error": True
            }

    async def _simple_retrieve(self, query: str) -> RetrievalResult:
        """Simple retrieval: direct dense vector search only"""

        # Use vectorstore adapter (works with both ChromaDB and Qdrant)
        docs = await self.vectorstore.similarity_search_with_score(
            query,
            k=self.runtime_settings['simple_k']
        )

        # Unpack documents and scores (adapter already returns similarity scores)
        documents = [doc for doc, score in docs]
        scores = [score for doc, score in docs]

        # Create simple retrieval result
        result = RetrievalResult(
            documents=documents,
            scores=scores,
            query_type="simple",
            strategy_used="simple_dense",
            explanation=None
        )

        return result

    def _format_sources(self, retrieval_result: RetrievalResult) -> List[Dict]:
        """Format source information"""

        sources = []
        seen_files = set()

        for doc, score in zip(
            retrieval_result.documents,
            retrieval_result.scores
        ):
            file_name = doc.metadata.get('file_name', 'Unknown')

            if file_name in seen_files:
                continue

            seen_files.add(file_name)

            sources.append({
                "file_name": file_name,
                "file_type": doc.metadata.get('file_type', 'unknown'),
                "relevance_score": float(score),
                "excerpt": doc.page_content[:250] + "...",
                "metadata": {
                    k: v for k, v in doc.metadata.items()
                    if k in ['page_number', 'chunk_index']
                }
            })

        return sources

    def get_system_status(self) -> Dict:
        """Get current system status"""

        if not self.initialized:
            return {
                "status": "offline",
                "message": "System not initialized"
            }

        stats = self.monitor.get_system_stats()

        doc_count = 0
        chunk_count = 0

        if self.config.documents_dir.exists():
            supported_ext = ['.txt', '.pdf', '.docx', '.doc', '.md']
            doc_count = sum(
                1 for f in self.config.documents_dir.rglob('*')
                if f.suffix.lower() in supported_ext
            )

        metadata_file = self.config.vector_db_dir / "chunk_metadata.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                chunk_count = len(data.get('texts', []))

        gpu_status = "Disabled"
        gpu_memory = 0
        if self.gpu_available:
            gpu_status = f"Enabled ({torch.cuda.get_device_name(0)})"
            gpu_memory = torch.cuda.memory_allocated(0) / 1024**2

        conversation_stats = {}
        if self.conversation_memory:
            conversation_stats = self.conversation_memory.get_stats()

        return {
            "status": "operational",
            "documents": doc_count,
            "chunks": chunk_count,
            "uptime": stats['uptime_formatted'],
            "queries_processed": stats['metrics']['query_count'],
            "avg_latency": stats['metrics']['avg_latency'],
            "cache_hit_rate": stats['cache'].get('query_cache', {}).get('hit_rate', 0),
            "conversation": conversation_stats,
            "mode": self.current_mode,
            "config": {
                "model": self.config.llm.model_name,
                "embedding": self.config.embedding.model_name,
                "gpu": gpu_status,
                "gpu_memory_mb": int(gpu_memory),
                "vector_store": "Qdrant" if self.using_qdrant else "ChromaDB"
            }
        }

    def clear_conversation(self) -> None:
        """Clear conversation memory"""
        if self.conversation_memory:
            self.conversation_memory.clear()
            logger.info("Conversation memory cleared")

    def submit_feedback(self, rating: str) -> Tuple[bool, str]:
        """Submit feedback for the last query/answer"""
        if not self.feedback_manager:
            return False, "Feedback system not initialized"

        if not self.last_query_metadata["query"]:
            return False, "No recent query to provide feedback for"

        success = self.feedback_manager.add_feedback(
            query=self.last_query_metadata["query"],
            answer=self.last_query_metadata["answer"],
            rating=rating,
            query_type=self.last_query_metadata["query_type"],
            strategy_used=self.last_query_metadata["strategy_used"]
        )

        if success:
            emoji = "👍" if rating == "thumbs_up" else "👎"
            return True, f"{emoji} Thank you for your feedback!"
        else:
            return False, "Failed to submit feedback"


rag_system: Optional[EnterpriseRAGSystem] = None


async def initialize_system():
    global rag_system
    config = load_config()
    rag_system = EnterpriseRAGSystem(config)
    success, message = await rag_system.initialize()
    return success, message


async def process_query(message: str, history: List) -> str:
    global rag_system

    if not rag_system or not rag_system.initialized:
        return "System not initialized. Please restart."

    if not message.strip():
        return "Please enter a question."

    result = await rag_system.query(message)

    if result.get("error"):
        return f"Error: {result['answer']}"

    response = f"{result['answer']}\n\n"

    if result.get("sources"):
        response += "---\n\n**Sources:**\n\n"

        for i, source in enumerate(result['sources'], 1):
            relevance_pct = source['relevance_score'] * 100
            response += f"{i}. **{source['file_name']}** ({relevance_pct:.0f}% relevant)\n"

            if source.get('metadata'):
                meta_parts = [f"{k}: {v}" for k, v in source['metadata'].items()]
                if meta_parts:
                    response += f"   *{' | '.join(meta_parts)}*\n"

            response += f"   \"{source['excerpt']}\"\n\n"

    if result.get("metadata"):
        mode = result['metadata'].get('mode', 'unknown').upper()
        response += f"\n*Mode: {mode} | "
        response += f"Strategy: {result['metadata'].get('strategy_used', 'unknown')}*"

    # Only show explanation in adaptive mode
    if rag_system.current_mode == "adaptive" and result.get("explanation"):
        explanation = result['explanation']
        response += "\n\n---\n\n<details><summary><b>📊 Explanation</b> (click to expand)</summary>\n\n"
        response += f"**Classification:** {explanation['query_type'].upper()} (score: {explanation['complexity_score']})\n\n"

        if explanation.get('scoring_breakdown'):
            response += "**Scoring Breakdown:**\n"
            for factor, value in explanation['scoring_breakdown'].items():
                response += f"- {factor.replace('_', ' ').title()}: {value}\n"
            response += "\n"

        if explanation.get('strategy_reasoning'):
            response += f"**Why this strategy?**\n{explanation['strategy_reasoning']}\n\n"

        if explanation.get('example_text'):
            response += f"**Summary:** {explanation['example_text']}\n"

        response += "</details>"

    return response


def get_status_html() -> str:
    global rag_system

    if not rag_system:
        return "<div style='padding:20px;background:#2d3748;color:#fc8181;border-radius:8px;'>System not initialized</div>"

    status = rag_system.get_system_status()

    if status['status'] == 'offline':
        badge = "background:#f56565"
        text = "OFFLINE"
    else:
        badge = "background:#48bb78"
        text = "ONLINE"

    # Mode badge
    mode = status.get('mode', 'simple').upper()
    mode_color = "#805ad5" if mode == "ADAPTIVE" else "#4299e1"
    mode_badge = f"<span style='background:{mode_color};padding:4px 12px;border-radius:4px;font-size:12px;font-weight:700;color:white;margin-left:8px;'>{mode}</span>"

    # GPU badge
    gpu_badge = ""
    if status['config'].get('gpu', 'Disabled') != 'Disabled':
        gpu_badge = f"<span style='background:#f6ad55;padding:4px 12px;border-radius:4px;font-size:12px;font-weight:700;color:white;margin-left:8px;'>GPU</span>"

    return f"""
    <div style="background:#1a202c;padding:20px;border-radius:8px;color:#e2e8f0;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <h3 style="margin:0;font-size:18px;font-weight:600;">Enterprise RAG System</h3>
            <div>
                <span style="{badge};padding:4px 12px;border-radius:4px;font-size:12px;font-weight:700;color:white;">{text}</span>
                {mode_badge}
                {gpu_badge}
            </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px;">
            <div style="background:#2d3748;padding:12px;border-radius:6px;">
                <div style="font-size:10px;color:#a0aec0;text-transform:uppercase;margin-bottom:4px;">Documents</div>
                <div style="font-size:24px;font-weight:700;color:#63b3ed;">{status['documents']}</div>
            </div>
            <div style="background:#2d3748;padding:12px;border-radius:6px;">
                <div style="font-size:10px;color:#a0aec0;text-transform:uppercase;margin-bottom:4px;">Chunks</div>
                <div style="font-size:24px;font-weight:700;color:#48bb78;">{status['chunks']}</div>
            </div>
            <div style="background:#2d3748;padding:12px;border-radius:6px;">
                <div style="font-size:10px;color:#a0aec0;text-transform:uppercase;margin-bottom:4px;">Queries</div>
                <div style="font-size:24px;font-weight:700;color:#ed8936;">{status['queries_processed']}</div>
            </div>
        </div>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid #4a5568;font-size:11px;color:#a0aec0;">
            Latency: {status['avg_latency']:.2f}s | Cache: {status['cache_hit_rate']:.0%} | {status['config']['model']}
        </div>
    </div>
    """


def change_mode(mode_selection):
    """Change retrieval mode and show/hide advanced settings"""
    global rag_system

    if not rag_system:
        return "System not initialized", False, gr.update(visible=False)

    # Map user-friendly names to internal names
    mode_map = {
        "🚀 Simple (Default)": "simple",
        "🎯 Adaptive Retrieval": "adaptive"
    }

    mode = mode_map.get(mode_selection, "simple")
    rag_system.set_mode(mode)

    # Show advanced settings checkbox only in adaptive mode
    show_advanced_checkbox = (mode == "adaptive")
    advanced_settings_visible = False  # Start collapsed

    message = f"✓ Mode set to: {mode.upper()}"

    return message, show_advanced_checkbox, gr.update(visible=advanced_settings_visible)


def toggle_advanced_settings(show_advanced):
    """Show or hide advanced settings accordion"""
    return gr.update(visible=show_advanced)


def get_current_settings() -> str:
    """Display current settings"""
    global rag_system

    if not rag_system:
        return "System not initialized"

    settings = rag_system.runtime_settings

    return f"""**Current Settings:**
- Simple K: {settings['simple_k']}
- Hybrid K: {settings['hybrid_k']}
- Advanced K: {settings['advanced_k']}
- Rerank Weight: {settings['rerank_weight']:.1f}
- RRF Constant: {settings['rrf_constant']}
- Simple Threshold: {settings['simple_threshold']}
- Moderate Threshold: {settings['moderate_threshold']}"""


def update_all_settings(simple_k, hybrid_k, advanced_k, rerank_weight,
                        rrf_constant, simple_thresh, moderate_thresh):
    """Update all settings from sliders"""
    global rag_system

    if not rag_system:
        return "System not initialized", get_current_settings()

    rag_system.update_settings(
        simple_k=simple_k,
        hybrid_k=hybrid_k,
        advanced_k=advanced_k,
        rerank_weight=rerank_weight,
        rrf_constant=rrf_constant,
        simple_threshold=simple_thresh,
        moderate_threshold=moderate_thresh
    )

    return "✓ Settings updated successfully", get_current_settings()


def reset_to_defaults():
    """Reset all settings to defaults"""
    global rag_system

    if not rag_system:
        return "System not initialized", get_current_settings(), *[None]*7

    defaults = rag_system.reset_settings()

    return (
        "✓ Settings reset to defaults",
        get_current_settings(),
        defaults['simple_k'],
        defaults['hybrid_k'],
        defaults['advanced_k'],
        defaults['rerank_weight'],
        defaults['rrf_constant'],
        defaults['simple_threshold'],
        defaults['moderate_threshold']
    )


def submit_thumbs_up():
    """Submit positive feedback"""
    global rag_system

    if not rag_system:
        return "System not initialized"

    success, message = rag_system.submit_feedback("thumbs_up")
    return message


def submit_thumbs_down():
    """Submit negative feedback"""
    global rag_system

    if not rag_system:
        return "System not initialized"

    success, message = rag_system.submit_feedback("thumbs_down")
    return message


def get_feedback_stats():
    """Get feedback statistics"""
    global rag_system

    if not rag_system or not rag_system.feedback_manager:
        return "Feedback system not initialized"

    stats = rag_system.feedback_manager.get_feedback_stats()

    output = f"""## Feedback Statistics

**Overall:**
- Total Feedback: {stats['total_feedback']}
- Thumbs Up: {stats['thumbs_up_count']}
- Thumbs Down: {stats['thumbs_down_count']}
- Satisfaction Rate: {stats['satisfaction_rate']:.1f}%

**By Query Type:**
"""

    for query_type, counts in stats['by_query_type'].items():
        total = counts['thumbs_up'] + counts['thumbs_down']
        satisfaction = (counts['thumbs_up'] / total * 100) if total > 0 else 0
        output += f"- {query_type.title()}: {satisfaction:.0f}% ({counts['thumbs_up']}/{total})\n"

    output += "\n**By Strategy:**\n"

    for strategy, counts in stats['by_strategy'].items():
        total = counts['thumbs_up'] + counts['thumbs_down']
        satisfaction = (counts['thumbs_up'] / total * 100) if total > 0 else 0
        output += f"- {strategy}: {satisfaction:.0f}% ({counts['thumbs_up']}/{total})\n"

    return output


def create_interface():
    custom_css = """
    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
    }
    .settings-box {
        background: #2d3748;
        color: #e2e8f0;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #4a5568;
    }
    /* Fix double scrollbar bug during query processing - Gradio specific */
    .chatbot {
        overflow: hidden !important;
        height: 500px !important;
    }
    .chatbot > .wrap {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        max-height: 500px !important;
    }
    .chatbot .message-row {
        overflow: visible !important;
    }
    /* Prevent body scroll when chatbot is scrolling */
    .chatbot:hover {
        overflow-y: hidden !important;
    }
    """

    global rag_system
    example_questions = rag_system.example_questions if rag_system else [
        "What are the main requirements?",
        "Can you summarize the key policies?"
    ]

    with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="Enterprise RAG") as demo:

        gr.Markdown("# 🚀 Enterprise RAG System\n### Simplified Interface - Choose Your Mode")

        status_display = gr.HTML(get_status_html())

        with gr.Row():
            # Left column - Chat interface
            with gr.Column(scale=6):
                chatbot = gr.Chatbot(
                    height=500,
                    show_label=False,
                    type='messages',
                    container=True,
                    autoscroll=True,
                    render_markdown=True,
                    bubble_full_width=False
                )

                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Ask about your documents...",
                        show_label=False,
                        scale=9,
                        container=False,
                        lines=1,
                        max_lines=10
                    )
                    submit = gr.Button("Send", scale=1, variant="primary")

                gr.Examples(
                    examples=example_questions,
                    inputs=msg
                )

                # Feedback buttons
                gr.Markdown("### Rate this answer:")
                with gr.Row():
                    thumbs_up_btn = gr.Button("👍 Thumbs Up", size="sm", variant="secondary")
                    thumbs_down_btn = gr.Button("👎 Thumbs Down", size="sm", variant="secondary")

                feedback_message = gr.Markdown("", visible=True)

                clear = gr.Button("Clear Chat", size="sm", variant="secondary")

            # Right column - Simple settings panel
            with gr.Column(scale=4):
                gr.Markdown("## ⚙️ Settings")

                # Mode selector (main control)
                mode_selector = gr.Radio(
                    choices=["🚀 Simple (Default)", "🎯 Adaptive Retrieval"],
                    value="🚀 Simple (Default)",
                    label="Retrieval Mode",
                    info="Simple = Fast & straightforward | Adaptive = Intelligent routing"
                )

                mode_status = gr.Markdown("✓ Mode: SIMPLE", elem_classes="settings-box")

                gr.Markdown("""
**🚀 Simple Mode:**
- Direct vector search
- Fast and consistent
- Best for most queries
- ~8-15 seconds response time

**🎯 Adaptive Mode:**
- Automatic query classification
- Strategy routing (simple/hybrid/advanced)
- Best for complex questions
- Variable response time based on complexity
""")

                gr.Markdown("---")

                # Advanced Settings - only visible in adaptive mode
                advanced_checkbox = gr.Checkbox(
                    label="Show Advanced Settings",
                    value=False,
                    visible=False,  # Hidden by default
                    info="Configure retrieval parameters"
                )

                with gr.Accordion("Advanced Settings", visible=False, open=False) as advanced_accordion:
                    gr.Markdown("### 📊 Number of Results (K)")
                    simple_k_slider = gr.Slider(
                        minimum=1, maximum=10, value=5, step=1,
                        label="Simple Queries K",
                        info="Results for simple lookups"
                    )

                    hybrid_k_slider = gr.Slider(
                        minimum=5, maximum=40, value=20, step=5,
                        label="Hybrid Queries K",
                        info="Results for hybrid retrieval"
                    )

                    advanced_k_slider = gr.Slider(
                        minimum=5, maximum=30, value=15, step=5,
                        label="Advanced Queries K",
                        info="Results for multi-query expansion"
                    )

                    gr.Markdown("---")
                    gr.Markdown("### ⚖️ Scoring Weights")

                    rerank_weight_slider = gr.Slider(
                        minimum=0.0, maximum=1.0, value=0.7, step=0.1,
                        label="Reranker Weight",
                        info="Higher = trust reranker more"
                    )

                    rrf_constant_slider = gr.Slider(
                        minimum=10, maximum=100, value=60, step=10,
                        label="RRF Constant",
                        info="Reciprocal Rank Fusion parameter"
                    )

                    gr.Markdown("---")
                    gr.Markdown("### 🎯 Query Classification Thresholds")

                    simple_thresh_slider = gr.Slider(
                        minimum=0, maximum=5, value=1, step=1,
                        label="Simple Threshold",
                        info="Max complexity score for simple"
                    )

                    moderate_thresh_slider = gr.Slider(
                        minimum=1, maximum=8, value=3, step=1,
                        label="Moderate Threshold",
                        info="Max complexity score for moderate"
                    )

                    gr.Markdown("---")

                    with gr.Row():
                        apply_btn = gr.Button("✓ Apply", variant="primary")
                        reset_btn = gr.Button("↺ Reset", variant="secondary")

                    settings_status = gr.Markdown("Ready", elem_classes="settings-box")
                    current_settings_display = gr.Markdown(
                        get_current_settings(),
                        elem_classes="settings-box"
                    )

                gr.Markdown("---")
                gr.Markdown("### 📊 Feedback Analytics")
                view_stats_btn = gr.Button("View Feedback Stats", variant="secondary")
                feedback_stats_display = gr.Markdown("Click to load stats", elem_classes="settings-box")

        # Event handlers
        async def respond(message, history):
            if not message.strip():
                return history, ""

            bot_message = await process_query(message, history)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": bot_message})
            return history, ""

        def clear_chat():
            """Clear chat and conversation memory"""
            global rag_system
            if rag_system:
                rag_system.clear_conversation()
            return None

        # Chat interactions
        msg.submit(respond, [msg, chatbot], [chatbot, msg])
        submit.click(respond, [msg, chatbot], [chatbot, msg])
        clear.click(clear_chat, None, chatbot, queue=False)

        # Mode selector
        mode_selector.change(
            change_mode,
            inputs=[mode_selector],
            outputs=[mode_status, advanced_checkbox, advanced_accordion]
        )

        # Advanced settings toggle
        advanced_checkbox.change(
            toggle_advanced_settings,
            inputs=[advanced_checkbox],
            outputs=[advanced_accordion]
        )

        # Settings interactions
        all_sliders = [
            simple_k_slider, hybrid_k_slider, advanced_k_slider,
            rerank_weight_slider, rrf_constant_slider,
            simple_thresh_slider, moderate_thresh_slider
        ]

        apply_btn.click(
            update_all_settings,
            inputs=all_sliders,
            outputs=[settings_status, current_settings_display]
        )

        reset_btn.click(
            reset_to_defaults,
            inputs=[],
            outputs=[settings_status, current_settings_display] + all_sliders
        )

        # Feedback buttons
        thumbs_up_btn.click(
            submit_thumbs_up,
            inputs=[],
            outputs=[feedback_message]
        )

        thumbs_down_btn.click(
            submit_thumbs_down,
            inputs=[],
            outputs=[feedback_message]
        )

        # Feedback stats
        view_stats_btn.click(
            get_feedback_stats,
            inputs=[],
            outputs=[feedback_stats_display]
        )

        # Auto-refresh status on load
        demo.load(get_status_html, None, status_display)

    return demo


async def main():
    logger.info("Starting Enterprise RAG System...")

    success, message = await initialize_system()

    if not success:
        logger.error(f"Initialization failed: {message}")
        return

    logger.info("System initialized successfully")

    demo = create_interface()
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    asyncio.run(main())
