#!/usr/bin/env python3
"""
Migration Script: ChromaDB → Qdrant + vLLM Production Setup

This script migrates your existing RAG system to production infrastructure:
1. Migrate ChromaDB vectors to Qdrant
2. Test Qdrant performance
3. Configure vLLM for fast inference
4. Setup embedding cache
5. Validate end-to-end pipeline

Usage:
    python scripts/migrate_to_production.py --dry-run  # Test without changes
    python scripts/migrate_to_production.py           # Execute migration
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
import time
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from _src.qdrant_store import QdrantVectorStore, migrate_chromadb_to_qdrant
from _src.embedding_cache import EmbeddingCache
from _src.config import load_config
from langchain_community.embeddings import OllamaEmbeddings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionMigrator:
    """Handles migration to production infrastructure"""

    def __init__(self, config, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.results = {}

    async def migrate(self):
        """Execute full migration"""

        logger.info("=" * 70)
        logger.info("PRODUCTION MIGRATION STARTED")
        logger.info("=" * 70)

        if self.dry_run:
            logger.warning("DRY RUN MODE - No changes will be made")

        # Step 1: Verify prerequisites
        logger.info("\n[Step 1/6] Verifying prerequisites...")
        await self._verify_prerequisites()

        # Step 2: Setup Qdrant
        logger.info("\n[Step 2/6] Setting up Qdrant vector database...")
        qdrant_store = await self._setup_qdrant()

        # Step 3: Migrate data
        logger.info("\n[Step 3/6] Migrating data from ChromaDB to Qdrant...")
        await self._migrate_data(qdrant_store)

        # Step 4: Setup embedding cache
        logger.info("\n[Step 4/6] Setting up Redis embedding cache...")
        await self._setup_embedding_cache()

        # Step 5: Test vLLM
        logger.info("\n[Step 5/6] Testing vLLM inference server...")
        await self._test_vllm()

        # Step 6: Validate pipeline
        logger.info("\n[Step 6/6] Validating end-to-end pipeline...")
        await self._validate_pipeline(qdrant_store)

        # Summary
        self._print_summary()

    async def _verify_prerequisites(self):
        """Verify all required services are running"""

        checks = {
            "Qdrant": ("localhost", 6333),
            "Redis": ("localhost", 6379),
            "vLLM": ("localhost", 8001)
        }

        for service, (host, port) in checks.items():
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    logger.info(f"✓ {service} is running on {host}:{port}")
                    self.results[f"{service}_available"] = True
                else:
                    logger.error(f"✗ {service} is not running on {host}:{port}")
                    logger.error(f"  Start with: docker-compose -f docker-compose.production.yml up {service.lower()} -d")
                    self.results[f"{service}_available"] = False

            except Exception as e:
                logger.error(f"✗ Failed to check {service}: {e}")
                self.results[f"{service}_available"] = False

        # Check ChromaDB exists
        chroma_path = self.config.vector_db_dir
        if chroma_path.exists():
            logger.info(f"✓ ChromaDB found at {chroma_path}")
            self.results["chromadb_exists"] = True
        else:
            logger.error(f"✗ ChromaDB not found at {chroma_path}")
            logger.error("  Run indexing first: python _src/index_documents.py")
            self.results["chromadb_exists"] = False

        # Check if we can proceed
        if not all([
            self.results.get("Qdrant_available"),
            self.results.get("Redis_available"),
            self.results.get("chromadb_exists")
        ]):
            logger.error("\n✗ Prerequisites not met. Cannot proceed.")
            sys.exit(1)

    async def _setup_qdrant(self) -> QdrantVectorStore:
        """Setup Qdrant collection"""

        qdrant = QdrantVectorStore(
            host="localhost",
            port=6333,
            collection_name="air_force_docs_production",
            vector_size=768  # nomic-embed-text dimension
        )

        if not self.dry_run:
            # Create collection with production config
            qdrant.create_collection(recreate=False)
            logger.info("✓ Qdrant collection created/verified")
        else:
            logger.info("(dry-run) Would create Qdrant collection")

        self.results["qdrant_setup"] = True
        return qdrant

    async def _migrate_data(self, qdrant_store: QdrantVectorStore):
        """Migrate ChromaDB data to Qdrant"""

        start_time = time.time()

        if self.dry_run:
            logger.info("(dry-run) Would migrate ChromaDB → Qdrant")
            self.results["migration_time"] = 0
            self.results["documents_migrated"] = 0
            return

        # Initialize embeddings
        embeddings = OllamaEmbeddings(
            model=self.config.embedding.model_name,
            base_url=self.config.ollama_host
        )

        # Migrate
        try:
            await migrate_chromadb_to_qdrant(
                chroma_path=str(self.config.vector_db_dir),
                qdrant_store=qdrant_store,
                embeddings_func=embeddings,
                batch_size=100
            )

            elapsed = time.time() - start_time
            info = qdrant_store.get_collection_info()

            logger.info(f"✓ Migration complete in {elapsed:.1f}s")
            logger.info(f"  Migrated {info['points_count']} documents")

            self.results["migration_time"] = elapsed
            self.results["documents_migrated"] = info['points_count']

        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            self.results["migration_failed"] = str(e)
            raise

    async def _setup_embedding_cache(self):
        """Setup Redis embedding cache"""

        cache = EmbeddingCache(
            redis_url="redis://localhost:6379",
            ttl=86400 * 7  # 7 days
        )

        try:
            await cache.connect()
            logger.info("✓ Redis embedding cache connected")

            # Test cache
            if not self.dry_run:
                import numpy as np
                test_embedding = np.random.rand(768).astype(np.float32)
                await cache.set("test_text", test_embedding)
                cached = await cache.get("test_text")

                if cached is not None and np.allclose(cached, test_embedding):
                    logger.info("✓ Cache read/write test passed")
                    self.results["cache_test"] = "passed"
                else:
                    logger.warning("⚠ Cache test failed")
                    self.results["cache_test"] = "failed"

            await cache.close()

        except Exception as e:
            logger.error(f"✗ Cache setup failed: {e}")
            self.results["cache_test"] = "error"

    async def _test_vllm(self):
        """Test vLLM inference server"""

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                async with session.get("http://localhost:8001/health") as resp:
                    if resp.status == 200:
                        logger.info("✓ vLLM server is healthy")
                    else:
                        logger.warning(f"⚠ vLLM health check returned {resp.status}")

                # Test inference
                if not self.dry_run:
                    start = time.time()

                    async with session.post(
                        "http://localhost:8001/v1/completions",
                        json={
                            "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                            "prompt": "What is 2+2? Answer:",
                            "max_tokens": 10,
                            "temperature": 0.0
                        }
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            elapsed = time.time() - start

                            logger.info(f"✓ vLLM inference test passed ({elapsed:.2f}s)")
                            logger.info(f"  Response: {result['choices'][0]['text']}")

                            self.results["vllm_latency"] = elapsed
                            self.results["vllm_test"] = "passed"
                        else:
                            logger.error(f"✗ vLLM inference failed: {resp.status}")
                            self.results["vllm_test"] = "failed"

        except Exception as e:
            logger.error(f"✗ vLLM test failed: {e}")
            self.results["vllm_test"] = "error"

    async def _validate_pipeline(self, qdrant_store: QdrantVectorStore):
        """Validate end-to-end query pipeline"""

        if self.dry_run:
            logger.info("(dry-run) Would validate query pipeline")
            return

        try:
            # Initialize embeddings
            embeddings = OllamaEmbeddings(
                model=self.config.embedding.model_name,
                base_url=self.config.ollama_host
            )

            # Test query
            test_query = "What are the uniform regulations?"
            logger.info(f"Testing query: '{test_query}'")

            # Generate embedding
            start = time.time()
            query_vector = embeddings.embed_query(test_query)
            embed_time = time.time() - start
            logger.info(f"  Embedding: {embed_time:.2f}s")

            # Search Qdrant
            start = time.time()
            results = await qdrant_store.search(
                query_vector=query_vector,
                top_k=5
            )
            search_time = time.time() - start
            logger.info(f"  Search: {search_time:.2f}s")
            logger.info(f"  Found {len(results)} results")

            if results:
                logger.info(f"  Top result score: {results[0].score:.3f}")
                logger.info(f"  Top result preview: {results[0].text[:100]}...")

            total_time = embed_time + search_time
            logger.info(f"✓ Pipeline test passed (total: {total_time:.2f}s)")

            self.results["pipeline_test"] = "passed"
            self.results["pipeline_latency"] = total_time

        except Exception as e:
            logger.error(f"✗ Pipeline validation failed: {e}")
            self.results["pipeline_test"] = "error"

    def _print_summary(self):
        """Print migration summary"""

        logger.info("\n" + "=" * 70)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 70)

        # Services
        logger.info("\nServices:")
        for service in ["Qdrant", "Redis", "vLLM"]:
            key = f"{service}_available"
            status = "✓" if self.results.get(key) else "✗"
            logger.info(f"  {status} {service}")

        # Migration
        if not self.dry_run:
            logger.info("\nMigration:")
            docs = self.results.get("documents_migrated", 0)
            time_taken = self.results.get("migration_time", 0)
            logger.info(f"  Documents migrated: {docs}")
            logger.info(f"  Time taken: {time_taken:.1f}s")

        # Tests
        logger.info("\nTests:")
        cache_test = self.results.get("cache_test", "not run")
        vllm_test = self.results.get("vllm_test", "not run")
        pipeline_test = self.results.get("pipeline_test", "not run")

        logger.info(f"  Cache: {cache_test}")
        logger.info(f"  vLLM: {vllm_test}")
        logger.info(f"  Pipeline: {pipeline_test}")

        # Performance
        if "pipeline_latency" in self.results:
            logger.info("\nPerformance:")
            logger.info(f"  Pipeline latency: {self.results['pipeline_latency']:.2f}s")

        # Next steps
        logger.info("\n" + "=" * 70)
        logger.info("NEXT STEPS")
        logger.info("=" * 70)
        logger.info("""
1. Update _src/app.py to use Qdrant instead of ChromaDB
2. Update _src/adaptive_retrieval.py to use vLLM
3. Enable embedding cache in production
4. Run full test suite: python tests/test_production.py
5. Deploy to production hardware
6. Monitor performance in Grafana (http://localhost:3001)
        """)


async def main():
    parser = argparse.ArgumentParser(description="Migrate to production infrastructure")
    parser.add_argument("--dry-run", action="store_true", help="Test without making changes")
    args = parser.parse_args()

    config = load_config()
    migrator = ProductionMigrator(config, dry_run=args.dry_run)

    try:
        await migrator.migrate()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
