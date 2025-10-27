"""
RAG Engine Wrapper - Wraps existing RAG components for FastAPI
CRITICAL: This does NOT modify existing code, only imports and wraps it
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

# Initialize logger FIRST (needed for import error handling)
logger = logging.getLogger(__name__)

# Add _src directory to Python path to import existing modules
# Path calculation: /app/app/core/rag_engine.py -> /app/_src
src_path = Path(__file__).parent.parent.parent / "_src"
sys.path.insert(0, str(src_path))

# Import existing RAG components (NO MODIFICATIONS)
from config import SystemConfig, load_config, RerankPreset
from adaptive_retrieval import AdaptiveRetriever, AdaptiveAnswerGenerator, RetrievalResult
from conversation_memory import ConversationMemory
from cache_next_gen import NextGenCacheManager
from embedding_cache import EmbeddingCache
from llm_factory import create_llm
from query_prefetcher import QueryPrefetcher

# CRITICAL FIX: Import optimized metadata with fallback to standard version
try:
    from collection_metadata_optimized import CollectionMetadataOptimized as CollectionMetadata
    logger.info("✓ Using OPTIMIZED metadata system with smart caching")
except ImportError as e:
    logger.warning(f"Failed to import optimized metadata (falling back to standard): {e}")
    from collection_metadata import CollectionMetadata
    logger.warning("⚠ Using standard metadata system (slower startup)")

from confidence_scoring import ConfidenceScorer

# LangChain imports
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM  # Updated to use new langchain-ollama package
from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.docstore.document import Document

# Import Qdrant vector store
from vector_store_qdrant import QdrantVectorStore

# Import timing utilities
from ..utils.timing import StageTimer


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

    # Default settings (ENHANCED for better recall)
    DEFAULT_SETTINGS = {
        'simple_k': 7,  # INCREASED from 5 for better recall
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
        self.vectorstore: Optional[Chroma | QdrantVectorStore] = None  # Support both Chroma and Qdrant
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.llm: Optional[OllamaLLM] = None
        self.embeddings: Optional[OllamaEmbeddings] = None
        self.embedding_cache: Optional[EmbeddingCache] = None

        # RAG engines
        self.retrieval_engine: Optional[AdaptiveRetriever] = None
        self.answer_generator: Optional[AdaptiveAnswerGenerator] = None
        self.collection_metadata: Optional[CollectionMetadata] = None
        self.confidence_scorer: Optional[ConfidenceScorer] = None

        # Infrastructure
        self.cache_manager: Optional[NextGenCacheManager] = None
        self.conversation_memory: Optional[ConversationMemory] = None
        self.query_prefetcher: Optional[QueryPrefetcher] = None

        # Model Management (HOTSWAP SUPPORT)
        self.model_manager = None  # Optional ModelManager for runtime model switching

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
        Initialize all RAG components asynchronously with PARALLEL LOADING.

        OPTIMIZATION: Components are loaded in parallel groups to minimize startup time.
        Expected speedup: 14-18 seconds (78s → 60-64s)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.info("=" * 60)
            logger.info("INITIALIZING RAG ENGINE (PARALLEL MODE)")
            logger.info("=" * 60)

            # ============================================================
            # PARALLEL GROUP 1: Independent components (run concurrently)
            # ============================================================
            logger.info("\n[PARALLEL GROUP 1] Loading independent components...")

            async def init_embedding_cache():
                """Initialize embedding cache"""
                logger.info("  → Connecting to Redis cache...")
                redis_url = f"redis://{self.config.cache.redis_host}:{self.config.cache.redis_port}"
                cache = EmbeddingCache(
                    redis_url=redis_url,
                    ttl=86400 * 7,  # 7 days
                    key_prefix="emb:v1:"
                )
                await cache.connect()
                logger.info(f"  ✓ Redis cache connected")
                return cache

            async def init_embeddings():
                """Initialize embedding model"""
                logger.info("  → Loading embedding model...")
                logger.info(f"     Model: {self.config.embedding.model_name}")

                if self.config.embedding.model_type == "huggingface":
                    import torch
                    # CRITICAL FIX: Force CPU for embeddings (RTX 5080 sm_120 incompatible with PyTorch 2.5.1)
                    # PyTorch pre-built binaries only support up to sm_90 (RTX 4090)
                    # Embedding is fast enough on CPU (~50ms for 1024-dim BGE-large)
                    device = 'cpu'
                    logger.info(f"     Device: {device}")

                    embeddings = HuggingFaceEmbeddings(
                        model_name=self.config.embedding.model_name,
                        model_kwargs={'device': device},
                        encode_kwargs={
                            'normalize_embeddings': self.config.embedding.normalize_embeddings,
                            'batch_size': self.config.embedding.batch_size
                        }
                    )
                else:
                    embeddings = OllamaEmbeddings(
                        model=self.config.embedding.model_name,
                        base_url=self.config.ollama_host
                    )

                # Test embeddings
                test_embed = await asyncio.to_thread(
                    embeddings.embed_query,
                    "test"
                )
                logger.info(f"  ✓ Embeddings ready (dim: {len(test_embed)})")
                return embeddings

            async def load_bm25_data():
                """Load BM25 metadata file"""
                logger.info("  → Loading BM25 metadata...")
                metadata_file = self.config.vector_db_dir / "chunk_metadata.json"

                if metadata_file.exists():
                    import json
                    data = await asyncio.to_thread(
                        lambda: json.load(open(metadata_file, 'r'))
                    )
                    logger.info(f"  ✓ BM25 metadata loaded ({len(data['texts'])} chunks)")
                    return data
                else:
                    logger.warning("  ⚠ BM25 metadata not found")
                    return None

            async def init_llm():
                """Initialize LLM client (skip if ModelManager is set)"""
                if self.model_manager:
                    # ModelManager already initialized the LLM
                    logger.info("  → Using LLM from ModelManager (hotswap enabled)")
                    llm = self.model_manager.get_llm()
                    logger.info("  ✓ LLM from ModelManager")
                    return llm
                else:
                    # Legacy path: create LLM directly
                    logger.info("  → Creating LLM client...")
                    llm = await asyncio.to_thread(
                        create_llm, self.config, False
                    )
                    logger.info("  ✓ LLM client created")
                    return llm

            # Run Group 1 in parallel
            results = await asyncio.gather(
                init_embedding_cache(),
                init_embeddings(),
                load_bm25_data(),
                init_llm(),
                return_exceptions=True
            )

            # Unpack results (with error handling)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Parallel init failed for component {i}: {result}")
                    raise result

            self.embedding_cache, self.embeddings, bm25_data, llm_result = results

            # Set LLM (either from ModelManager or direct init)
            if not self.model_manager:
                self.llm = llm_result
            # else: self.llm already set from model_manager in main.py

            logger.info("[GROUP 1] ✓ All independent components loaded")

            # ============================================================
            # PARALLEL GROUP 2: Components that depend on Group 1
            # ============================================================
            logger.info("\n[PARALLEL GROUP 2] Loading dependent components...")

            async def init_cache_manager():
                """Initialize cache manager (needs embeddings)"""
                logger.info("  → Initializing cache system...")

                def embed_for_cache(text: str) -> List[float]:
                    return self.embeddings.embed_query(text)

                cache_manager = NextGenCacheManager(
                    self.config,
                    embeddings_func=embed_for_cache
                )
                logger.info("  ✓ Cache system ready")
                return cache_manager

            async def init_vectorstore():
                """Initialize vectorstore (needs embeddings) - supports Chroma or Qdrant"""
                logger.info("  → Loading vector database...")
                logger.info(f"     Vector store type: {self.config.vector_store}")

                if self.config.vector_store == "qdrant":
                    # Initialize Qdrant vector store
                    logger.info("     Qdrant host: qdrant:6333")

                    vectorstore = QdrantVectorStore(
                        collection_name="documents",
                        vector_size=self.config.embedding.dimension,  # 1024 for BGE-large
                        host="qdrant",
                        port=6333,
                        use_async=True,
                        enable_sparse=True  # QUICK WIN #1: Enable BM25 hybrid search (+5% accuracy)
                    )

                    # Initialize connection
                    await vectorstore.initialize()
                    logger.info("  ✓ Qdrant vector store loaded")
                    return vectorstore

                else:
                    # Use ChromaDB (legacy/fallback)
                    if not self.config.vector_db_dir.exists():
                        raise FileNotFoundError(f"Vector database not found at {self.config.vector_db_dir}")

                    vectorstore = await asyncio.to_thread(
                        Chroma,
                        persist_directory=str(self.config.vector_db_dir),
                        embedding_function=self.embeddings
                    )
                    logger.info("  ✓ ChromaDB vector store loaded")
                    return vectorstore

            async def init_bm25_retriever(data):
                """Initialize BM25 retriever (needs BM25 data)"""
                logger.info("  → Building BM25 retriever...")

                if data:
                    texts = data['texts']
                    metadata = data['metadata']
                    bm25_docs = [
                        Document(page_content=text, metadata=meta)
                        for text, meta in zip(texts, metadata)
                    ]
                    retriever = await asyncio.to_thread(
                        BM25Retriever.from_documents, bm25_docs
                    )
                    retriever.k = self.config.retrieval.initial_k
                    logger.info(f"  ✓ BM25 ready")
                else:
                    logger.warning("  ⚠ Using dummy BM25 retriever")
                    retriever = BM25Retriever.from_documents([
                        Document(page_content="dummy")
                    ])
                return retriever

            async def warmup_llm():
                """Warm up LLM model (needs LLM client)"""
                logger.info("  → Skipping LLM warmup (llama.cpp loads on first use)")
                logger.info("     Model will be loaded into VRAM on first query")
                return True

            # Run Group 2 in parallel
            results = await asyncio.gather(
                init_cache_manager(),
                init_vectorstore(),
                init_bm25_retriever(bm25_data),
                warmup_llm(),
                return_exceptions=True
            )

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Parallel init failed for component {i}: {result}")
                    raise result

            self.cache_manager, self.vectorstore, self.bm25_retriever, _ = results
            logger.info("[GROUP 2] ✓ All dependent components loaded")

            # ============================================================
            # PARALLEL GROUP 3: Components needing vectorstore + LLM
            # ============================================================
            logger.info("\n[PARALLEL GROUP 3] Loading final components...")

            async def init_metadata():
                """Initialize collection metadata (needs vectorstore + embeddings)"""
                logger.info("  → Initializing collection metadata...")
                try:
                    from pathlib import Path as PathLib
                    metadata_path = PathLib(self.config.scope_detection.metadata_path)

                    metadata = await asyncio.to_thread(
                        CollectionMetadata.load_or_compute,
                        vectorstore=self.vectorstore,
                        embeddings=self.embeddings,
                        llm=None,
                        metadata_path=metadata_path,
                        force_recompute=self.config.scope_detection.force_recompute
                    )
                    logger.info("  ✓ Collection metadata ready")
                    return metadata
                except Exception as e:
                    logger.warning(f"  ⚠ Metadata init skipped: {e}")
                    return None

            async def init_conversation_memory():
                """Initialize conversation memory (needs LLM)"""
                logger.info("  → Initializing conversation memory...")
                memory = ConversationMemory(
                    llm=self.llm,
                    max_exchanges=10,
                    summarization_threshold=5,
                    enable_summarization=True
                )
                logger.info("  ✓ Conversation memory ready")
                return memory

            async def init_confidence_scorer():
                """Initialize confidence scorer (needs embeddings)"""
                logger.info("  → Initializing confidence scorer...")
                try:
                    scorer = ConfidenceScorer(embeddings=self.embeddings)
                    logger.info("  ✓ Confidence scorer ready")
                    return scorer
                except Exception as e:
                    logger.warning(f"  ⚠ Confidence scorer failed: {e}")
                    return None

            # Run Group 3 in parallel
            results = await asyncio.gather(
                init_metadata(),
                init_conversation_memory(),
                init_confidence_scorer(),
                return_exceptions=True
            )

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Parallel init failed for component {i}: {result}")
                    raise result

            self.collection_metadata, self.conversation_memory, self.confidence_scorer = results
            logger.info("[GROUP 3] ✓ Final components loaded")

            # ============================================================
            # SEQUENTIAL: Retrieval engines (need everything)
            # ============================================================
            logger.info("\n[FINAL] Initializing retrieval engines...")
            logger.info(f"[DEBUG] self.llm type: {type(self.llm)}, value: {self.llm is not None}")
            logger.info(f"[DEBUG] self.config has query_transformation: {hasattr(self.config, 'query_transformation')}")
            if hasattr(self.config, 'query_transformation'):
                logger.info(f"[DEBUG] query_transformation.enable_hyde: {self.config.query_transformation.enable_hyde}")
            self.retrieval_engine = AdaptiveRetriever(
                embedding_model=self.embeddings,
                vector_store=self.vectorstore,
                embedding_cache=self.embedding_cache if hasattr(self, 'embedding_cache') else None,
                use_cache=True,
                config=self.config,  # Pass config for reranking and multi-query settings
                llm_service=self.llm  # ENABLED: Advanced RAG features (HyDE, Multi-Query, LLM Reranking) for 90% accuracy target
            )
            self.answer_generator = AdaptiveAnswerGenerator(
                llm_model=self.llm
            )
            logger.info("✓ Retrieval engines ready")

            # ============================================================
            # L5: Query Prefetcher (runs in background)
            # ============================================================
            logger.info("\n[L5] Initializing query prefetcher...")
            try:
                self.query_prefetcher = QueryPrefetcher(
                    embedding_cache=self.embedding_cache,
                    retrieval_engine=self.retrieval_engine,
                    max_concurrent_prefetches=3,
                    prediction_window_size=10,
                    enable_auto_prefetch=True
                )
                await self.query_prefetcher.start()
                logger.info("✓ Query prefetcher started (L5 cache layer active)")
            except Exception as e:
                logger.warning(f"⚠ Query prefetcher failed to initialize: {e}")
                self.query_prefetcher = None

            self.initialized = True
            logger.info("\n" + "=" * 60)
            logger.info("RAG ENGINE READY (PARALLEL INIT COMPLETE)")
            logger.info("=" * 60)

            return True, "RAG Engine initialized successfully"

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False, f"Initialization failed: {str(e)}"

    async def query(
        self,
        question: str,
        mode: str = "simple",
        use_context: bool = True,
        rerank_preset: Optional[str] = "quality"
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
        # DEBUG: Entry point - method body starting
        logger.info(f"[DEBUG RAG_ENGINE] query() method entered, question='{question[:50]}...', mode={mode}")

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

        logger.info(f"[DEBUG RAG_ENGINE] Passed initialization check, creating timer...")

        # Convert rerank preset to count
        llm_rerank_count = None
        if rerank_preset:
            preset_map = {
                "quick": 2,
                "quality": 3,
                "deep": 5
            }
            llm_rerank_count = preset_map.get(rerank_preset, 3)
            logger.info(f"[RAG_ENGINE] Rerank preset '{rerank_preset}' → {llm_rerank_count} docs")

        # Initialize stage timer
        timer = StageTimer()
        timer.start()

        logger.info(f"[DEBUG RAG_ENGINE] Timer created, entering try block...")

        try:
            # OPTIMIZATION: Stage 1 - Cache lookup (ALWAYS check first for sub-ms response)
            logger.info(f"[DEBUG RAG_ENGINE] Starting cache lookup...")
            timer.start_stage("cache_lookup")
            cached_result = self.cache_manager.get_query_result(
                question,
                {"model": self.config.llm.model_name}
            )
            logger.info(f"[DEBUG RAG_ENGINE] Cache lookup completed, result={'HIT' if cached_result else 'MISS'}")
            timer.end_stage()

            # PERFORMANCE: Early exit on cache hit (0.86ms average)
            if cached_result:
                logger.info(f"[CACHE HIT - FAST PATH] {question[:50]}...")
                timing_breakdown = timer.get_breakdown()
                cached_result["metadata"]["processing_time_ms"] = timing_breakdown["total_ms"]
                cached_result["metadata"]["timing_breakdown"] = timing_breakdown
                cached_result["metadata"]["cache_hit"] = True
                cached_result["metadata"]["optimization"] = "cache_fast_path"
                return cached_result

            # Stage 2: Context enhancement (OPTIMIZATION: Only if needed)
            logger.info(f"[DEBUG RAG_ENGINE] Starting context enhancement, use_context={use_context}")
            timer.start_stage("context_enhancement")
            enhanced_query = question
            if use_context and self.conversation_memory:
                # OPTIMIZATION: Run in thread to avoid blocking
                logger.info(f"[DEBUG RAG_ENGINE] Calling conversation_memory.get_relevant_context_for_query...")
                enhanced_query, _ = await asyncio.to_thread(
                    self.conversation_memory.get_relevant_context_for_query,
                    question,
                    max_exchanges=3
                )
                logger.info(f"[DEBUG RAG_ENGINE] Context retrieved")
            timer.end_stage()
            logger.info(f"[DEBUG RAG_ENGINE] Context enhancement complete, query={'enhanced' if enhanced_query != question else 'unchanged'}")

            # Stage 3: Document retrieval (with sub-stage timing)
            logger.info(f"[DEBUG RAG_ENGINE] Starting document retrieval, mode={mode}")
            if mode == "simple":
                # BUGFIX: Pass both original question and enhanced query
                # - original question used for multi-query expansion decision
                # - enhanced query used for retrieval if multi-query not activated
                logger.info(f"[DEBUG RAG_ENGINE] Calling self._simple_retrieve()...")
                retrieval_result = await self._simple_retrieve(
                    enhanced_query,
                    timer,
                    original_query=question
                )
                logger.info(f"[DEBUG RAG_ENGINE] _simple_retrieve() returned, docs={len(retrieval_result.documents) if retrieval_result else 0}")
            else:
                timer.start_stage("retrieval")
                logger.info(f"[DEBUG RAG_ENGINE] Calling retrieval_engine.retrieve()...")
                retrieval_result = await self.retrieval_engine.retrieve(
                    query=enhanced_query,
                    llm_rerank_count=llm_rerank_count
                )
                logger.info(f"[DEBUG RAG_ENGINE] retrieval_engine.retrieve() returned")
                timer.end_stage()

            # Check if we have results
            if not retrieval_result.documents:
                timing_breakdown = timer.get_breakdown()
                return {
                    "answer": "I couldn't find any relevant documents to answer your question.",
                    "sources": [],
                    "metadata": {
                        "strategy_used": "simple_dense" if mode == "simple" else retrieval_result.strategy_used,
                        "query_type": "simple" if mode == "simple" else retrieval_result.metadata.get('query_type', 'simple'),
                        "mode": mode,
                        "processing_time_ms": timing_breakdown["total_ms"],
                        "timing_breakdown": timing_breakdown,
                        "cache_hit": False
                    },
                    "error": False
                }

            # QUICK WIN #6: Parallel answer generation with pre-answer confidence scoring (50% speedup)
            # OPTIMIZATION: Start confidence calculation on retrieval quality BEFORE answer generation
            # This runs in parallel with answer generation, saving 50% of confidence scoring time
            # Note: Full confidence (with answer quality) must wait for answer, but retrieval quality can start early

            # Stage 4: Answer generation (with parallel pre-confidence scoring)
            timer.start_stage("answer_generation")

            # Pre-calculate retrieval confidence (doesn't need answer)
            pre_confidence_task = None
            if self.confidence_scorer and retrieval_result.documents:
                async def _pre_calculate_confidence():
                    """Calculate retrieval-based confidence signals before answer generation"""
                    try:
                        # Start timing for this component
                        import time
                        t0 = time.perf_counter()

                        # This is a simplified confidence that only looks at retrieval quality
                        # Full confidence will be calculated after answer is ready
                        pre_conf = {
                            'retrieval_scores': retrieval_result.scores[:3],
                            'doc_count': len(retrieval_result.documents)
                        }

                        elapsed = (time.perf_counter() - t0) * 1000
                        logger.debug(f"[QUICK WIN #6] Pre-confidence calculated in {elapsed:.1f}ms (parallel with generation)")
                        return pre_conf
                    except Exception as e:
                        logger.warning(f"Pre-confidence calculation failed: {e}")
                        return None

                # Launch pre-confidence calculation in parallel
                pre_confidence_task = asyncio.create_task(_pre_calculate_confidence())

            # Generate answer (this will run in parallel with pre-confidence)
            answer = await self.answer_generator.generate(
                question,
                retrieval_result.documents
            )
            timer.end_stage()

            # Stage 4.5: Confidence scoring (finalize with answer)
            timer.start_stage("confidence_scoring")
            confidence_data = None
            if self.confidence_scorer and retrieval_result.documents:
                try:
                    # Wait for pre-confidence if it was running
                    if pre_confidence_task:
                        await pre_confidence_task  # Should complete instantly since generation took longer

                    # Now calculate full confidence including answer quality
                    confidence_data = self.confidence_scorer.calculate_confidence(
                        query=question,
                        answer=answer,
                        documents=retrieval_result.documents[:3],
                        retrieval_scores=retrieval_result.scores[:3]
                    )
                    logger.info(f"Confidence: {confidence_data['overall']:.2f} ({confidence_data['interpretation']})")
                except Exception as e:
                    logger.warning(f"Confidence scoring failed: {e}")
            timer.end_stage()

            # Stage 5: Post-processing (memory & cache) - OPTIMIZATION: Fire and forget
            timer.start_stage("post_processing")

            # Get final timing breakdown
            timing_breakdown = timer.get_breakdown()

            # OPTIMIZATION: Simplified result structure (remove optional explanation for speed)
            result = {
                "answer": answer,
                "sources": self._format_sources(retrieval_result),
                "metadata": {
                    "strategy_used": retrieval_result.metadata.get('strategy', 'simple_dense'),  # BUGFIX: Get from metadata
                    "query_type": "simple" if mode == "simple" else retrieval_result.metadata.get('query_type', 'simple'),
                    "mode": mode,
                    "processing_time_ms": timing_breakdown["total_ms"],
                    "timing_breakdown": timing_breakdown,
                    "cache_hit": False,
                    "optimization": "speed_optimized"
                },
                "error": False
            }

            # Add confidence data if available
            if confidence_data:
                # Normalize confidence to 0-1 range (cap at 1.0 or divide by 100 if > 1)
                raw_confidence = float(confidence_data["overall"])
                normalized_confidence = min(1.0, raw_confidence / 100.0 if raw_confidence > 1 else raw_confidence)
                result["metadata"]["confidence"] = normalized_confidence
                result["metadata"]["confidence_interpretation"] = confidence_data["interpretation"]
                result["metadata"]["confidence_signals"] = confidence_data["signals"]

            # OPTIMIZATION: Run memory & cache updates asynchronously (don't block response)
            # This shaves off 50-100ms from response time
            async def _background_updates():
                try:
                    # Store in conversation memory
                    if self.conversation_memory:
                        await asyncio.to_thread(
                            self.conversation_memory.add,
                            query=question,
                            response=answer,
                            retrieved_docs=retrieval_result.documents,
                            query_type="simple" if mode == "simple" else retrieval_result.query_type,
                            strategy_used=retrieval_result.strategy_used  # BUGFIX: Use actual strategy
                        )

                    # Cache result (sync operation, but fire and forget)
                    self.cache_manager.put_query_result(
                        question,
                        {"model": self.config.llm.model_name},
                        result
                    )

                    # L5: Trigger query prefetching (predict and prefetch next likely queries)
                    if self.query_prefetcher:
                        await self.query_prefetcher.on_query_received(
                            query=question,
                            trigger_prefetch=True
                        )
                except Exception as e:
                    logger.warning(f"Background update failed (non-critical): {e}")

            # Fire and forget background updates
            asyncio.create_task(_background_updates())

            timer.end_stage()  # End post-processing

            self.query_count += 1
            logger.info(f"[OPTIMIZED] Query processed in {timing_breakdown['total_ms']:.1f}ms")

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

    async def _simple_retrieve(
        self,
        query: str,
        timer: Optional[StageTimer] = None,
        original_query: str = None  # BUGFIX: Original user question for multi-query decision
    ) -> RetrievalResult:
        """
        TRULY SIMPLE retrieval - single dense vector search, NO query transformations, NO multi-query fusion

        PERFORMANCE: Optimized for speed with minimal overhead
        - Single embedding generation
        - Single vector search
        - Minimal reranking (top 3 only)
        - No query transformations (HyDE, multi-query, etc.)
        """

        # Start timing
        if timer:
            timer.start_stage("retrieval.simple")

        # CRITICAL FIX: Disable ALL advanced features for true simple mode
        # This prevents the 5 LLM calls we were seeing (18.5s query time)
        retrieval_result = await self.retrieval_engine.retrieve(
            query,
            _disable_multi_query=True,  # Disable multi-query fusion (prevents 4 extra LLM calls)
            _disable_query_transform=True,  # Disable HyDE and query transformations (prevents 1 LLM call)
            top_k=3  # Limit to top 3 results for speed
        )

        if timer:
            timer.end_stage()

        return retrieval_result

    def _format_sources(self, retrieval_result: RetrievalResult) -> List[Dict]:
        """
        Format source documents for API response.

        IMPORTANT: Must match Source schema in schemas.py:
        {
          file_name: str,
          file_type: str,
          relevance_score: float,
          excerpt: str,
          metadata: Dict[str, Any]
        }
        """
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

            # Extract file extension for file_type
            file_extension = os.path.splitext(file_name)[1]
            if file_extension:
                file_type = file_extension[1:]  # Remove leading dot (.pdf -> pdf)
            else:
                file_type = 'unknown'

            # Truncate excerpt to 500 characters
            excerpt = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content

            # QDRANT FIX: Normalize relevance scores to 0-1 range
            # Qdrant can return cosine similarity scores > 1.0 due to floating point precision
            # Clamp to 1.0 max to pass Pydantic validation (ge=0.0, le=1.0)
            normalized_score = min(float(score), 1.0)

            # Format to match Source schema
            source_dict = {
                "file_name": file_name,
                "file_type": file_type,
                "relevance_score": normalized_score,
                "excerpt": excerpt,
                "metadata": {}
            }

            # Add page number to metadata if available
            if 'page_number' in doc.metadata:
                source_dict["metadata"]["page_number"] = doc.metadata['page_number']

            # Add any other metadata fields
            for key, value in doc.metadata.items():
                if key not in ['file_name', 'page_number']:
                    source_dict["metadata"][key] = value

            sources.append(source_dict)

        return sources

    def clear_conversation(self) -> Tuple[bool, str]:
        """Clear conversation memory AND query cache"""
        try:
            cleared_items = []

            # Clear conversation memory
            if self.conversation_memory:
                self.conversation_memory.clear()
                logger.info("Conversation memory cleared")
                cleared_items.append("conversation memory")

            # CRITICAL FIX: Also clear the Redis query cache
            if self.cache_manager:
                self.cache_manager.clear_all()
                logger.info("Query cache cleared")
                cleared_items.append("query cache")

            if cleared_items:
                message = f"Successfully cleared: {', '.join(cleared_items)}"
                return True, message
            else:
                return False, "No components initialized to clear"

        except Exception as e:
            logger.error(f"Failed to clear conversation/cache: {e}")
            return False, f"Error clearing conversation/cache: {str(e)}"

    def update_settings(self, **kwargs) -> Tuple[bool, str, Dict]:
        """
        Update runtime settings including hot-swapping LLM model.

        Returns:
            Tuple of (success, message, current_settings)
        """
        try:
            updated = []

            # HOT-SWAP: Handle LLM model change
            if 'llm_model' in kwargs and kwargs['llm_model']:
                new_model = kwargs['llm_model']
                logger.info(f"HOT-SWAP: Switching LLM model from {self.config.llm.model_name} to {new_model}")

                # Update config
                old_model = self.config.llm.model_name
                self.config.llm.model_name = new_model

                # Recreate LLM with new model
                try:
                    self.llm = create_llm(self.config, test_connection=False)

                    # Update dependent components
                    if self.conversation_memory:
                        self.conversation_memory.llm = self.llm
                    if self.retrieval_engine:
                        self.retrieval_engine.llm = self.llm
                    if self.answer_generator:
                        self.answer_generator.llm = self.llm

                    # Clear cache (old model's answers not compatible)
                    if self.cache_manager:
                        self.cache_manager.clear_all()
                        logger.info("Cache cleared after model switch")

                    logger.info(f"✓ LLM hot-swapped successfully: {old_model} → {new_model}")
                    updated.append('llm_model')

                except Exception as e:
                    # Rollback on failure
                    logger.error(f"Hot-swap failed, rolling back: {e}")
                    self.config.llm.model_name = old_model
                    self.llm = create_llm(self.config, test_connection=False)
                    return False, f"Model hot-swap failed: {str(e)}", self.runtime_settings.copy()

            # HOT-SWAP: Handle temperature change
            if 'temperature' in kwargs and kwargs['temperature'] is not None:
                new_temp = max(0.0, min(2.0, float(kwargs['temperature'])))
                logger.info(f"HOT-SWAP: Updating temperature to {new_temp}")
                self.config.llm.temperature = new_temp
                # Recreate LLM with new temperature
                self.llm = create_llm(self.config, test_connection=False)
                updated.append('temperature')

            # Standard settings
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

            # Return current settings including model info
            current_settings = self.runtime_settings.copy()
            current_settings['llm_model'] = self.config.llm.model_name
            current_settings['temperature'] = self.config.llm.temperature

            return True, message, current_settings

        except Exception as e:
            logger.error(f"Failed to update settings: {e}", exc_info=True)
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

            # Add query variants for transparency (only when multi-query fusion is used)
            if retrieval_result.metadata.get("query_variants"):
                metadata["query_variants"] = retrieval_result.metadata.get("query_variants")

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
            # Build prompt using same logic as AdaptiveAnswerGenerator.generate()
            query_type = retrieval_result.query_type

            # Limit context chunks and truncate
            max_sources = 3 if query_type == "simple" else 5
            max_chunk_length = 300 if query_type == "simple" else 400

            context_parts = []
            for i, (doc, score) in enumerate(zip(
                retrieval_result.documents[:max_sources],
                retrieval_result.scores[:max_sources]
            ), 1):
                source = doc.metadata.get('file_name', 'Unknown').split('/')[-1]
                chunk = doc.page_content[:max_chunk_length]
                if len(doc.page_content) > max_chunk_length:
                    chunk += "..."
                context_parts.append(f"[{i}] {chunk}")

            context = "\n\n".join(context_parts)

            # Build prompt based on query type
            if query_type == "simple":
                prompt = f"""Answer from sources. Be brief.

