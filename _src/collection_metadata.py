"""
Collection Metadata System - Domain-Agnostic Scope Detection

Automatically learns the semantic boundaries of any document collection
without hardcoded keywords. Works for Air Force docs, networking guides,
policies, recipes, or any other domain.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from langchain_chroma import Chroma
from langchain_community.llms import Ollama as OllamaLLM
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class CollectionMetadata:
    """
    Computes and stores semantic metadata about a document collection

    Attributes:
        centroid: Average embedding vector representing the collection's semantic center
        avg_distance: Average distance from centroid (defines the "radius" of valid queries)
        scope_summary: LLM-generated description of what topics the collection covers
        sample_queries: Example queries that should be in-scope
    """

    def __init__(
        self,
        centroid: Optional[np.ndarray] = None,
        avg_distance: Optional[float] = None,
        std_distance: Optional[float] = None,
        scope_summary: Optional[str] = None,
        sample_queries: Optional[List[str]] = None,
        metadata_path: Path = Path("data/collection_metadata.json")
    ):
        self.centroid = centroid
        self.avg_distance = avg_distance
        self.std_distance = std_distance
        self.scope_summary = scope_summary
        self.sample_queries = sample_queries or []
        self.metadata_path = metadata_path

    @classmethod
    def load_or_compute(
        cls,
        vectorstore: Chroma,
        embeddings: HuggingFaceEmbeddings,
        llm: OllamaLLM,
        metadata_path: Path = Path("data/collection_metadata.json"),
        force_recompute: bool = False
    ) -> "CollectionMetadata":
        """
        Load existing metadata or compute if not available

        Args:
            vectorstore: The vector database containing document embeddings
            embeddings: Embedding model used for the collection
            llm: LLM for generating scope summaries
            metadata_path: Where to save/load metadata
            force_recompute: If True, recompute even if metadata exists
        """

        # Try to load existing metadata
        if metadata_path.exists() and not force_recompute:
            try:
                logger.info(f"Loading collection metadata from {metadata_path}")
                return cls.load_from_file(metadata_path)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}. Recomputing...")

        # Compute new metadata
        logger.info("Computing collection metadata (this may take 1-2 minutes)...")
        metadata = cls._compute_metadata(vectorstore, embeddings, llm)

        # Save for future use
        metadata.save_to_file(metadata_path)

        return metadata

    @classmethod
    def _compute_metadata(
        cls,
        vectorstore: Chroma,
        embeddings: HuggingFaceEmbeddings,
        llm: OllamaLLM
    ) -> "CollectionMetadata":
        """Compute semantic metadata from scratch"""

        logger.info("Step 1/4: Retrieving all document chunks...")

        # Get all documents from vectorstore
        # ChromaDB doesn't have a direct "get all" method, so we use a trick:
        # Search for a common word that appears in most documents
        all_docs = vectorstore.get()

        if not all_docs or not all_docs.get('documents'):
            raise ValueError("No documents found in vectorstore")

        documents = all_docs['documents']
        embeddings_list = all_docs.get('embeddings', [])

        logger.info(f"Found {len(documents)} document chunks")

        # If embeddings not returned, compute them
        if not embeddings_list:
            logger.info("Step 2/4: Computing embeddings for all chunks...")
            embeddings_list = [
                embeddings.embed_query(doc)
                for doc in documents
            ]

        embeddings_array = np.array(embeddings_list)

        logger.info("Step 2/4: Computing semantic centroid...")
        centroid = np.mean(embeddings_array, axis=0)

        logger.info("Step 3/4: Computing distance statistics...")
        # Calculate distance from each embedding to centroid
        distances = [
            np.linalg.norm(emb - centroid)
            for emb in embeddings_array
        ]

        avg_distance = float(np.mean(distances))
        std_distance = float(np.std(distances))

        logger.info(f"  Avg distance: {avg_distance:.4f}")
        logger.info(f"  Std distance: {std_distance:.4f}")

        logger.info("Step 4/4: Generating scope summary with LLM...")
        scope_summary = cls._generate_scope_summary(documents, llm)

        logger.info("✓ Collection metadata computed successfully!")

        return cls(
            centroid=centroid,
            avg_distance=avg_distance,
            std_distance=std_distance,
            scope_summary=scope_summary,
            sample_queries=[]
        )

    @staticmethod
    def _generate_scope_summary(documents: List[str], llm: OllamaLLM) -> str:
        """Generate LLM-based description of collection scope"""

        # Sample up to 15 diverse chunks for analysis
        sample_size = min(15, len(documents))
        step = len(documents) // sample_size
        sample_docs = [documents[i * step] for i in range(sample_size)]

        # Create compact sample text (max 2000 chars)
        sample_text = "\n---\n".join([
            doc[:200] + "..." if len(doc) > 200 else doc
            for doc in sample_docs
        ])[:2000]

        prompt = f"""Analyze these document excerpts and describe what topics they cover.
