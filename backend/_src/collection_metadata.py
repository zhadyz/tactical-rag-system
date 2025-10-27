"""
ATLAS Protocol - Collection Metadata

Analyzes and caches metadata about the document collection for scope detection.
Helps determine whether queries are in-scope or out-of-scope for better UX.
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class CollectionMetadata:
    """
    Manages collection-level metadata for scope detection.

    Features:
    - Document count and statistics
    - Topic extraction and clustering
    - Scope boundaries
    - Cache metadata to disk
    """

    def __init__(
        self,
        total_docs: int = 0,
        total_chunks: int = 0,
        topics: Optional[List[str]] = None,
        metadata_dict: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize collection metadata.

        Args:
            total_docs: Number of documents in collection
            total_chunks: Number of text chunks
            topics: List of identified topics
            metadata_dict: Additional metadata
        """
        self.total_docs = total_docs
        self.total_chunks = total_chunks
        self.topics = topics or []
        self.metadata = metadata_dict or {}
        self.computed_at = datetime.now()

        logger.debug(
            f"CollectionMetadata: {total_docs} docs, "
            f"{total_chunks} chunks, {len(self.topics)} topics"
        )

    @classmethod
    def load_or_compute(
        cls,
        vectorstore,
        embeddings,
        llm=None,
        metadata_path: Optional[Path] = None,
        force_recompute: bool = False
    ):
        """
        Load metadata from cache or compute fresh.

        Args:
            vectorstore: Vector database instance
            embeddings: Embedding model
            llm: LLM for topic extraction (optional)
            metadata_path: Path to cached metadata file
            force_recompute: Force recomputation even if cache exists

        Returns:
            CollectionMetadata instance
        """
        # Try loading from cache
        if metadata_path and metadata_path.exists() and not force_recompute:
            try:
                logger.info(f"Loading collection metadata from {metadata_path}")
                return cls.load_from_file(metadata_path)
            except Exception as e:
                logger.warning(f"Failed to load cached metadata: {e}")

        # Compute fresh metadata
        logger.info("Computing collection metadata...")
        metadata = cls._compute_metadata(vectorstore, embeddings, llm)

        # Save to cache
        if metadata_path:
            try:
                metadata.save_to_file(metadata_path)
                logger.info(f"Metadata cached to {metadata_path}")
            except Exception as e:
                logger.warning(f"Failed to cache metadata: {e}")

        return metadata

    @classmethod
    def _compute_metadata(cls, vectorstore, embeddings, llm=None):
        """
        Compute metadata from vectorstore.

        Args:
            vectorstore: Vector database
            embeddings: Embedding model
            llm: LLM for topic extraction

        Returns:
            CollectionMetadata instance
        """
        try:
            # Get collection stats
            collection = vectorstore._collection
            total_chunks = collection.count()

            # Estimate documents (approximate)
            total_docs = max(1, total_chunks // 10)  # Rough estimate

            # TODO: Extract topics using LLM (future enhancement)
            topics = ["General Knowledge", "Technical Documentation"]

            metadata_dict = {
                "collection_name": collection.name,
                "embedding_model": getattr(embeddings, 'model_name', 'unknown'),
                "computed_at": datetime.now().isoformat()
            }

            logger.info(f"Metadata computed: {total_docs} docs, {total_chunks} chunks")

            return cls(
                total_docs=total_docs,
                total_chunks=total_chunks,
                topics=topics,
                metadata_dict=metadata_dict
            )

        except Exception as e:
            logger.error(f"Metadata computation failed: {e}")
            # Return empty metadata
            return cls()

    def save_to_file(self, path: Path) -> None:
        """Save metadata to JSON file"""
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "total_docs": self.total_docs,
            "total_chunks": self.total_chunks,
            "topics": self.topics,
            "metadata": self.metadata,
            "computed_at": self.computed_at.isoformat()
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Metadata saved to {path}")

    @classmethod
    def load_from_file(cls, path: Path):
        """Load metadata from JSON file"""
        with open(path, 'r') as f:
            data = json.load(f)

        metadata = cls(
            total_docs=data.get("total_docs", 0),
            total_chunks=data.get("total_chunks", 0),
            topics=data.get("topics", []),
            metadata_dict=data.get("metadata", {})
        )

        # Restore timestamp
        if "computed_at" in data:
            metadata.computed_at = datetime.fromisoformat(data["computed_at"])

        logger.debug(f"Metadata loaded from {path}")
        return metadata

    def get_summary(self) -> str:
        """Get human-readable summary"""
        return (
            f"Collection: {self.total_docs} documents, "
            f"{self.total_chunks} chunks, "
            f"Topics: {', '.join(self.topics[:3])}"
        )


# Alias for optimized version (same implementation for now)
CollectionMetadataOptimized = CollectionMetadata
