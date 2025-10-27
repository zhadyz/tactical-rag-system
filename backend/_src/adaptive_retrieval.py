"""
Adaptive Retrieval Layer - ATLAS Protocol Integration

Mission: Integrate L4 embedding cache into retrieval pipeline
Architecture: Wrap embedding operations with cache-first lookups
Performance Target: -98% embedding latency for cached queries

Integration Points:
- Query embedding generation (single queries)
- Document embedding generation (batch indexing)
- Multi-query expansion (4 variants cached separately)

Research Source: V3.5_AUGMENTATION_REPORT.md Section 4 & 6
Implementation Date: 2025-10-23
Lead: THE DIDACT (Research Specialist)
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np

from embedding_cache import EmbeddingCache
from query_transformations import QueryTransformationPipeline, QueryType
from advanced_reranking import LLMReranker, HybridReranker, HybridBGEReranker

# Try importing BGE Reranker (Quick Win #7)
try:
    from bge_reranker import BGERerankerV2M3, BGERerankerConfig, create_and_initialize_bge_reranker
    BGE_RERANKER_AVAILABLE = True
except ImportError:
    BGE_RERANKER_AVAILABLE = False
    logger.warning("[AdaptiveRetriever] BGE Reranker not available, will use LLM fallback")

logger = logging.getLogger(__name__)

# Lazy import for CrossEncoder to avoid startup overhead
_cross_encoder = None
def get_cross_encoder(model_name: str):
    """Lazy load cross-encoder model"""
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder
        import os

        # Force CPU for PyTorch models (RTX 5080 sm_120 incompatibility workaround)
        device = 'cpu' if os.getenv('FORCE_TORCH_CPU') == '1' else 'cuda'
        _cross_encoder = CrossEncoder(model_name, device=device)
        logger.info(f"CrossEncoder loaded: {model_name} (device={device})")
    return _cross_encoder


@dataclass
class RetrievalResult:
    """Result from adaptive retrieval operation"""
    documents: List[Any]
    scores: List[float]
    metadata: Dict[str, Any]
    cache_hit: bool = False


class AdaptiveRetriever:
    """
    Adaptive Retrieval Engine with L4 Embedding Cache

    Architecture:
    - Cache-first embedding lookups (99% of queries hit cache in production)
    - Automatic cache warming during indexing
    - Batch optimization for document embeddings
    - Statistics tracking for performance monitoring

    Performance Characteristics:
    - Cached query: <1ms embedding latency
    - Uncached query: 50-100ms embedding computation
    - Expected cache hit rate: 60-80% (production average)
    - Latency reduction: -98% for cached queries
    """

    def __init__(
        self,
        embedding_model: Any,  # HuggingFace or Ollama embeddings
        vector_store: Any,  # ChromaDB or Qdrant
        embedding_cache: Optional[EmbeddingCache] = None,
        use_cache: bool = True,
        config: Any = None,  # Optional config object with retrieval settings
        llm_service: Any = None  # LLM service for query transformations and LLM reranking
    ):
        """
        Initialize Adaptive Retriever

        Args:
            embedding_model: Embedding model instance (e.g., HuggingFaceEmbeddings)
            vector_store: Vector database instance (e.g., Chroma)
            embedding_cache: Optional EmbeddingCache instance
            use_cache: Enable/disable caching (default: True)
            config: Optional config object with RetrievalConfig
            llm_service: Optional LLM service for query transformations and reranking
        """
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.embedding_cache = embedding_cache
        self.use_cache = use_cache
        self.config = config
        self.llm_service = llm_service

        # Performance metrics
        self.total_queries = 0
        self.cache_hits = 0
        self.total_embedding_time_ms = 0.0

        # Cross-encoder reranking (lazy loaded)
        self.cross_encoder = None
        self.cross_encoder_model_name = None
        if config and hasattr(config, 'retrieval'):
            self.cross_encoder_model_name = config.retrieval.reranker_model

        # Advanced query transformations (HyDE, Multi-Query, Classification)
        self.query_transformer = None
        if llm_service and config and hasattr(config, 'query_transformation'):
            qt_config = config.query_transformation
            if qt_config.enable_hyde or qt_config.enable_multiquery_rewrite or qt_config.enable_classification:
                self.query_transformer = QueryTransformationPipeline(
                    llm_service=llm_service,
                    enable_hyde=qt_config.enable_hyde,
                    enable_multiquery=qt_config.enable_multiquery_rewrite,
                    enable_classification=qt_config.enable_classification
                )
                logger.info(
                    f"Query Transformations enabled: HyDE={qt_config.enable_hyde}, "
                    f"MultiQuery={qt_config.enable_multiquery_rewrite}, "
                    f"Classification={qt_config.enable_classification}"
                )

        # Advanced LLM-based reranking (on top of cross-encoder)
        self.llm_reranker = None
        self.hybrid_reranker = None
        self.bge_reranker = None  # QUICK WIN #7: BGE Reranker v2-m3 (lazy initialized)
        if llm_service and config and hasattr(config, 'advanced_reranking'):
            ar_config = config.advanced_reranking
            if ar_config.enable_llm_reranking:
                self.llm_reranker = LLMReranker(
                    llm_service=llm_service,
                    top_n=ar_config.llm_rerank_top_n,
                    use_async=False  # DEADLOCK FIX: Single-thread executor requires sequential calls
                )
                logger.info(
                    f"LLM Reranking enabled: top_n={ar_config.llm_rerank_top_n}, "
                    f"hybrid_alpha={ar_config.hybrid_rerank_alpha}"
                )

        logger.info(
            f"AdaptiveRetriever initialized: cache={'enabled' if use_cache else 'disabled'}, "
            f"cross_encoder={'configured' if self.cross_encoder_model_name else 'disabled'}, "
            f"query_transforms={'enabled' if self.query_transformer else 'disabled'}, "
            f"llm_reranking={'enabled' if self.llm_reranker else 'disabled'}"
        )

    async def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for query with cache-first lookup

        Args:
            query: Query text

        Returns:
            Embedding vector as numpy array
        """
        import time
        start_time = time.perf_counter()

        logger.info(f"[DEBUG EMBED] embed_query() called with query: '{query[:50]}...'")

        # Try cache first if enabled
        if self.use_cache and self.embedding_cache:
            logger.info(f"[DEBUG EMBED] Checking embedding cache...")
            cached = await self.embedding_cache.get(query)
            logger.info(f"[DEBUG EMBED] Cache check complete, result={'HIT' if cached is not None else 'MISS'}")
            if cached is not None:
                self.cache_hits += 1
                self.total_queries += 1
                latency_ms = (time.perf_counter() - start_time) * 1000
                self.total_embedding_time_ms += latency_ms

                logger.debug(f"Query embedding from cache ({latency_ms:.2f}ms)")
                return cached

        # Cache miss - compute embedding
        self.total_queries += 1

        logger.info(f"[DEBUG EMBED] Cache miss, computing embedding...")
        logger.info(f"[DEBUG EMBED] Checking if embedding_model.embed_query is async: {asyncio.iscoroutinefunction(self.embedding_model.embed_query)}")

        if asyncio.iscoroutinefunction(self.embedding_model.embed_query):
            logger.info(f"[DEBUG EMBED] Calling async embedding_model.embed_query()...")
            embedding = await self.embedding_model.embed_query(query)
            logger.info(f"[DEBUG EMBED] Async embedding generation complete")
        else:
            # Run sync function in executor to avoid blocking
            logger.info(f"[DEBUG EMBED] Calling sync embedding_model.embed_query() in executor...")
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.embedding_model.embed_query,
                query
            )
            logger.info(f"[DEBUG EMBED] Sync embedding generation complete")

        logger.info(f"[DEBUG EMBED] Converting embedding to numpy array...")
        # Convert to numpy array
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding, dtype=np.float32)
        logger.info(f"[DEBUG EMBED] Conversion complete")

        latency_ms = (time.perf_counter() - start_time) * 1000
        self.total_embedding_time_ms += latency_ms

        logger.debug(f"Query embedding computed ({latency_ms:.2f}ms)")

        # Store in cache for future use
        if self.use_cache and self.embedding_cache:
            logger.info(f"[DEBUG EMBED] Storing embedding in cache...")
            await self.embedding_cache.set(query, embedding)
            logger.info(f"[DEBUG EMBED] Embedding stored in cache")

        logger.info(f"[DEBUG EMBED] embed_query() returning successfully")
        return embedding

    async def embed_documents(
        self,
        documents: List[str],
        batch_size: int = 64
    ) -> List[np.ndarray]:
        """
        Generate embeddings for documents with batch cache optimization

        Args:
            documents: List of document texts
            batch_size: Batch size for uncached embeddings (default: 64)

        Returns:
            List of embedding vectors
        """
        import time
        start_time = time.perf_counter()

        # Try batch cache retrieval if enabled
        embeddings = []
        uncached_indices = []
        uncached_texts = []

        if self.use_cache and self.embedding_cache:
            cached_embeddings = await self.embedding_cache.batch_get(documents)

            for i, cached in enumerate(cached_embeddings):
                if cached is not None:
                    embeddings.append(cached)
                    self.cache_hits += 1
                else:
                    embeddings.append(None)  # Placeholder
                    uncached_indices.append(i)
                    uncached_texts.append(documents[i])

            self.total_queries += len(documents)

            logger.info(
                f"Document embeddings: {len(documents) - len(uncached_texts)}/{len(documents)} "
                f"from cache ({(1 - len(uncached_texts)/len(documents))*100:.1f}% hit rate)"
            )
        else:
            # Cache disabled - all documents need computation
            uncached_indices = list(range(len(documents)))
            uncached_texts = documents
            embeddings = [None] * len(documents)
            self.total_queries += len(documents)

        # Compute embeddings for uncached documents
        if uncached_texts:
            if asyncio.iscoroutinefunction(self.embedding_model.embed_documents):
                computed = await self.embedding_model.embed_documents(uncached_texts)
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                computed = await loop.run_in_executor(
                    None,
                    self.embedding_model.embed_documents,
                    uncached_texts
                )

            # Convert to numpy arrays
            computed = [
                np.array(emb, dtype=np.float32) if not isinstance(emb, np.ndarray) else emb
                for emb in computed
            ]

            # Fill in computed embeddings
            for idx, embedding in zip(uncached_indices, computed):
                embeddings[idx] = embedding

            # Store newly computed embeddings in cache
            if self.use_cache and self.embedding_cache:
                await self.embedding_cache.batch_set(uncached_texts, computed)

        latency_ms = (time.perf_counter() - start_time) * 1000
        self.total_embedding_time_ms += latency_ms

        logger.info(
            f"Document embedding complete: {len(documents)} docs in {latency_ms:.2f}ms "
            f"({latency_ms/len(documents):.2f}ms per doc)"
        )

        return embeddings

    async def _expand_query(self, query: str, num_variants: int = 4) -> Tuple[List[str], Optional[QueryType]]:
        """
        Generate query variants using advanced query transformations

        Uses QueryTransformationPipeline (HyDE + Multi-Query) if available,
        otherwise falls back to simple rule-based expansion.

        Args:
            query: Original query text
            num_variants: Number of variants to generate

        Returns:
            Tuple of (query_variants, query_type)
        """
        # Use advanced query transformations if available
        if self.query_transformer is not None:
            try:
                transformed_queries, query_type = await self.query_transformer.transform(query)
                logger.info(
                    f"Query transformations applied: {len(transformed_queries)} variants, "
                    f"type={query_type.value if query_type else 'unknown'}"
                )
                # Limit to num_variants if needed
                return transformed_queries[:num_variants], query_type
            except Exception as e:
                logger.error(f"Query transformation failed: {e}, falling back to simple expansion")
                # Fall through to simple expansion

        # Fallback: Simple rule-based expansion
        variants = [query]  # Always include original

        # Variant 1: Add "policy" or "regulation" context
        if "policy" not in query.lower() and "regulation" not in query.lower():
            variants.append(f"{query} policy")

        # Variant 2: Rephrase question words
        rephrased = query
        for old, new in [("how often", "what frequency"), ("when", "what time"),
                          ("how many", "what number"), ("what are", "list the")]:
            if old in query.lower():
                rephrased = query.lower().replace(old, new)
                variants.append(rephrased)
                break

        # Variant 3: Add "requirements" context for procedural questions
        if any(word in query.lower() for word in ["how", "what", "requirements", "must"]):
            variants.append(f"{query} requirements")

        # Return up to num_variants (deduplicated)
        unique_variants = list(dict.fromkeys(variants))  # Preserves order
        return unique_variants[:num_variants], None

    async def _rerank_documents(
        self,
        query: str,
        documents: List[Any],
        top_k: int = 30,
        query_type: Optional[QueryType] = None,
        llm_rerank_count: Optional[int] = None
    ) -> List[Tuple[Any, float]]:
        """
        Rerank documents using cross-encoder or hybrid cross-encoder + LLM

        Args:
            query: Query text
            documents: List of LangChain Document objects
            top_k: Number of top documents to return
            query_type: Optional query type for adaptive LLM reranking
            llm_rerank_count: Number of docs to rerank with LLM (overrides config for presets)

        Returns:
            List of (document, score) tuples, sorted by relevance
        """
        if not documents:
            return []

        # If no reranking configured, return documents as-is
        if not self.cross_encoder_model_name and not self.llm_reranker:
            return [(doc, 1.0) for doc in documents[:top_k]]

        # QUICK WIN: Determine how many docs to rerank with LLM (for performance tuning)
        effective_rerank_count = llm_rerank_count
        if effective_rerank_count is None and self.llm_reranker:
            effective_rerank_count = self.llm_reranker.top_n

        # Convert documents to format expected by rerankers
        # QUICK WIN OPTIMIZATION: Only pass the required number for LLM reranking to save time
        max_docs_for_llm = effective_rerank_count if effective_rerank_count else len(documents)
        docs_for_reranking = []
        for doc in documents[:max_docs_for_llm]:
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            docs_for_reranking.append({
                'content': content,
                'metadata': metadata,
                'original_doc': doc
            })

        # Check if hybrid reranking is available
        use_hybrid = (self.llm_reranker is not None and
                     self.cross_encoder_model_name is not None)

        if use_hybrid:
            # Hybrid reranking: Cross-encoder + LLM
            logger.debug(f"Using hybrid reranking for {len(documents)} documents")

            # Initialize hybrid reranker on first use
            if self.hybrid_reranker is None:
                # Lazy load cross-encoder
                if self.cross_encoder is None:
                    self.cross_encoder = get_cross_encoder(self.cross_encoder_model_name)

                # Create a simple cross-encoder reranker wrapper
                class CrossEncoderWrapper:
                    def __init__(self, cross_encoder, model_name):
                        self.cross_encoder = cross_encoder
                        self.model_name = model_name

                    def rerank(self, query, documents):
                        # Prepare pairs
                        pairs = [[query, doc['content']] for doc in documents]
                        # Score
                        scores = self.cross_encoder.predict(pairs)
                        # Add scores to documents
                        for doc, score in zip(documents, scores):
                            doc['cross_encoder_score'] = float(score)
                        # Sort by score
                        documents.sort(key=lambda x: x['cross_encoder_score'], reverse=True)
                        return documents

                ce_wrapper = CrossEncoderWrapper(self.cross_encoder, self.cross_encoder_model_name)

                # Get hybrid alpha from config
                hybrid_alpha = 0.6  # Default
                use_bge = False  # Default
                bge_device = "cuda"  # Default
                bge_batch_size = 32  # Default

                if self.config and hasattr(self.config, 'advanced_reranking'):
                    ar_config = self.config.advanced_reranking
                    hybrid_alpha = ar_config.hybrid_rerank_alpha
                    use_bge = ar_config.enable_bge_reranker if hasattr(ar_config, 'enable_bge_reranker') else False
                    bge_device = ar_config.bge_reranker_device if hasattr(ar_config, 'bge_reranker_device') else "cuda"
                    bge_batch_size = ar_config.bge_reranker_batch_size if hasattr(ar_config, 'bge_reranker_batch_size') else 32

                # QUICK WIN #7: Initialize BGE Reranker v2-m3 (400ms → 60ms, 85% faster)
                if use_bge and BGE_RERANKER_AVAILABLE and self.bge_reranker is None:
                    try:
                        logger.info("[AdaptiveRetriever] Initializing BGE Reranker v2-m3...")
                        self.bge_reranker = await create_and_initialize_bge_reranker(
                            device=bge_device,
                            batch_size=bge_batch_size,
                            normalize_scores=True
                        )
                        logger.info("[AdaptiveRetriever] ✓ BGE Reranker v2-m3 initialized successfully")
                    except Exception as e:
                        logger.error(f"[AdaptiveRetriever] Failed to initialize BGE Reranker: {e}")
                        logger.warning("[AdaptiveRetriever] Falling back to LLM reranking")
                        use_bge = False

                # Create HybridBGEReranker (with BGE primary, LLM fallback)
                self.hybrid_reranker = HybridBGEReranker(
                    cross_encoder_reranker=ce_wrapper,
                    bge_reranker=self.bge_reranker,
                    llm_reranker=self.llm_reranker,
                    use_bge=use_bge,
                    alpha=hybrid_alpha
                )

                logger.info(
                    f"[AdaptiveRetriever] HybridBGEReranker initialized: "
                    f"BGE={'enabled' if use_bge else 'disabled'}, "
                    f"alpha={hybrid_alpha}"
                )

            # Apply hybrid reranking
            query_type_str = query_type.value if query_type else "general"

            # Direct async call (reranker is now async)
            reranked_docs = await self.hybrid_reranker.rerank(
                query,
                docs_for_reranking,
                query_type_str
            )

            # Extract top_k results
            results = []
            for doc_dict in reranked_docs[:top_k]:
                original_doc = doc_dict['original_doc']
                final_score = doc_dict.get('final_score', 0.0)
                results.append((original_doc, final_score))

            if results:
                logger.debug(
                    f"Hybrid reranking complete: {len(results)} docs, "
                    f"top score: {results[0][1]:.4f}, bottom score: {results[-1][1]:.4f}"
                )

            return results

        elif self.cross_encoder_model_name:
            # Cross-encoder only reranking
            logger.debug(f"Using cross-encoder reranking for {len(documents)} documents")

            # Lazy load cross-encoder
            if self.cross_encoder is None:
                self.cross_encoder = get_cross_encoder(self.cross_encoder_model_name)

            # Prepare pairs for reranking
            pairs = [[query, doc['content']] for doc in docs_for_reranking]

            # Score with cross-encoder (synchronous, run in thread)
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,
                self.cross_encoder.predict,
                pairs
            )

            # Sort by scores (descending)
            ranked = sorted(
                zip([d['original_doc'] for d in docs_for_reranking], scores),
                key=lambda x: x[1],
                reverse=True
            )

            logger.debug(
                f"Cross-encoder reranking complete: top score: {ranked[0][1]:.3f}, "
                f"bottom score: {ranked[-1][1]:.3f}"
            )

            return ranked[:top_k]

        else:
            # LLM-only reranking (fallback, less common)
            logger.debug(f"Using LLM-only reranking for {len(documents)} documents")

            query_type_str = query_type.value if query_type else "general"

            loop = asyncio.get_event_loop()
            reranked_docs = await loop.run_in_executor(
                None,
                self.llm_reranker.rerank,
                query,
                docs_for_reranking,
                query_type_str
            )

            results = []
            for doc_dict in reranked_docs[:top_k]:
                original_doc = doc_dict['original_doc']
                llm_score = doc_dict.get('llm_score', 0.0)
                results.append((original_doc, llm_score / 10.0))  # Normalize to 0-1

            return results

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        _disable_multi_query: bool = False,
        _disable_query_transform: bool = False,
        llm_rerank_count: Optional[int] = None
    ) -> RetrievalResult:
        """
        Enhanced retrieval with automatic multi-query fusion and reranking

        Pipeline:
        1. Detect if query benefits from multi-query expansion
        2. If yes: use multi_query_retrieve() with RRF fusion
        3. If no: single-query retrieval with optional reranking

        Args:
            query: Query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            RetrievalResult with documents, scores, and cache metrics
        """
        # Check if multi-query fusion is enabled and beneficial
        use_multi_query = False
        if not _disable_multi_query and self.config and hasattr(self.config, 'retrieval'):
            retrieval_config = self.config.retrieval

            # Auto-detect vague queries that benefit from multi-query expansion
            vague_indicators = ["how", "what", "when", "requirements", "policy",
                                "rules", "must", "should", "frequency", "often"]
            is_vague = any(indicator in query.lower() for indicator in vague_indicators)

            use_multi_query = retrieval_config.use_multi_query and is_vague

        # Apply query transformations first (HyDE + classification)
        # CRITICAL FIX: Skip transformations when explicitly disabled OR called from multi_query_retrieve()
        # since the query variants are already transformed
        logger.info(f"[DEBUG RETRIEVE] Starting retrieve() for query: '{query[:50]}...'")
        query_variants = None
        query_type = None
        if self.query_transformer is not None and not _disable_multi_query and not _disable_query_transform:
            try:
                logger.info(f"[DEBUG RETRIEVE] Calling query_transformer.transform()...")
                transformed, query_type = await self.query_transformer.transform(query)
                logger.info(f"[DEBUG RETRIEVE] Query transformation complete, variants={len(transformed) if transformed else 0}")
                # For single-query mode, we'll use the first transformation (HyDE)
                # For multi-query mode, we'll use all variants
                query_variants = transformed
            except Exception as e:
                logger.error(f"Query transformation failed: {e}")
        else:
            logger.info(f"[DEBUG RETRIEVE] Skipping query transformation (transformer={self.query_transformer is not None}, disable_multi={_disable_multi_query}, disable_transform={_disable_query_transform})")

        # Route to multi-query or single-query retrieval
        if use_multi_query:
            logger.info(f"Using multi-query fusion for: {query[:60]}...")

            # Use transformed query variants if available, otherwise fallback
            if query_variants is None:
                num_variants = self.config.retrieval.multi_query_variants
                query_variants, query_type = await self._expand_query(query, num_variants=num_variants)

            # Use multi-query retrieval with RRF fusion
            result = await self.multi_query_retrieve(
                query_variants=query_variants,
                top_k=top_k,
                fusion_method="rrf"
            )

            result.metadata["multi_query"] = True
            result.metadata["num_variants"] = len(query_variants)
            result.metadata["query_type"] = query_type.value if query_type else None
            return result

        else:
            # Standard single-query retrieval with optional reranking
            logger.debug(f"Using single-query retrieval for: {query[:60]}...")

            # Determine K values for reranking pipeline
            initial_k = top_k
            rerank_k = top_k
            final_k = top_k

            use_reranking = False
            if self.config and hasattr(self.config, 'retrieval'):
                retrieval_config = self.config.retrieval
                if retrieval_config.use_reranking:
                    use_reranking = True
                    initial_k = retrieval_config.initial_k  # Retrieve 100 candidates
                    rerank_k = retrieval_config.rerank_k    # Rerank to top 30
                    final_k = retrieval_config.final_k      # Return top 8

            # Step 1: Initial retrieval (large K if reranking)
            # Use HyDE-transformed query if available
            logger.info(f"[DEBUG RETRIEVE] Starting embedding generation...")
            embedding_query = query_variants[0] if query_variants else query
            logger.info(f"[DEBUG RETRIEVE] Calling self.embed_query()...")
            query_embedding = await self.embed_query(embedding_query)
            logger.info(f"[DEBUG RETRIEVE] embed_query() returned, embedding shape={query_embedding.shape}")

            # HYBRID SEARCH ACTIVATION: Use hybrid_search() instead of dense-only similarity_search_by_vector()
            # This enables BM25 sparse vectors + dense vectors with RRF fusion (+5-7% accuracy)

            # DEBUG: Log vector_store details to diagnose hybrid search activation
            logger.info(f"[HYBRID DEBUG] vector_store type: {type(self.vector_store)}")
            logger.info(f"[HYBRID DEBUG] vector_store class: {self.vector_store.__class__.__name__}")
            logger.info(f"[HYBRID DEBUG] hasattr(vector_store, 'hybrid_search'): {hasattr(self.vector_store, 'hybrid_search')}")
            logger.info(f"[HYBRID DEBUG] Available methods: {[m for m in dir(self.vector_store) if not m.startswith('_')]}")

            # Track which retrieval strategy was used for metadata reporting
            retrieval_strategy = "dense"  # Default fallback

            if hasattr(self.vector_store, 'hybrid_search'):
                # Qdrant hybrid search with BM25 + dense vector fusion
                retrieval_strategy = "hybrid"
                logger.info(f"[HYBRID ACTIVATED] Using hybrid search (dense + BM25 sparse) for query: {query[:60]}...")

                if asyncio.iscoroutinefunction(self.vector_store.hybrid_search):
                    logger.info(f"[DEBUG RETRIEVE] Calling async vector_store.hybrid_search()...")
                    search_results = await self.vector_store.hybrid_search(
                        dense_vector=query_embedding.tolist(),
                        query_text=query,  # Original query text for BM25 tokenization
                        top_k=initial_k,
                        query_filter=filter_metadata
                    )
                    logger.info(f"[DEBUG RETRIEVE] Async hybrid_search() returned {len(search_results)} results")
                else:
                    logger.info(f"[DEBUG RETRIEVE] Calling sync vector_store.hybrid_search() in executor...")
                    loop = asyncio.get_event_loop()
                    search_results = await loop.run_in_executor(
                        None,
                        self.vector_store.hybrid_search,
                        query_embedding.tolist(),
                        query,
                        initial_k,
                        filter_metadata
                    )
                    logger.info(f"[DEBUG RETRIEVE] Sync hybrid_search() returned {len(search_results)} results")

                # Convert QdrantSearchResult objects to LangChain Document format
                from langchain.schema import Document
                initial_results = []
                for result in search_results:
                    doc = Document(
                        page_content=result.payload.get('text', ''),
                        metadata={k: v for k, v in result.payload.items() if k != 'text'}
                    )
                    initial_results.append(doc)

                logger.debug(f"Hybrid search returned {len(initial_results)} results")

            elif asyncio.iscoroutinefunction(self.vector_store.similarity_search_by_vector):
                # Fallback to dense-only search (ChromaDB or Qdrant with sparse disabled)
                retrieval_strategy = "dense"
                logger.warning(f"[HYBRID FALLBACK] Using dense-only async search for query: {query[:60]}...")
                initial_results = await self.vector_store.similarity_search_by_vector(
                    query_embedding.tolist(),
                    k=initial_k,
                    filter=filter_metadata
                )
            else:
                retrieval_strategy = "dense"
                logger.warning(f"[HYBRID FALLBACK] Using dense-only sync search for query: {query[:60]}...")
                loop = asyncio.get_event_loop()
                initial_results = await loop.run_in_executor(
                    None,
                    self.vector_store.similarity_search_by_vector,
                    query_embedding.tolist(),
                    initial_k,
                    filter_metadata
                )

            # Step 2: Reranking (if enabled)
            if use_reranking and len(initial_results) > 0:
                logger.debug(f"Reranking {len(initial_results)} documents...")
                reranked = await self._rerank_documents(query, initial_results, top_k=rerank_k, query_type=query_type, llm_rerank_count=llm_rerank_count)
                final_results = [doc for doc, score in reranked[:final_k]]
                final_scores = [score for doc, score in reranked[:final_k]]
            else:
                final_results = initial_results[:final_k]
                final_scores = [0.0] * len(final_results)

            # Check cache hit
            cache_hit = bool(
                self.use_cache and
                self.embedding_cache and
                await self.embedding_cache.get(query) is not None
            )

            return RetrievalResult(
                documents=final_results,
                scores=final_scores,
                metadata={
                    "top_k": final_k,
                    "initial_k": initial_k,
                    "reranking_used": use_reranking,
                    "multi_query": False,
                    "filter": filter_metadata,
                    "cache_enabled": self.use_cache,
                    "query_type": query_type.value if query_type else None,
                    "hyde_used": query_variants is not None,
                    "strategy": retrieval_strategy  # BUGFIX: Report hybrid vs dense search
                },
                cache_hit=cache_hit
            )

    async def multi_query_retrieve(
        self,
        query_variants: List[str],
        top_k: int = 10,
        fusion_method: str = "rrf"
    ) -> RetrievalResult:
        """
        Multi-query retrieval with RRF fusion (cache-optimized)

        Each query variant is cached separately for maximum reuse.

        Args:
            query_variants: List of query variants (e.g., from query expansion)
            top_k: Number of results per query
            fusion_method: Fusion method ("rrf" or "simple")

        Returns:
            Fused retrieval results
        """
        # Retrieve results for each query variant in parallel
        # IMPORTANT: _disable_multi_query=True prevents infinite recursion
        retrieval_tasks = [
            self.retrieve(variant, top_k=top_k, _disable_multi_query=True)
            for variant in query_variants
        ]

        results = await asyncio.gather(*retrieval_tasks)

        # Reciprocal Rank Fusion (RRF)
        if fusion_method == "rrf":
            fused_scores = {}
            k = 60  # RRF constant (tunable)

            for result in results:
                for rank, doc in enumerate(result.documents):
                    doc_id = id(doc)  # Use object id as key
                    score = 1.0 / (k + rank + 1)
                    fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + score

            # Sort by fused score
            sorted_items = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

            # Reconstruct document list
            doc_map = {id(doc): doc for result in results for doc in result.documents}
            fused_docs = [doc_map[doc_id] for doc_id, _ in sorted_items[:top_k]]
            fused_scores_list = [score for _, score in sorted_items[:top_k]]

        else:
            # Simple fusion - concatenate and deduplicate
            seen = set()
            fused_docs = []
            fused_scores_list = []

            for result in results:
                for doc, score in zip(result.documents, result.scores):
                    doc_id = id(doc)
                    if doc_id not in seen:
                        seen.add(doc_id)
                        fused_docs.append(doc)
                        fused_scores_list.append(score)

                    if len(fused_docs) >= top_k:
                        break

        # Check if any query was cache hit
        any_cache_hit = any(result.cache_hit for result in results)

        return RetrievalResult(
            documents=fused_docs,
            scores=fused_scores_list,
            metadata={
                "num_variants": len(query_variants),
                "fusion_method": fusion_method,
                "top_k": top_k
            },
            cache_hit=any_cache_hit
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get retriever performance statistics

        Returns:
            Dictionary with performance metrics
        """
        cache_hit_rate = (
            (self.cache_hits / self.total_queries * 100.0)
            if self.total_queries > 0 else 0.0
        )

        avg_embedding_time = (
            (self.total_embedding_time_ms / self.total_queries)
            if self.total_queries > 0 else 0.0
        )

        return {
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "avg_embedding_time_ms": round(avg_embedding_time, 3),
            "cache_enabled": self.use_cache
        }


class AdaptiveAnswerGenerator:
    """
    Placeholder for answer generation (LLM integration)

    This would integrate with llama.cpp or Ollama for response generation.
    Implementation deferred to ATLAS Phase 4.
    """

    def __init__(self, llm_model: Any):
        self.llm_model = llm_model
        # Initialize answer validator for quality improvements
        from answer_validator import AnswerValidator
        self.validator = AnswerValidator()
        logger.info("AdaptiveAnswerGenerator initialized with answer validation")

    async def generate(
        self,
        query: str,
        context_documents: List[Any],
        max_tokens: int = 2048
    ) -> str:
        """
        Generate answer from query and retrieved context

        Args:
            query: User query
            context_documents: Retrieved documents
            max_tokens: Maximum response tokens

        Returns:
            Generated answer
        """
        if not context_documents:
            return "I couldn't find any relevant documents to answer your question."

        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(context_documents[:5], 1):
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            source = doc.metadata.get('file_name', 'Unknown') if hasattr(doc, 'metadata') else 'Unknown'

            # NOTE: Quick Win #5 (context truncation) was REMOVED to preserve quality
            # Truncation saves 200-300ms but degrades answer completeness

            context_parts.append(f"[Document {i} - {source}]\n{content}\n")

        context_str = "\n".join(context_parts)

        # Create RAG prompt
        prompt = f"""You are an AI assistant answering questions about Air Force policy documents (DAFIs).

Based ONLY on the following context documents, provide a clear, accurate, and concise answer to the user's question. If the context doesn't contain enough information to answer the question, say so.

CONTEXT:
{context_str}

QUESTION: {query}

ANSWER:"""

        try:
            # CRITICAL FIX: Use async generate() method if available (LlamaCppLangChainAdapter)
            # Root cause: asyncio.to_thread(invoke) where invoke() uses asyncio.run() creates nested event loops
            # Solution: Call async generate() directly instead of wrapping sync invoke()
            import inspect
            if hasattr(self.llm_model, 'generate') and inspect.iscoroutinefunction(self.llm_model.generate):
                response = await self.llm_model.generate(prompt)
            elif hasattr(self.llm_model, 'invoke'):
                response = await asyncio.to_thread(self.llm_model.invoke, prompt)
            elif hasattr(self.llm_model, '__call__'):
                response = await asyncio.to_thread(self.llm_model, prompt)
            else:
                logger.error(f"LLM model type not supported: {type(self.llm_model)}")
                return "Error: LLM model not configured properly"

            # Extract text from response
            if hasattr(response, 'content'):
                answer = response.content
            elif isinstance(response, str):
                answer = response
            else:
                answer = str(response)

            # Validate and fix common answer formatting issues
            answer = self.validator.validate(query, answer.strip())

            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {e}", exc_info=True)
            return f"Error generating answer: {str(e)}"