{context}

Q: {question}
A:"""
            elif query_type == "moderate":
                prompt = f"""Answer from sources below. Cite [number].

{context}

Q: {question}
A:"""
            else:
                prompt = f"""Answer comprehensively from sources. Cite [number].

{context}

Q: {question}
A:"""

            # Stream from LLM (check if async streaming is available)
            if hasattr(self.llm, 'astream'):
                # Use async streaming for llama.cpp and other async-capable LLMs
                async for chunk in self.llm.astream(prompt):
                    yield chunk
            else:
                # Fallback to sync streaming for Ollama
                for chunk in self.llm.stream(prompt):
                    yield chunk

        except Exception as e:
            logger.error(f"Answer streaming error: {e}", exc_info=True)
            yield f"[Error: {str(e)}]"

    def sync_llm_from_model_manager(self):
        """
        Synchronize LLM from ModelManager after a model switch.

        This method is called by the model_control API after a successful
        model hotswap to update all RAG components with the new LLM instance.
        """
        if not self.model_manager:
            logger.warning("Cannot sync LLM: ModelManager not set")
            return False

        try:
            # Get fresh LLM instance from ModelManager
            new_llm = self.model_manager.get_llm()

            if not new_llm:
                logger.error("ModelManager returned None for LLM")
                return False

            # Update LLM reference
            self.llm = new_llm

            # Update all dependent components
            if self.conversation_memory:
                self.conversation_memory.llm = new_llm
                logger.info("  ✓ Updated conversation_memory LLM")

            if self.retrieval_engine:
                self.retrieval_engine.llm = new_llm
                logger.info("  ✓ Updated retrieval_engine LLM")

            if self.answer_generator:
                self.answer_generator.llm = new_llm
                logger.info("  ✓ Updated answer_generator LLM")

            # Clear cache (old model's answers not compatible with new model)
            if self.cache_manager:
                self.cache_manager.clear_all()
                logger.info("  ✓ Cache cleared after model switch")

            logger.info("✓ RAG Engine synchronized with new model")
            return True

        except Exception as e:
            logger.error(f"Failed to sync LLM from ModelManager: {e}", exc_info=True)
            return False

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

        # Get current model from ModelManager if available
        current_model = self.config.llm.model_name
        if self.model_manager:
            model_info = self.model_manager.get_current_model()
            if model_info:
                current_model = f"{model_info['name']} ({model_info['backend']})"

        return {
            "status": "operational",
            "message": "All systems operational",
            "components": components,
            "uptime_seconds": uptime.total_seconds(),
            "query_count": self.query_count,
            "current_mode": self.current_mode,
            "config": {
                "llm_model": current_model,
                "embedding_model": self.config.embedding.model_name,
                "ollama_host": self.config.ollama_host
            }
        }
