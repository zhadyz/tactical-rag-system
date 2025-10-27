"""
Qdrant Vector Store Wrapper with Hybrid Search Support

This module provides a production-ready wrapper for Qdrant vector database with:
- Dense vector search (semantic)
- Sparse vector search (keyword-based, BM25-style)
- Hybrid search with Reciprocal Rank Fusion (RRF)
- Named vector support for multi-representation
- HNSW configuration for optimal performance
- Embedded mode support (no server needed)

Performance targets (per ATLAS specs):
- Search latency: 3-5ms @ 1M documents
- RPS: 1200+ queries/sec
- Scalability: 100M+ documents

Author: HOLLOWED_EYES (Mendicant Bias Elite Development Intelligence)
Date: 2025-10-23
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import asyncio
import pickle

import numpy as np
from langchain_core.documents import Document
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    HnswConfigDiff,
    OptimizersConfigDiff,
    Prefetch,
    Query,
    SearchParams,
    FusionQuery,
    Fusion,
    Filter,
    FieldCondition,
    MatchValue,
)
from qdrant_client.http.models import CollectionInfo, UpdateResult

# For BM25 sparse vector generation
from rank_bm25 import BM25Okapi


logger = logging.getLogger(__name__)


@dataclass
class QdrantSearchResult:
    """Result from Qdrant hybrid search"""
    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None


class QdrantVectorStore:
    """
    Production-ready Qdrant vector store with hybrid search.

    Features:
    - Dense vectors (BGE-large-en-v1.5, 1024-dim)
    - Sparse vectors (BM25-style keyword matching)
    - Hybrid search with RRF fusion
    - Embedded mode (file-based, no server)
    - HNSW optimization for 3-5ms latency

    Usage:
        store = QdrantVectorStore(
            collection_name="documents",
            vector_size=1024,
            path="./qdrant_storage"  # Embedded mode
        )
        await store.initialize()

        # Hybrid search
        results = await store.hybrid_search(
            dense_vector=[0.1, 0.2, ...],
            query_text="search query",
            top_k=10
        )
    """

    def __init__(
        self,
        collection_name: str = "documents",
        vector_size: int = 1024,
        path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        use_async: bool = True,
        enable_sparse: bool = True,  # ENABLED for hybrid search (BM25 + dense vectors)
    ):
        """
        Initialize Qdrant vector store.

        Args:
            collection_name: Name of Qdrant collection
            vector_size: Dimension of dense vectors (default: 1024 for BGE-large)
            path: Path for embedded mode (file-based storage)
            host: Qdrant server host (for server mode)
            port: Qdrant server port (for server mode)
            use_async: Use async client (recommended)
            enable_sparse: Enable sparse vectors for hybrid search
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.enable_sparse = enable_sparse
        self.use_async = use_async

        # Initialize client (embedded or server mode)
        if path:
            # Embedded mode - no server needed
            logger.info(f"Initializing Qdrant in embedded mode: {path}")
            if use_async:
                self.client = AsyncQdrantClient(path=path)
            else:
                self.client = QdrantClient(path=path)
        elif host and port:
            # Server mode
            logger.info(f"Connecting to Qdrant server: {host}:{port}")
            if use_async:
                # CRITICAL FIX: Disable compatibility check for Qdrant client 1.15.1 vs server 1.7.4
                # The /collections/{name}/exists endpoint doesn't exist in 1.7.4, causing 404 errors
                self.client = AsyncQdrantClient(host=host, port=port, check_compatibility=False)
            else:
                self.client = QdrantClient(host=host, port=port, check_compatibility=False)
        else:
            # Default: in-memory mode (testing only)
            logger.warning("Using in-memory mode - data will not persist!")
            if use_async:
                self.client = AsyncQdrantClient(":memory:")
            else:
                self.client = QdrantClient(":memory:")

        # BM25 tokenizer for sparse vectors
        self.bm25: Optional[BM25Okapi] = None
        self.tokenized_corpus: List[List[str]] = []

        # BM25 persistence path (use writable cache directory)
        if path:
            self.bm25_path = Path(path) / f"{collection_name}_bm25.pkl"
        else:
            # Default to /app/.cache for writable storage (not read-only /app/documents)
            cache_dir = Path("/app/.cache")
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.bm25_path = cache_dir / f"{collection_name}_bm25.pkl"

        self.initialized = False

    async def initialize(self, recreate: bool = False) -> bool:
        """
        Initialize Qdrant collection with optimized configuration.

        Args:
            recreate: If True, delete existing collection and recreate

        Returns:
            True if successful
        """
        try:
            # Check if collection exists
            logger.info(f"[DEBUG] Checking if collection exists: {self.collection_name}, use_async={self.use_async}")

            # CRITICAL FIX: collection_exists() throws 404 on Qdrant 1.7.4 server
            # Fallback to listing collections and checking if name exists
            try:
                if self.use_async:
                    exists = await self.client.collection_exists(self.collection_name)
                else:
                    exists = await asyncio.to_thread(
                        self.client.collection_exists,
                        self.collection_name
                    )
            except Exception as check_err:
                logger.warning(f"[DEBUG] collection_exists() failed with: {type(check_err).__name__}: {check_err}")
                logger.info(f"[DEBUG] Falling back to list collections method")
                # Fallback: Get all collections and check if ours exists
                if self.use_async:
                    collections_response = await self.client.get_collections()
                else:
                    collections_response = await asyncio.to_thread(self.client.get_collections)

                collection_names = [c.name for c in collections_response.collections]
                exists = self.collection_name in collection_names
                logger.info(f"[DEBUG] Fallback method found {len(collection_names)} collections, exists={exists}")

            logger.info(f"[DEBUG] collection_exists() returned: {exists} (type: {type(exists)}, recreate={recreate})")

            if exists and recreate:
                logger.warning(f"[DEBUG] Deleting collection because exists={exists} and recreate={recreate}")
                logger.warning(f"Deleting existing collection: {self.collection_name}")
                if self.use_async:
                    await self.client.delete_collection(self.collection_name)
                else:
                    await asyncio.to_thread(
                        self.client.delete_collection,
                        self.collection_name
                    )
                exists = False
                logger.info(f"[DEBUG] After deletion, exists set to: {exists}")

            logger.info(f"[DEBUG] Before creation check: exists={exists}, not exists={not exists}, will create={not exists}")

            if not exists:
                logger.info(f"Creating collection: {self.collection_name}")
                try:
                    await self._create_collection()
                    logger.info(f"[DEBUG] Collection created successfully")
                except Exception as create_err:
                    # RACE CONDITION FIX: If we get 409 Conflict, another instance created it first
                    # This is fine - we can proceed as if we created it
                    logger.error(f"[DEBUG] Caught creation error - Type: {type(create_err).__name__}, String: '{str(create_err)}'")
                    err_str = str(create_err).lower()
                    has_409 = "409" in err_str
                    has_conflict = "conflict" in err_str
                    has_already = "already exists" in err_str
                    logger.error(f"[DEBUG] Condition checks: has_409={has_409}, has_conflict={has_conflict}, has_already={has_already}")

                    if has_409 or has_conflict or has_already:
                        logger.warning(f"[DEBUG] Collection creation conflict detected (another instance created it): {create_err}")
                        logger.info(f"[DEBUG] Proceeding anyway - collection exists")
                    else:
                        # Not a conflict error - reraise
                        logger.error(f"[DEBUG] Not a conflict error - reraising")
                        raise
            else:
                logger.info(f"[DEBUG] Skipping creation - collection already exists")

            self.initialized = True
            logger.info(f"Qdrant collection '{self.collection_name}' ready")

            # Load BM25 index if it exists (for hybrid search persistence)
            if self.enable_sparse:
                self._load_bm25()

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}", exc_info=True)
            return False

    async def _create_collection(self):
        """Create Qdrant collection with hybrid search configuration"""
        # Configure dense vectors (semantic search)
        dense_config = VectorParams(
            size=self.vector_size,
            distance=Distance.COSINE,
            on_disk=False,  # Keep in RAM for speed (we have 96GB!)
        )

        # HNSW configuration for 3-5ms latency
        hnsw_config = HnswConfigDiff(
            m=16,  # Number of edges per node (higher = better accuracy, more memory)
            ef_construct=128,  # Search depth during index build (higher = better quality)
            full_scan_threshold=10000,  # Switch to exact search below this size
            max_indexing_threads=0,  # Use all CPU cores
            on_disk=False,  # Keep HNSW graph in RAM for speed
        )

        # Optimizer configuration for write throughput
        optimizer_config = OptimizersConfigDiff(
            deleted_threshold=0.2,  # Trigger optimization at 20% deleted
            vacuum_min_vector_number=1000,  # Minimum vectors before vacuum
            default_segment_number=0,  # Auto-determine segments
            max_segment_size=None,  # No limit (we have RAM)
            memmap_threshold=None,  # No disk mapping
            indexing_threshold=20000,  # Start indexing after 20k points
            flush_interval_sec=5,  # Flush to disk every 5 seconds
            max_optimization_threads=0,  # Use all CPU cores
        )

        # Create collection with dense vectors
        if self.enable_sparse:
            # Named vectors: "dense" and "sparse"
            vectors_config = {
                "dense": dense_config,
            }
            sparse_vectors_config = {
                "sparse": SparseVectorParams()
            }
        else:
            # Single dense vector
            vectors_config = dense_config
            sparse_vectors_config = None

        if self.use_async:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
                hnsw_config=hnsw_config,
                optimizers_config=optimizer_config,
                shard_number=1,  # Single shard for embedded mode
                replication_factor=1,  # No replication for embedded mode
                write_consistency_factor=1,  # Fast writes
                on_disk_payload=False,  # Keep payload in RAM (we have 96GB!)
            )
        else:
            await asyncio.to_thread(
                self.client.create_collection,
                collection_name=self.collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
                hnsw_config=hnsw_config,
                optimizers_config=optimizer_config,
                shard_number=1,
                replication_factor=1,
                write_consistency_factor=1,
                on_disk_payload=False,
            )

        logger.info("Collection created with hybrid search support")

    def _generate_sparse_vector(self, text: str) -> SparseVector:
        """
        Generate BM25-style sparse vector for keyword matching.

        Args:
            text: Input text

        Returns:
            Sparse vector with BM25 scores
        """
        if not self.bm25:
            logger.warning("BM25 not initialized - returning empty sparse vector")
            return SparseVector(indices=[], values=[])

        # Tokenize query
        tokens = text.lower().split()

        # Get BM25 scores for each document in corpus
        scores = self.bm25.get_scores(tokens)

        # Convert to sparse vector (indices = doc IDs, values = BM25 scores)
        # Take top N non-zero scores for efficiency
        top_n = 100
        top_indices = np.argsort(scores)[-top_n:][::-1]
        top_scores = scores[top_indices]

        # Filter out zeros
        non_zero_mask = top_scores > 0
        indices = top_indices[non_zero_mask].tolist()
        values = top_scores[non_zero_mask].tolist()

        return SparseVector(indices=indices, values=values)

    def _save_bm25(self):
        """Save BM25 index to disk for persistence."""
        if not self.bm25 or not self.tokenized_corpus:
            logger.warning("No BM25 index to save")
            return

        try:
            # Create directory if it doesn't exist
            self.bm25_path.parent.mkdir(parents=True, exist_ok=True)

            # Save both BM25 and tokenized_corpus
            with open(self.bm25_path, 'wb') as f:
                pickle.dump({
                    'bm25': self.bm25,
                    'tokenized_corpus': self.tokenized_corpus
                }, f)

            logger.info(f"BM25 index saved to: {self.bm25_path}")
        except Exception as e:
            logger.error(f"Failed to save BM25 index: {e}")

    def _load_bm25(self):
        """Load BM25 index from disk if it exists."""
        if not self.bm25_path.exists():
            logger.info(f"No BM25 index found at: {self.bm25_path}")
            return

        try:
            with open(self.bm25_path, 'rb') as f:
                data = pickle.load(f)

            self.bm25 = data['bm25']
            self.tokenized_corpus = data['tokenized_corpus']

            logger.info(f"BM25 index loaded from: {self.bm25_path} ({len(self.tokenized_corpus)} documents)")
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            self.bm25 = None
            self.tokenized_corpus = []

    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100,
        show_progress: bool = False,
    ) -> int:
        """
        Index documents into Qdrant with dense + sparse vectors.

        Args:
            documents: List of dicts with keys:
                - text: str (document content)
                - embedding: List[float] (dense vector)
                - metadata: Dict (optional metadata)
                - id: Optional[str] (document ID)
            batch_size: Batch size for indexing
            show_progress: Show progress bar

        Returns:
            Number of documents indexed
        """
        if not self.initialized:
            raise RuntimeError("Qdrant not initialized - call initialize() first")

        logger.info(f"Indexing {len(documents)} documents...")

        # Build BM25 index for sparse vectors if enabled
        if self.enable_sparse:
            logger.info("Building BM25 index for sparse vectors...")
            self.tokenized_corpus = [doc["text"].lower().split() for doc in documents]
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            # Save BM25 index for persistence
            self._save_bm25()

        # Index in batches
        total_indexed = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            points = []

            for idx, doc in enumerate(batch):
                # FIXED: Use integer IDs for Qdrant v1.8.0 compatibility
                point_id = i + idx
                dense_vector = doc["vector"]  # FIXED: Changed from "embedding" to "vector"
                metadata = doc.get("metadata", {})

                # Add text to metadata
                metadata["text"] = doc["text"]

                if self.enable_sparse:
                    # Generate sparse vector
                    sparse_vector = self._generate_sparse_vector(doc["text"])

                    # Point with named vectors
                    point = PointStruct(
                        id=point_id,
                        vector={
                            "dense": dense_vector,
                        },
                        payload=metadata,
                    )
                    # Add sparse vector separately (can't add in same dict)
                    point.vector["sparse"] = sparse_vector
                else:
                    # Point with single vector
                    point = PointStruct(
                        id=point_id,
                        vector=dense_vector,
                        payload=metadata,
                    )

                points.append(point)

            # Upsert batch
            if self.use_async:
                await self.client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                )
            else:
                await asyncio.to_thread(
                    self.client.upsert,
                    collection_name=self.collection_name,
                    points=points,
                )

            total_indexed += len(batch)

            if show_progress:
                logger.info(f"Indexed {total_indexed}/{len(documents)} documents")

        logger.info(f"Successfully indexed {total_indexed} documents")
        return total_indexed

    async def hybrid_search(
        self,
        dense_vector: List[float],
        query_text: str,
        top_k: int = 10,
        dense_limit: int = 20,
        sparse_limit: int = 20,
        fusion: str = "rrf",  # "rrf" or "dbsf"
        query_filter: Optional[Filter] = None,
    ) -> List[QdrantSearchResult]:
        """
        Perform hybrid search with dense + sparse vectors using RRF fusion.

        Args:
            dense_vector: Dense embedding vector
            query_text: Query text for sparse vector
            top_k: Number of final results
            dense_limit: Candidates from dense search (prefetch)
            sparse_limit: Candidates from sparse search (prefetch)
            fusion: Fusion method ("rrf" = Reciprocal Rank Fusion, "dbsf" = Distribution-Based Score Fusion)
            query_filter: Optional filter condition

        Returns:
            List of search results with fused scores
        """
        if not self.initialized:
            raise RuntimeError("Qdrant not initialized")

        if not self.enable_sparse:
            # Fallback to dense-only search
            return await self.search(
                query_vector=dense_vector,
                top_k=top_k,
                query_filter=query_filter,
            )

        # Generate sparse vector from query text
        sparse_vector = self._generate_sparse_vector(query_text)

        # Hybrid search with RRF fusion
        # Uses prefetch pattern: fetch candidates from each modality, then fuse
        if self.use_async:
            results = await self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    # Prefetch from dense vector
                    Prefetch(
                        query=dense_vector,
                        using="dense",
                        limit=dense_limit,
                    ),
                    # Prefetch from sparse vector
                    Prefetch(
                        query=sparse_vector,
                        using="sparse",
                        limit=sparse_limit,
                    ),
                ],
                query=FusionQuery(
                    fusion=Fusion.RRF if fusion == "rrf" else Fusion.DBSF
                ),
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False,  # Don't return vectors (save bandwidth)
            )
        else:
            results = await asyncio.to_thread(
                self.client.query_points,
                collection_name=self.collection_name,
                prefetch=[
                    Prefetch(
                        query=dense_vector,
                        using="dense",
                        limit=dense_limit,
                    ),
                    Prefetch(
                        query=sparse_vector,
                        using="sparse",
                        limit=sparse_limit,
                    ),
                ],
                query=FusionQuery(
                    fusion=Fusion.RRF if fusion == "rrf" else Fusion.DBSF
                ),
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )

        # Convert to QdrantSearchResult
        search_results = []
        for point in results.points:
            search_results.append(QdrantSearchResult(
                id=str(point.id),
                score=point.score,
                payload=point.payload,
            ))

        return search_results

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        query_filter: Optional[Filter] = None,
    ) -> List[QdrantSearchResult]:
        """
        Perform dense-only vector search.

        Args:
            query_vector: Dense embedding vector
            top_k: Number of results
            query_filter: Optional filter condition

        Returns:
            List of search results
        """
        if not self.initialized:
            raise RuntimeError("Qdrant not initialized")

        # Dense vector search
        if self.use_async:
            results = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                using="dense" if self.enable_sparse else None,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
        else:
            results = await asyncio.to_thread(
                self.client.query_points,
                collection_name=self.collection_name,
                query=query_vector,
                using="dense" if self.enable_sparse else None,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )

        # Convert to QdrantSearchResult
        search_results = []
        for point in results.points:
            search_results.append(QdrantSearchResult(
                id=str(point.id),
                score=point.score,
                payload=point.payload,
            ))

        return search_results

    async def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> List[Document]:
        """
        LangChain-compatible similarity search by vector.

        Args:
            embedding: Query embedding vector
            k: Number of results to return
            filter: Optional metadata filter (not yet implemented)
            **kwargs: Additional arguments (ignored)

        Returns:
            List of LangChain Document objects
        """
        if not self.initialized:
            raise RuntimeError("Qdrant not initialized - call initialize() first")

        # Convert filter to Qdrant format if provided (simplified for now)
        qdrant_filter = None
        if filter:
            # TODO: Implement proper filter conversion
            logger.warning("Metadata filtering not yet implemented for Qdrant")

        # Perform search using v1.8.0-compatible search() API
        # FIXED: Changed from query_points() to search() for Qdrant v1.8.0 compatibility
        # FIXED: Added using="dense" for named vector support when sparse vectors are enabled
        if self.use_async:
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=("dense", embedding) if self.enable_sparse else embedding,
                query_filter=qdrant_filter,
                limit=k,
                with_payload=True,
                with_vectors=False,
            )
        else:
            results = await asyncio.to_thread(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=("dense", embedding) if self.enable_sparse else embedding,
                query_filter=qdrant_filter,
                limit=k,
                with_payload=True,
                with_vectors=False,
            )

        # Convert to LangChain Document objects
        # Note: search() returns a list of ScoredPoint objects directly, not a results wrapper
        documents = []
        for point in results:
            # Extract text from payload
            text = point.payload.get("text", "")

            # Create metadata without 'text' field
            metadata = {k: v for k, v in point.payload.items() if k != "text"}
            metadata["score"] = point.score  # Add similarity score to metadata

            documents.append(Document(
                page_content=text,
                metadata=metadata
            ))

        return documents

    async def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection information and statistics.

        Returns:
            Dict with collection info
        """
        if not self.initialized:
            raise RuntimeError("Qdrant not initialized")

        if self.use_async:
            info: CollectionInfo = await self.client.get_collection(self.collection_name)
        else:
            info: CollectionInfo = await asyncio.to_thread(
                self.client.get_collection,
                self.collection_name
            )

        return {
            "name": self.collection_name,
            "points_count": info.points_count,
            "segments_count": info.segments_count,
            "status": info.status.value,
            "vector_size": self.vector_size,
            "indexed_vectors_count": info.indexed_vectors_count,
        }

    async def close(self):
        """Close Qdrant client"""
        if self.use_async and hasattr(self.client, 'close'):
            await self.client.close()
        logger.info("Qdrant client closed")


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize Qdrant in embedded mode
        store = QdrantVectorStore(
            collection_name="test_collection",
            vector_size=1024,
            path="./qdrant_test",
            enable_sparse=True,
        )

        # Initialize collection
        await store.initialize(recreate=True)

        # Index sample documents
        documents = [
            {
                "text": "Qdrant is a vector database with hybrid search",
                "embedding": np.random.rand(1024).tolist(),
                "metadata": {"source": "docs", "category": "database"},
                "id": "doc_1",
            },
            {
                "text": "Hybrid search combines dense and sparse vectors",
                "embedding": np.random.rand(1024).tolist(),
                "metadata": {"source": "docs", "category": "search"},
                "id": "doc_2",
            },
        ]

        await store.index_documents(documents)

        # Hybrid search
        results = await store.hybrid_search(
            dense_vector=np.random.rand(1024).tolist(),
            query_text="vector database search",
            top_k=2,
        )

        for result in results:
            print(f"ID: {result.id}, Score: {result.score:.4f}")
            print(f"Text: {result.payload.get('text', 'N/A')}\n")

        # Get collection info
        info = await store.get_collection_info()
        print(f"Collection info: {info}")

        await store.close()

    asyncio.run(main())
