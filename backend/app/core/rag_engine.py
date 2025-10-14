"""
RAG Engine Wrapper - Wraps existing RAG components for FastAPI
CRITICAL: This does NOT modify existing code, only imports and wraps it
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

# Add _src directory to Python path to import existing modules
# Path calculation: /app/app/core/rag_engine.py -> /app/_src
src_path = Path(__file__).parent.parent.parent / "_src"
sys.path.insert(0, str(src_path))

# Import existing RAG components (NO MODIFICATIONS)
from config import SystemConfig, load_config
from adaptive_retrieval import AdaptiveRetriever, AdaptiveAnswerGenerator, RetrievalResult
from conversation_memory import ConversationMemory
from cache_next_gen import NextGenCacheManager
from embedding_cache import EmbeddingCache
from llm_factory import create_llm
from collection_metadata import CollectionMetadata

# LangChain imports
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM  # Updated to use new langchain-ollama package
from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.docstore.document import Document

# Import timing utilities
from ..utils.timing import StageTimer

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Async wrapper for existing RAG system components.

    This class wraps the existing RAG code without modifying it,
    providing a clean async API for FastAPI endpoints.

    Architecture:
    - Initializes all existing components (vectorstore, BM25, LLM, cache, memory)
    - Provides async query processing with mode routing
    - Manages conversation state
    - Handles caching transparently
    """

    # Default settings (same as app.py)
    DEFAULT_SETTINGS = {
        'simple_k': 5,
        'hybrid_k': 20,
        'advanced_k': 15,
        'rerank_weight': 0.7,
        'simple_threshold': 1,
        'moderate_threshold': 3,
        'rrf_constant': 60
    }

    def __init__(self, config: Optional[SystemConfig] = None):
        """
        Initialize RAG Engine wrapper.

        Args:
            config: Optional SystemConfig, if None will load from environment
        """
        self.config = config or load_config()

        # Core components (initialized in async initialize())
        self.vectorstore: Optional[Chroma] = None
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.llm: Optional[OllamaLLM] = None
        self.embeddings: Optional[OllamaEmbeddings] = None
        self.embedding_cache: Optional[EmbeddingCache] = None

        # RAG engines
        self.retrieval_engine: Optional[AdaptiveRetriever] = None
        self.answer_generator: Optional[AdaptiveAnswerGenerator] = None
        self.collection_metadata: Optional[CollectionMetadata] = None

        # Infrastructure
        self.cache_manager: Optional[NextGenCacheManager] = None
        self.conversation_memory: Optional[ConversationMemory] = None

        # State
        self.initialized = False
        self.runtime_settings = self.DEFAULT_SETTINGS.copy()
        self.current_mode = "simple"  # Default mode

        # Statistics
        self.query_count = 0
        self.start_time = datetime.now()

        logger.info("RAGEngine wrapper created")

    async def initialize(self) -> Tuple[bool, str]:
        """
        Initialize all RAG components asynchronously.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.info("=" * 60)
            logger.info("INITIALIZING RAG ENGINE")
            logger.info("=" * 60)

            # 1. Initialize embedding cache (do this first for Redis connection)
            logger.info("\n1. Initializing embedding cache...")
            redis_url = f"redis://{self.config.cache.redis_host}:{self.config.cache.redis_port}"
            self.embedding_cache = EmbeddingCache(
                redis_url=redis_url,
                ttl=86400 * 7,  # 7 days
                key_prefix="emb:v1:"
            )
            await self.embedding_cache.connect()
            logger.info(f"✓ Embedding cache connected to {redis_url}")

            # 2. Initialize embeddings
            logger.info("\n2. Initializing embedding model...")
            logger.info(f"   Model: {self.config.embedding.model_name}")
            logger.info(f"   Type: {self.config.embedding.model_type}")

            if self.config.embedding.model_type == "huggingface":
                # UPGRADED: Using state-of-the-art HuggingFace embedding model
                import torch
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                logger.info(f"   Device: {device}")

                self.embeddings = HuggingFaceEmbeddings(
                    model_name=self.config.embedding.model_name,
                    model_kwargs={'device': device},
                    encode_kwargs={
                        'normalize_embeddings': self.config.embedding.normalize_embeddings,
                        'batch_size': self.config.embedding.batch_size
                    }
                )
            else:
                # Fallback to Ollama embeddings
                self.embeddings = OllamaEmbeddings(
                    model=self.config.embedding.model_name,
                    base_url=self.config.ollama_host
                )

            # Test embeddings
            test_embed = await asyncio.to_thread(
                self.embeddings.embed_query,
                "test"
            )
            logger.info(f"✓ Embeddings ready (dim: {len(test_embed)})")

            # 3. Initialize cache manager
            logger.info("\n3. Initializing cache system...")

            def embed_for_cache(text: str) -> List[float]:
                """Sync wrapper for embeddings (for cache)"""
                return self.embeddings.embed_query(text)

            self.cache_manager = NextGenCacheManager(
                self.config,
                embeddings_func=embed_for_cache
            )
            logger.info("✓ Cache system ready")

            # 4. Load vectorstore
            logger.info("\n4. Loading vector database...")
            if not self.config.vector_db_dir.exists():
                return False, f"Vector database not found at {self.config.vector_db_dir}"

            self.vectorstore = Chroma(
                persist_directory=str(self.config.vector_db_dir),
                embedding_function=self.embeddings
            )
            logger.info("✓ Vector store loaded")

            # 4.5. Initialize collection metadata
            logger.info("\n4.5. Initializing collection metadata...")
            try:
                from pathlib import Path as PathLib
                metadata_path = PathLib(self.config.scope_detection.metadata_path)

                self.collection_metadata = CollectionMetadata.load_or_compute(
                    vectorstore=self.vectorstore,
                    embeddings=self.embeddings,
                    llm=None,  # Will be set later
                    metadata_path=metadata_path,
                    force_recompute=self.config.scope_detection.force_recompute
                )
                logger.info(f"✓ Collection metadata ready")
            except Exception as e:
                logger.warning(f"⚠ Collection metadata initialization skipped: {e}")
                logger.warning("  Out-of-scope detection will be disabled")
                self.collection_metadata = None

            # 5. Load BM25 retriever
            logger.info("\n5. Loading BM25 retriever...")
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
                logger.info(f"✓ BM25 ready ({len(texts)} chunks)")
            else:
                logger.warning("⚠ BM25 metadata not found, using dummy retriever")
                self.bm25_retriever = BM25Retriever.from_documents([
                    Document(page_content="dummy")
                ])

            # 6. Connect to LLM (using LLM factory for vLLM support)
            logger.info("\n6. Connecting to LLM...")
            self.llm = create_llm(self.config, test_connection=False)

            # Skip LLM test during initialization to avoid vLLM first-inference delay
            # The LLM will be tested during the first actual query
            logger.info("✓ LLM ready (will be tested on first query)")

            # 7. Initialize conversation memory
            logger.info("\n7. Initializing conversation memory...")
            self.conversation_memory = ConversationMemory(
                llm=self.llm,
                max_exchanges=10,
                summarization_threshold=5,
                enable_summarization=True
            )
            logger.info("✓ Conversation memory ready")

            # 8. Initialize retrieval engines
            logger.info("\n8. Initializing retrieval engines...")
            self.retrieval_engine = AdaptiveRetriever(
                vectorstore=self.vectorstore,
                bm25_retriever=self.bm25_retriever,
                llm=self.llm,
                config=self.config,
                runtime_settings=self.runtime_settings
            )
            self.answer_generator = AdaptiveAnswerGenerator(
                llm=self.llm,
                embeddings=self.embeddings,
                collection_metadata=self.collection_metadata,
                scope_config=self.config.scope_detection
            )
            logger.info("✓ Retrieval engines ready")

            self.initialized = True
            logger.info("\n" + "=" * 60)
            logger.info("RAG ENGINE READY")
            logger.info("=" * 60)

            return True, "RAG Engine initialized successfully"

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False, f"Initialization failed: {str(e)}"

    async def query(
        self,
        question: str,
        mode: str = "simple",
        use_context: bool = True
    ) -> Dict:
        """
        Process a query using the RAG system.

        Args:
            question: User's question
            mode: Retrieval mode ("simple" or "adaptive")
            use_context: Whether to use conversation context

        Returns:
            Dict with answer, sources, metadata (including detailed timing), and optional explanation
        """
        if not self.initialized:
            return {
                "answer": "RAG Engine not initialized",
                "sources": [],
                "metadata": {
                    "strategy_used": "none",
                    "query_type": "none",
                    "mode": mode,
                    "processing_time_ms": 0
                },
                "error": True
            }

        # Initialize stage timer
        timer = StageTimer()
        timer.start()

        try:
            # Stage 1: Cache lookup
            timer.start_stage("cache_lookup")
            cached_result = self.cache_manager.get_query_result(
                question,
                {"model": self.config.llm.model_name}
            )
            timer.end_stage()

            if cached_result:
                logger.info(f"[CACHE HIT] {question[:50]}...")
                timing_breakdown = timer.get_breakdown()
                cached_result["metadata"]["processing_time_ms"] = timing_breakdown["total_ms"]
                cached_result["metadata"]["timing_breakdown"] = timing_breakdown
                cached_result["metadata"]["cache_hit"] = True
                return cached_result

            # Stage 2: Context enhancement
            timer.start_stage("context_enhancement")
            enhanced_query = question
            if use_context and self.conversation_memory:
                enhanced_query, _ = self.conversation_memory.get_relevant_context_for_query(
                    question,
                    max_exchanges=3
                )
            timer.end_stage()

            # Stage 3: Document retrieval (with sub-stage timing)
            if mode == "simple":
                retrieval_result = await self._simple_retrieve(enhanced_query, timer)
            else:
                timer.start_stage("retrieval")
                retrieval_result = await self.retrieval_engine.retrieve(
                    query=enhanced_query
                )
                timer.end_stage()

            # Check if we have results
            if not retrieval_result.documents:
                timing_breakdown = timer.get_breakdown()
                return {
                    "answer": "I couldn't find any relevant documents to answer your question.",
                    "sources": [],
                    "metadata": {
                        "strategy_used": "simple_dense" if mode == "simple" else retrieval_result.strategy_used,
                        "query_type": "simple" if mode == "simple" else retrieval_result.query_type,
                        "mode": mode,
                        "processing_time_ms": timing_breakdown["total_ms"],
                        "timing_breakdown": timing_breakdown,
                        "cache_hit": False
                    },
                    "error": False
                }

            # Stage 4: Answer generation
            timer.start_stage("answer_generation")
            answer = await self.answer_generator.generate(
                question,
                retrieval_result
            )
            timer.end_stage()

            # Stage 5: Post-processing (memory & cache)
            timer.start_stage("post_processing")

            # Get final timing breakdown
            timing_breakdown = timer.get_breakdown()

            result = {
                "answer": answer,
                "sources": self._format_sources(retrieval_result),
                "metadata": {
                    "strategy_used": "simple_dense" if mode == "simple" else retrieval_result.strategy_used,
                    "query_type": "simple" if mode == "simple" else retrieval_result.query_type,
                    "mode": mode,
                    "processing_time_ms": timing_breakdown["total_ms"],
                    "timing_breakdown": timing_breakdown,
                    "cache_hit": False
                },
                "explanation": (
                    retrieval_result.explanation.to_dict()
                    if hasattr(retrieval_result, 'explanation') and retrieval_result.explanation
                    else None
                ),
                "error": False
            }

            # Store in conversation memory
            if self.conversation_memory:
                self.conversation_memory.add(
                    query=question,
                    response=answer,
                    retrieved_docs=retrieval_result.documents,
                    query_type="simple" if mode == "simple" else retrieval_result.query_type,
                    strategy_used="simple_dense" if mode == "simple" else retrieval_result.strategy_used
                )

            # Cache result
            self.cache_manager.put_query_result(
                question,
                {"model": self.config.llm.model_name},
                result
            )

            timer.end_stage()  # End post-processing

            self.query_count += 1
            logger.info(f"Query processed in {timing_breakdown['total_ms']:.1f}ms - Breakdown: {timing_breakdown['stages']}")

            return result

        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)
            timing_breakdown = timer.get_breakdown()

            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "sources": [],
                "metadata": {
                    "strategy_used": "error",
                    "query_type": "error",
                    "mode": mode,
                    "processing_time_ms": timing_breakdown["total_ms"],
                    "timing_breakdown": timing_breakdown,
                    "cache_hit": False
                },
                "error": True
            }

    async def get_cached_embedding(self, text: str) -> List[float]:
        """Get embedding with cache support"""
        if not self.embedding_cache:
            # No cache, use direct embedding
            return await asyncio.to_thread(
                self.embeddings.embed_query,
                text
            )

        # Try cache first
        cached = await self.embedding_cache.get(text)
        if cached is not None:
            return cached.tolist()

        # Cache miss - generate embedding
        embedding = await asyncio.to_thread(
            self.embeddings.embed_query,
            text
        )

        # Store in cache
        import numpy as np
        await self.embedding_cache.set(text, np.array(embedding, dtype=np.float32))

        return embedding

    async def _simple_retrieve(self, query: str, timer: Optional[StageTimer] = None) -> RetrievalResult:
        """Simple retrieval using direct dense vector search with sub-stage timing"""

        # Sub-stage: Retrieval (embedding + vector search combined)
        if timer:
            timer.start_stage("retrieval.dense_search")

        # Chroma computes embedding internally in similarity_search_with_score
        docs = await asyncio.to_thread(
            self.vectorstore.similarity_search_with_score,
            query,
            k=self.runtime_settings['simple_k']
        )

        if timer:
            timer.end_stage()

        # Sub-stage: Score normalization
        if timer:
            timer.start_stage("retrieval.score_normalization")

        documents = [doc for doc, score in docs]
        # Convert L2 distance to similarity score (0-1 range)
        # Lower distance = higher similarity
        # Use exponential decay to convert distance to similarity
        scores = [max(0.0, 1.0 / (1.0 + score)) for doc, score in docs]

        if timer:
            timer.end_stage()

        return RetrievalResult(
            documents=documents,
            scores=scores,
            query_type="simple",
            strategy_used="simple_dense",
            explanation=None
        )

    def _format_sources(self, retrieval_result: RetrievalResult) -> List[Dict]:
        """Format source documents for API response"""
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
                "excerpt": doc.page_content[:250] + "..." if len(doc.page_content) > 250 else doc.page_content,
                "metadata": {
                    k: v for k, v in doc.metadata.items()
                    if k in ['page_number', 'chunk_index']
                }
            })

        return sources

    def clear_conversation(self) -> Tuple[bool, str]:
        """Clear conversation memory"""
        try:
            if self.conversation_memory:
                self.conversation_memory.clear()
                logger.info("Conversation memory cleared")
                return True, "Conversation memory cleared successfully"
            return False, "Conversation memory not initialized"
        except Exception as e:
            logger.error(f"Failed to clear conversation: {e}")
            return False, f"Error clearing conversation: {str(e)}"

    def update_settings(self, **kwargs) -> Tuple[bool, str, Dict]:
        """
        Update runtime settings.

        Returns:
            Tuple of (success, message, current_settings)
        """
        try:
            updated = []
            for key, value in kwargs.items():
                if key in self.DEFAULT_SETTINGS and value is not None:
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
                    updated.append(key)

            # Update retrieval engine settings
            if self.retrieval_engine:
                self.retrieval_engine.runtime_settings = self.runtime_settings

            message = f"Updated settings: {', '.join(updated)}" if updated else "No settings changed"
            logger.info(message)

            return True, message, self.runtime_settings.copy()

        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False, f"Error updating settings: {str(e)}", self.runtime_settings.copy()

    def reset_settings(self) -> Dict:
        """Reset settings to defaults"""
        self.runtime_settings = self.DEFAULT_SETTINGS.copy()
        if self.retrieval_engine:
            self.retrieval_engine.runtime_settings = self.runtime_settings
        logger.info("Settings reset to defaults")
        return self.runtime_settings.copy()

    async def query_stream(
        self,
        question: str,
        mode: str = "simple",
        use_context: bool = True
    ):
        """
        Stream query processing with real-time token generation.

        Yields chunks as they are generated:
        - {"type": "sources", "content": [...]} - Retrieved sources
        - {"type": "token", "content": "..."} - Generated tokens
        - {"type": "metadata", "content": {...}} - Processing metadata
        - {"type": "done"} - Completion signal
        """
        if not self.initialized:
            yield {"type": "error", "content": "RAG Engine not initialized"}
            return

        start_time = asyncio.get_event_loop().time()

        try:
            # Check cache first
            cached_result = self.cache_manager.get_query_result(
                question,
                {"model": self.config.llm.model_name}
            )

            if cached_result:
                logger.info(f"[CACHE HIT STREAM] {question[:50]}...")
                # Send cached result as rapid stream
                yield {"type": "sources", "content": cached_result["sources"]}

                # Stream the answer token by token for consistency
                answer = cached_result["answer"]
                for i, char in enumerate(answer):
                    yield {"type": "token", "content": char}
                    if i % 5 == 0:  # Small delay every 5 chars for smooth display
                        await asyncio.sleep(0.01)

                yield {"type": "metadata", "content": cached_result["metadata"]}
                yield {"type": "done"}
                return

            # Enhance query with context if enabled
            enhanced_query = question
            if use_context and self.conversation_memory:
                enhanced_query, _ = self.conversation_memory.get_relevant_context_for_query(
                    question,
                    max_exchanges=3
                )

            # Perform retrieval
            if mode == "simple":
                retrieval_result = await self._simple_retrieve(enhanced_query)
            else:
                retrieval_result = await self.retrieval_engine.retrieve(
                    query=enhanced_query
                )

            # Send sources immediately
            yield {
                "type": "sources",
                "content": self._format_sources(retrieval_result)
            }

            # Stream the answer generation
            answer_tokens = []

            async for token in self._stream_answer(question, retrieval_result):
                yield {"type": "token", "content": token}
                answer_tokens.append(token)

            # Finalize
            full_answer = "".join(answer_tokens)
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000

            metadata = {
                "strategy_used": "simple_dense" if mode == "simple" else retrieval_result.strategy_used,
                "query_type": "simple" if mode == "simple" else retrieval_result.query_type,
                "mode": mode,
                "processing_time_ms": processing_time
            }

            yield {"type": "metadata", "content": metadata}
            yield {"type": "done"}

            # Store in memory and cache
            if self.conversation_memory:
                self.conversation_memory.add(
                    query=question,
                    response=full_answer,
                    retrieved_docs=retrieval_result.documents,
                    query_type="simple" if mode == "simple" else retrieval_result.query_type,
                    strategy_used="simple_dense" if mode == "simple" else retrieval_result.strategy_used
                )

            # Cache the full result
            result = {
                "answer": full_answer,
                "sources": self._format_sources(retrieval_result),
                "metadata": metadata,
                "error": False
            }
            self.cache_manager.put_query_result(
                question,
                {"model": self.config.llm.model_name},
                result
            )

            self.query_count += 1

        except Exception as e:
            logger.error(f"Stream query error: {e}", exc_info=True)
            yield {"type": "error", "content": str(e)}

    async def _stream_answer(self, question: str, retrieval_result: RetrievalResult):
        """Stream answer generation token by token"""
        try:
            # Use the LLM's streaming capability
            prompt = self.answer_generator._build_prompt(question, retrieval_result)

            # Stream from LLM
            for chunk in self.llm.stream(prompt):
                yield chunk

        except Exception as e:
            logger.error(f"Answer streaming error: {e}", exc_info=True)
            yield f"[Error: {str(e)}]"

    def get_status(self) -> Dict:
        """Get system status"""
        if not self.initialized:
            return {
                "status": "offline",
                "message": "RAG Engine not initialized",
                "components": {}
            }

        uptime = datetime.now() - self.start_time

        components = {
            "vectorstore": "ready" if self.vectorstore else "offline",
            "llm": "ready" if self.llm else "offline",
            "bm25_retriever": "ready" if self.bm25_retriever else "offline",
            "cache": "ready" if self.cache_manager else "offline",
            "conversation_memory": "ready" if self.conversation_memory else "offline",
        }

        return {
            "status": "operational",
            "message": "All systems operational",
            "components": components,
            "uptime_seconds": uptime.total_seconds(),
            "query_count": self.query_count,
            "current_mode": self.current_mode,
            "config": {
                "llm_model": self.config.llm.model_name,
                "embedding_model": self.config.embedding.model_name,
                "ollama_host": self.config.ollama_host
            }
        }