Be specific and concise (2-3 sentences max).

Document excerpts:
{sample_text}

What topics/domains do these documents cover?"""

        try:
            response = llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Failed to generate scope summary: {e}")
            return "Document collection (scope summary unavailable)"

    def is_query_in_scope(
        self,
        query_embedding: np.ndarray,
        strict_threshold: float = 1.5,
        relaxed_threshold: float = 2.0
    ) -> tuple[bool, str, float]:
        """
        Check if a query is within the semantic boundaries of the collection

        Args:
            query_embedding: Embedding vector of the user query
            strict_threshold: Multiplier of avg_distance for strict checking (default 1.5)
            relaxed_threshold: Multiplier for relaxed checking (default 2.0)

        Returns:
            (is_in_scope, message, distance)
        """

        if self.centroid is None:
            # Fallback: Can't determine scope without centroid
            return True, "", 0.0

        # Calculate distance from query to collection centroid
        distance = float(np.linalg.norm(query_embedding - self.centroid))

        # Normalize by average distance (makes threshold meaningful)
        normalized_distance = distance / self.avg_distance

        logger.info(f"Query distance from centroid: {distance:.4f} (normalized: {normalized_distance:.2f}x avg)")

        # Clearly in scope
        if normalized_distance <= strict_threshold:
            return True, "", normalized_distance

        # Clearly out of scope
        if normalized_distance > relaxed_threshold:
            message = (
                f"This query appears to be outside the scope of the available documents. "
                f"The document collection covers: {self.scope_summary}"
            )
            return False, message, normalized_distance

        # Borderline (between strict and relaxed)
        # Allow but warn
        return True, "", normalized_distance

    def save_to_file(self, path: Path):
        """Save metadata to JSON file"""

        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "centroid": self.centroid.tolist() if self.centroid is not None else None,
            "avg_distance": self.avg_distance,
            "std_distance": self.std_distance,
            "scope_summary": self.scope_summary,
            "sample_queries": self.sample_queries
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"✓ Saved collection metadata to {path}")

    @classmethod
    def load_from_file(cls, path: Path) -> "CollectionMetadata":
        """Load metadata from JSON file"""

        with open(path, 'r') as f:
            data = json.load(f)

        centroid = np.array(data['centroid']) if data['centroid'] else None

        return cls(
            centroid=centroid,
            avg_distance=data.get('avg_distance'),
            std_distance=data.get('std_distance'),
            scope_summary=data.get('scope_summary'),
            sample_queries=data.get('sample_queries', []),
            metadata_path=path
        )

    def __repr__(self):
        return (
            f"CollectionMetadata(avg_distance={self.avg_distance:.4f}, "
            f"scope='{self.scope_summary[:50]}...')"
        )


def compute_collection_metadata_cli(
    vectorstore_path: str = "data/chroma_db",
    output_path: str = "data/collection_metadata.json"
):
    """
    CLI utility to compute collection metadata

    Usage:
        python -m _src.collection_metadata
    """

    from _src.config import load_config

    logger.info("Loading configuration...")
    config = load_config()

    logger.info("Loading vector store...")
    embeddings = HuggingFaceEmbeddings(
        model_name=config.embeddings.model_name,
        model_kwargs={'device': 'cuda'},
        encode_kwargs={'device': 'cuda', 'batch_size': 32}
    )

    vectorstore = Chroma(
        persist_directory=vectorstore_path,
        embedding_function=embeddings,
        collection_name="afi_documents"
    )

    logger.info("Loading LLM...")
    llm = OllamaLLM(
        model=config.llm.model_name,
        base_url=config.llm.base_url
    )

    logger.info("Computing metadata...")
    metadata = CollectionMetadata.load_or_compute(
        vectorstore=vectorstore,
        embeddings=embeddings,
        llm=llm,
        metadata_path=Path(output_path),
        force_recompute=True
    )

    logger.info("\n" + "="*80)
    logger.info("COLLECTION METADATA SUMMARY")
    logger.info("="*80)
    logger.info(f"Scope: {metadata.scope_summary}")
    logger.info(f"Avg Distance: {metadata.avg_distance:.4f}")
    logger.info(f"Std Distance: {metadata.std_distance:.4f}")
    logger.info(f"Saved to: {output_path}")
    logger.info("="*80)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    compute_collection_metadata_cli()
