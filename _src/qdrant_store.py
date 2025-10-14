"""
Qdrant Vector Store - Production-grade vector database for large-scale RAG
Replaces ChromaDB for better performance at scale (500k-2M vectors)
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    SearchParams, QuantizationConfig, ScalarQuantization
)

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result from Qdrant"""
    id: int
    score: float
    text: str
    metadata: Dict


class QdrantVectorStore:
    """
    Production-grade vector store optimized for Air Force documentation

    Features:
    - HNSW indexing for sub-second search at 500k+ vectors
    - Quantization for 4x memory reduction
    - Filtering by document ID, category, etc.
    - Batch operations for efficient indexing
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "air_force_docs",
        vector_size: int = 768
    ):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.vector_size = vector_size

        logger.info(f"Connected to Qdrant at {host}:{port}")

    def create_collection(self, recreate: bool = False):
        """
        Create optimized collection for production use

        Args:
            recreate: If True, delete existing collection first
        """

        if recreate and self.client.collection_exists(self.collection_name):
            logger.warning(f"Deleting existing collection: {self.collection_name}")
            self.client.delete_collection(self.collection_name)

        if self.client.collection_exists(self.collection_name):
            logger.info(f"Collection {self.collection_name} already exists")
            return

        logger.info(f"Creating collection {self.collection_name} with vector size {self.vector_size}")

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE,
            ),
            # HNSW optimization for large-scale search
            # These params balance speed vs accuracy
            hnsw_config={
                "m": 16,                    # Connections per layer (higher = better recall, more memory)
                "ef_construct": 200,        # Construction quality (higher = better index, slower build)
                "full_scan_threshold": 10000  # Use brute force below this threshold
            },
            # Quantization reduces memory by 4x with minimal accuracy loss
            quantization_config=ScalarQuantization(
                scalar=ScalarQuantization.ScalarQuantizationConfig(
                    type="int8",
                    quantile=0.99,
                    always_ram=True  # Keep quantized vectors in RAM for speed
                )
            )
        )

        logger.info(f"Collection {self.collection_name} created successfully")

    async def index_documents(
        self,
        documents: List[Dict],
        batch_size: int = 100,
        show_progress: bool = True
    ):
        """
        Index documents in batches for efficiency

        Args:
            documents: List of dicts with keys: text, embedding, metadata
            batch_size: Number of documents per batch
            show_progress: Log progress every batch

        Expected format:
        {
            "text": "chunk content",
            "embedding": [0.1, 0.2, ...],  # numpy array or list
            "metadata": {
                "document_id": "AFI-36-2903",
                "file_name": "dafi36-2903.pdf",
                "page": 10,
                "chunk_index": 5,
                "category": "uniform_regulations"
            }
        }
        """

        total_docs = len(documents)
        logger.info(f"Indexing {total_docs} documents in batches of {batch_size}")

        points = []
        indexed_count = 0

        for i, doc in enumerate(documents):
            # Convert numpy array to list if needed
            embedding = doc["embedding"]
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()

            # Create point with unique ID
            point = PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "text": doc["text"],
                    **doc.get("metadata", {})
                }
            )
            points.append(point)

            # Batch upsert when batch is full
            if len(points) >= batch_size:
                await asyncio.to_thread(
                    self.client.upsert,
                    collection_name=self.collection_name,
                    points=points
                )
                indexed_count += len(points)
                points = []

                if show_progress:
                    progress_pct = (indexed_count / total_docs) * 100
                    logger.info(f"Indexed {indexed_count}/{total_docs} ({progress_pct:.1f}%)")

        # Upsert remaining points
        if points:
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=points
            )
            indexed_count += len(points)

        logger.info(f"Indexing complete: {indexed_count}/{total_docs} documents")

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict] = None,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Search for similar vectors with optional filtering

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional filters, e.g. {"document_id": "AFI-36-2903"}
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of SearchResult objects
        """

        # Build Qdrant filter if provided
        qdrant_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                qdrant_filter = Filter(must=conditions)

        # Execute search
        results = await asyncio.to_thread(
            self.client.search,
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            search_params=SearchParams(
                hnsw_ef=128,  # Search quality (higher = better, slower)
                exact=False   # Use approximate search for speed
            ),
            score_threshold=score_threshold
        )

        # Convert to SearchResult objects
        search_results = []
        for hit in results:
            search_results.append(SearchResult(
                id=hit.id,
                score=hit.score,
                text=hit.payload.get("text", ""),
                metadata={
                    k: v for k, v in hit.payload.items()
                    if k != "text"
                }
            ))

        return search_results

    async def search_by_document(
        self,
        query_vector: List[float],
        document_id: str,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Search within a specific document only

        This is a MASSIVE performance optimization when users mention
        specific document IDs (e.g., "In AFI 36-2903, what are...")

        Reduces search space by 99%+ for large collections
        """

        return await self.search(
            query_vector=query_vector,
            top_k=top_k,
            filters={"document_id": document_id}
        )

    def get_collection_info(self) -> Dict:
        """Get collection statistics"""

        info = self.client.get_collection(self.collection_name)

        return {
            "name": self.collection_name,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "points_count": info.points_count,
            "status": info.status.value,
            "config": {
                "distance": info.config.params.vectors.distance.value,
                "vector_size": info.config.params.vectors.size
            }
        }

    async def delete_by_document(self, document_id: str):
        """
        Delete all chunks from a specific document

        Useful for incremental updates when a document is modified
        """

        await asyncio.to_thread(
            self.client.delete,
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )

        logger.info(f"Deleted all chunks for document: {document_id}")


# Utility functions for migration

def convert_langchain_to_qdrant(langchain_docs: List) -> List[Dict]:
    """
    Convert LangChain Document objects to Qdrant format

    Args:
        langchain_docs: List of LangChain Document objects

    Returns:
        List of dicts ready for Qdrant indexing
    """

    qdrant_docs = []

    for i, doc in enumerate(langchain_docs):
        qdrant_doc = {
            "text": doc.page_content,
            "embedding": None,  # Will be filled by embedding function
            "metadata": {
                "document_id": doc.metadata.get("file_name", f"doc_{i}").replace(".pdf", ""),
                "file_name": doc.metadata.get("file_name", "unknown"),
                "page": doc.metadata.get("page_number", 0),
                "chunk_index": doc.metadata.get("chunk_index", i),
                "category": doc.metadata.get("category", "general")
            }
        }
        qdrant_docs.append(qdrant_doc)

    return qdrant_docs


async def migrate_chromadb_to_qdrant(
    chroma_path: str,
    qdrant_store: QdrantVectorStore,
    embeddings_func,
    batch_size: int = 100
):
    """
    Migrate existing ChromaDB collection to Qdrant

    Args:
        chroma_path: Path to ChromaDB persist directory
        qdrant_store: Initialized QdrantVectorStore
        embeddings_func: Function to generate embeddings
        batch_size: Batch size for indexing
    """

    from langchain_chroma import Chroma

    logger.info(f"Loading ChromaDB from {chroma_path}")

    # Load ChromaDB
    chroma = Chroma(
        persist_directory=chroma_path,
        embedding_function=embeddings_func
    )

    # Get all documents
    # Note: ChromaDB doesn't have a direct "get all" method, so we use a workaround
    collection = chroma._collection
    results = collection.get(include=["metadatas", "documents", "embeddings"])

    documents = []
    for i in range(len(results["ids"])):
        documents.append({
            "text": results["documents"][i],
            "embedding": results["embeddings"][i],
            "metadata": results["metadatas"][i]
        })

    logger.info(f"Found {len(documents)} documents in ChromaDB")

    # Create Qdrant collection
    qdrant_store.create_collection(recreate=False)

    # Index documents
    await qdrant_store.index_documents(documents, batch_size=batch_size)

    logger.info("Migration complete!")

    # Verify counts match
    qdrant_info = qdrant_store.get_collection_info()
    logger.info(f"ChromaDB: {len(documents)} docs | Qdrant: {qdrant_info['points_count']} docs")

    if len(documents) == qdrant_info['points_count']:
        logger.info("✓ Migration verified - counts match!")
    else:
        logger.warning("⚠ Migration counts don't match - manual verification needed")
