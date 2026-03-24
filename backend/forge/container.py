"""
Forge - Service Container (Dependency Injection)

Lazy-initialized container replacing global mutable variables.
Parallel initialization in 3 groups matching the current rag_engine.py pattern.
"""

import logging
import asyncio
from typing import Optional, Any

from forge.config import ForgeConfig

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Lazy-initialized service container.

    Services are created on first access (or during initialize() for eager startup).
    Lifecycle: initialize() at app startup, shutdown() at app teardown.
    """

    def __init__(self, config: ForgeConfig):
        self.config = config
        self._services: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Getters (lazy)
    # ------------------------------------------------------------------

    async def get_embeddings(self):
        if "embeddings" not in self._services:
            from forge.infrastructure.embeddings import BGEM3Service
            svc = BGEM3Service(
                model_name=self.config.bge_m3.model_name,
                device=self.config.bge_m3.device,
                batch_size=self.config.bge_m3.batch_size,
                max_length=self.config.bge_m3.max_length,
                normalize=self.config.bge_m3.normalize_embeddings,
            )
            await svc.initialize()
            self._services["embeddings"] = svc
        return self._services["embeddings"]

    async def get_vectorstore(self):
        if "vectorstore" not in self._services:
            from forge.infrastructure.vectorstore import ForgeVectorStore
            store = ForgeVectorStore(
                collection_name=self.config.collection_name,
                dense_dim=self.config.bge_m3.dimension,
            )
            await store.initialize()
            self._services["vectorstore"] = store
        return self._services["vectorstore"]

    async def get_llm(self):
        if "llm" not in self._services:
            from forge.infrastructure.llm import create_llm
            llm = create_llm(self.config)
            self._services["llm"] = llm
        return self._services["llm"]

    async def get_cache(self):
        if "cache" not in self._services:
            from forge.infrastructure.cache import ForgeCache
            cache = ForgeCache(
                redis_host=self.config.cache.redis_host,
                redis_port=self.config.cache.redis_port,
                redis_db=self.config.cache.redis_db,
                redis_password=self.config.cache.redis_password,
                ttl=self.config.cache.ttl,
            )
            await cache.connect()
            self._services["cache"] = cache
        return self._services["cache"]

    async def get_memory(self):
        if "memory" not in self._services:
            from forge.infrastructure.memory import ConversationMemory
            llm = await self.get_llm()
            mem = ConversationMemory(llm=llm)
            self._services["memory"] = mem
        return self._services["memory"]

    async def get_model_manager(self):
        if "model_manager" not in self._services:
            from forge.infrastructure.models import ModelManager
            mgr = ModelManager(self.config)
            self._services["model_manager"] = mgr
        return self._services["model_manager"]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """
        Eagerly initialize all services in 3 parallel groups.

        Group 1: Cache + Embeddings (no deps)
        Group 2: VectorStore + LLM (no deps between them)
        Group 3: Memory + ModelManager (depend on LLM)
        """
        logger.info("ServiceContainer: initializing (3 groups)...")

        # Group 1
        logger.info("  Group 1: cache + embeddings")
        g1 = await asyncio.gather(
            self.get_cache(),
            self.get_embeddings(),
            return_exceptions=True,
        )
        for r in g1:
            if isinstance(r, Exception):
                logger.error(f"  Group 1 error: {r}")

        # Group 2
        logger.info("  Group 2: vectorstore + llm")
        g2 = await asyncio.gather(
            self.get_vectorstore(),
            self.get_llm(),
            return_exceptions=True,
        )
        for r in g2:
            if isinstance(r, Exception):
                logger.error(f"  Group 2 error: {r}")

        # Group 3
        logger.info("  Group 3: memory + model_manager")
        g3 = await asyncio.gather(
            self.get_memory(),
            self.get_model_manager(),
            return_exceptions=True,
        )
        for r in g3:
            if isinstance(r, Exception):
                logger.error(f"  Group 3 error: {r}")

        logger.info("ServiceContainer: initialization complete")

    async def shutdown(self) -> None:
        """Cleanup all services."""
        logger.info("ServiceContainer: shutting down...")

        cache = self._services.get("cache")
        if cache and hasattr(cache, "close"):
            await cache.close()

        vectorstore = self._services.get("vectorstore")
        if vectorstore and hasattr(vectorstore, "close"):
            await vectorstore.close()

        self._services.clear()
        logger.info("ServiceContainer: shutdown complete")
