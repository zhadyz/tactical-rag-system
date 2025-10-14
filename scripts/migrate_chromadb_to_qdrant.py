"""
Migration Script: ChromaDB to Qdrant
Migrates existing ChromaDB vector database to Qdrant for better performance at scale

Usage:
    python scripts/migrate_chromadb_to_qdrant.py [--batch-size 100] [--verify]

Requirements:
    - ChromaDB collection at ./chroma_db (default location)
    - Qdrant server running (default: localhost:6333)
    - Ollama embeddings server running (for regenerating embeddings if needed)
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path
from typing import List, Dict
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "_src"))

from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from qdrant_store import QdrantVectorStore
from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_chromadb_to_qdrant(
    chroma_path: str,
    qdrant_host: str,
    qdrant_port: int,
    collection_name: str,
    batch_size: int = 100,
    verify: bool = True
):
    """
    Migrate ChromaDB to Qdrant

    Args:
        chroma_path: Path to ChromaDB persist directory
        qdrant_host: Qdrant server host
        qdrant_port: Qdrant server port
        collection_name: Target collection name in Qdrant
        batch_size: Batch size for indexing
        verify: Whether to verify migration after completion
    """

    logger.info("=" * 60)
    logger.info("CHROMADB TO QDRANT MIGRATION")
    logger.info("=" * 60)

    # Load configuration
    config = load_config()

    # Initialize embeddings
    logger.info("\n1. Initializing embeddings model...")
    embeddings = OllamaEmbeddings(
        model=config.embedding.model_name,
        base_url=config.ollama_host
    )
    test_embed = await asyncio.to_thread(embeddings.embed_query, "test")
    logger.info(f"   Embeddings ready (dimension: {len(test_embed)})")

    # Load ChromaDB
    logger.info(f"\n2. Loading ChromaDB from {chroma_path}...")
    if not Path(chroma_path).exists():
        logger.error(f"   ChromaDB not found at {chroma_path}")
        return False

    chroma = Chroma(
        persist_directory=chroma_path,
        embedding_function=embeddings
    )

    # Get all documents from ChromaDB
    logger.info("   Extracting documents from ChromaDB...")
    collection = chroma._collection
    results = collection.get(include=["metadatas", "documents", "embeddings"])

    total_docs = len(results["ids"])
    logger.info(f"   Found {total_docs} documents in ChromaDB")

    if total_docs == 0:
        logger.error("   No documents found in ChromaDB!")
        return False

    # Convert to Qdrant format
    logger.info("\n3. Converting documents to Qdrant format...")
    documents = []
    for i in range(total_docs):
        documents.append({
            "text": results["documents"][i],
            "embedding": results["embeddings"][i],
            "metadata": results["metadatas"][i]
        })

    logger.info(f"   Converted {len(documents)} documents")

    # Initialize Qdrant
    logger.info(f"\n4. Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
    try:
        qdrant_store = QdrantVectorStore(
            host=qdrant_host,
            port=qdrant_port,
            collection_name=collection_name,
            vector_size=len(test_embed)
        )
        logger.info("   Connected to Qdrant")
    except Exception as e:
        logger.error(f"   Failed to connect to Qdrant: {e}")
        logger.error("   Make sure Qdrant server is running!")
        return False

    # Create collection
    logger.info(f"\n5. Creating Qdrant collection '{collection_name}'...")
    try:
        qdrant_store.create_collection(recreate=False)
        logger.info("   Collection created")
    except Exception as e:
        logger.warning(f"   Collection creation issue: {e}")

    # Index documents
    logger.info(f"\n6. Indexing documents (batch size: {batch_size})...")
    try:
        await qdrant_store.index_documents(
            documents=documents,
            batch_size=batch_size,
            show_progress=True
        )
    except Exception as e:
        logger.error(f"   Indexing failed: {e}")
        return False

    # Verify migration
    if verify:
        logger.info("\n7. Verifying migration...")
        qdrant_info = qdrant_store.get_collection_info()
        qdrant_count = qdrant_info['points_count']

        logger.info(f"   ChromaDB documents: {total_docs}")
        logger.info(f"   Qdrant points:     {qdrant_count}")

        if total_docs == qdrant_count:
            logger.info("   ✓ Migration verified - counts match!")
        else:
            logger.warning(f"   ⚠ Count mismatch! Missing {total_docs - qdrant_count} documents")
            return False

        # Test search
        logger.info("\n8. Testing search functionality...")
        try:
            query = "test query"
            query_vector = await asyncio.to_thread(embeddings.embed_query, query)
            search_results = await qdrant_store.search(
                query_vector=query_vector,
                top_k=3
            )
            logger.info(f"   ✓ Search successful - returned {len(search_results)} results")
        except Exception as e:
            logger.error(f"   Search test failed: {e}")
            return False

    logger.info("\n" + "=" * 60)
    logger.info("MIGRATION COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"\nNext steps:")
    logger.info(f"1. Set USE_QDRANT=true in your environment or .env file")
    logger.info(f"2. Restart your application")
    logger.info(f"3. Verify the system is using Qdrant in the status display")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate ChromaDB to Qdrant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/migrate_chromadb_to_qdrant.py
  python scripts/migrate_chromadb_to_qdrant.py --batch-size 200
  python scripts/migrate_chromadb_to_qdrant.py --no-verify
        """
    )

    parser.add_argument(
        "--chroma-path",
        type=str,
        default="./chroma_db",
        help="Path to ChromaDB directory (default: ./chroma_db)"
    )

    parser.add_argument(
        "--qdrant-host",
        type=str,
        default="localhost",
        help="Qdrant host (default: localhost)"
    )

    parser.add_argument(
        "--qdrant-port",
        type=int,
        default=6333,
        help="Qdrant port (default: 6333)"
    )

    parser.add_argument(
        "--collection-name",
        type=str,
        default="air_force_docs",
        help="Qdrant collection name (default: air_force_docs)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for indexing (default: 100)"
    )

    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip verification after migration"
    )

    args = parser.parse_args()

    # Run migration
    success = asyncio.run(
        migrate_chromadb_to_qdrant(
            chroma_path=args.chroma_path,
            qdrant_host=args.qdrant_host,
            qdrant_port=args.qdrant_port,
            collection_name=args.collection_name,
            batch_size=args.batch_size,
            verify=not args.no_verify
        )
    )

    if success:
        logger.info("\n✓ Migration successful!")
        sys.exit(0)
    else:
        logger.error("\n✗ Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
