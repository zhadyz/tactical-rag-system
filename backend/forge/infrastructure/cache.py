"""
Forge - Multi-Layer Cache Manager

Merged from _src/embedding_cache.py + _src/cache_next_gen.py into a unified
four-layer cache:

  L1: Exact query -> full response  (Redis, SHA-256 key, 7-day TTL)
  L2: Semantic similarity cache     (embedding sim > 0.95)
  L3: Embedding cache               (Redis, for BGE-M3 vectors)
  L4: Proposition retrieval cache   (Redis, keyed by proposition text)
"""

import logging
import hashlib
import json
import pickle
import time
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

import numpy as np
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class CacheStats:
    """Tracks hit/miss statistics across all layers."""

    def __init__(self):
        self.l1_hits = 0
        self.l1_misses = 0
        self.l2_hits = 0
        self.l2_misses = 0
        self.l3_hits = 0
        self.l3_misses = 0
        self.l4_hits = 0
        self.l4_misses = 0
        self.total_latency_ms = 0.0
        self.operations = 0

    def to_dict(self) -> Dict[str, Any]:
        total = self.l1_hits + self.l1_misses
        hit_rate = (self.l1_hits / total * 100) if total else 0.0
        return {
            "l1_hits": self.l1_hits,
            "l1_misses": self.l1_misses,
            "l2_hits": self.l2_hits,
            "l3_hits": self.l3_hits,
            "l4_hits": self.l4_hits,
            "overall_hit_rate": round(hit_rate, 2),
            "avg_latency_ms": round(
                self.total_latency_ms / self.operations, 3
            ) if self.operations else 0.0,
        }


class ForgeCache:
    """
    Unified multi-layer cache backed by Redis.

    L1 — exact query match (full response)
    L2 — semantic similarity (placeholder; needs embeddings_func)
    L3 — embedding vectors (pickle)
    L4 — proposition retrieval results
    """

    # Key prefixes
    L1_PREFIX = "forge:l1:"
    L2_PREFIX = "forge:l2:"
    L3_PREFIX = "forge:l3:"
    L4_PREFIX = "forge:l4:"

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        ttl: int = 86400 * 7,
        semantic_threshold: float = 0.95,
    ):
        self.redis_url = f"redis://{redis_host}:{redis_port}"
        self.redis_db = redis_db
        self.redis_password = redis_password
        self.ttl = ttl
        self.semantic_threshold = semantic_threshold

        self.client: Optional[aioredis.Redis] = None
        self.stats = CacheStats()

    async def connect(self):
        self.client = await aioredis.from_url(
            self.redis_url,
            db=self.redis_db,
            password=self.redis_password,
            decode_responses=False,
        )
        await self.client.ping()
        logger.info(f"ForgeCache connected: {self.redis_url}")

    async def close(self):
        if self.client:
            await self.client.close()

    # ------------------------------------------------------------------
    # L1: Exact query -> full response
    # ------------------------------------------------------------------

    @staticmethod
    def _l1_key(query: str) -> str:
        normalized = query.strip().lower()
        h = hashlib.sha256(normalized.encode()).hexdigest()
        return f"{ForgeCache.L1_PREFIX}{h}"

    async def l1_get(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached query response."""
        if not self.client:
            return None
        start = time.perf_counter()
        try:
            data = await self.client.get(self._l1_key(query))
            latency = (time.perf_counter() - start) * 1000
            self.stats.total_latency_ms += latency
            self.stats.operations += 1
            if data:
                self.stats.l1_hits += 1
                return json.loads(data)
            self.stats.l1_misses += 1
            return None
        except Exception as e:
            logger.warning(f"L1 get error: {e}")
            self.stats.l1_misses += 1
            return None

    async def l1_set(self, query: str, result: Dict[str, Any]) -> bool:
        if not self.client:
            return False
        try:
            await self.client.setex(
                self._l1_key(query), self.ttl, json.dumps(result),
            )
            return True
        except Exception as e:
            logger.warning(f"L1 set error: {e}")
            return False

    # ------------------------------------------------------------------
    # L3: Embedding cache (pickle)
    # ------------------------------------------------------------------

    @staticmethod
    def _l3_key(text: str) -> str:
        normalized = text.strip().lower()
        h = hashlib.sha256(normalized.encode()).hexdigest()
        return f"{ForgeCache.L3_PREFIX}{h}"

    async def l3_get(self, text: str) -> Optional[np.ndarray]:
        if not self.client:
            return None
        try:
            data = await self.client.get(self._l3_key(text))
            if data:
                self.stats.l3_hits += 1
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.warning(f"L3 get error: {e}")
            return None

    async def l3_set(self, text: str, embedding: np.ndarray) -> bool:
        if not self.client:
            return False
        try:
            await self.client.setex(
                self._l3_key(text), self.ttl,
                pickle.dumps(embedding, protocol=pickle.HIGHEST_PROTOCOL),
            )
            return True
        except Exception as e:
            logger.warning(f"L3 set error: {e}")
            return False

    async def l3_get_or_compute(
        self, text: str, compute_fn: Callable, *args, **kwargs,
    ) -> np.ndarray:
        """Get embedding from cache, or compute + cache."""
        cached = await self.l3_get(text)
        if cached is not None:
            return cached

        import asyncio
        if asyncio.iscoroutinefunction(compute_fn):
            result = await compute_fn(text, *args, **kwargs)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, compute_fn, text, *args)

        if not isinstance(result, np.ndarray):
            result = np.array(result, dtype=np.float32)
        await self.l3_set(text, result)
        return result

    async def l3_batch_get(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        if not self.client:
            return [None] * len(texts)
        try:
            pipe = self.client.pipeline()
            for t in texts:
                pipe.get(self._l3_key(t))
            raw = await pipe.execute()
            results = []
            for data in raw:
                if data:
                    self.stats.l3_hits += 1
                    results.append(pickle.loads(data))
                else:
                    results.append(None)
            return results
        except Exception as e:
            logger.warning(f"L3 batch get error: {e}")
            return [None] * len(texts)

    async def l3_batch_set(self, texts: List[str], embeddings: List[np.ndarray]) -> int:
        if not self.client:
            return 0
        try:
            pipe = self.client.pipeline()
            for t, emb in zip(texts, embeddings):
                pipe.setex(
                    self._l3_key(t), self.ttl,
                    pickle.dumps(emb, protocol=pickle.HIGHEST_PROTOCOL),
                )
            await pipe.execute()
            return len(texts)
        except Exception as e:
            logger.warning(f"L3 batch set error: {e}")
            return 0

    # ------------------------------------------------------------------
    # L4: Proposition retrieval cache
    # ------------------------------------------------------------------

    @staticmethod
    def _l4_key(text: str) -> str:
        h = hashlib.sha256(text.strip().lower().encode()).hexdigest()
        return f"{ForgeCache.L4_PREFIX}{h}"

    async def l4_get(self, text: str) -> Optional[List[Dict[str, Any]]]:
        if not self.client:
            return None
        try:
            data = await self.client.get(self._l4_key(text))
            if data:
                self.stats.l4_hits += 1
                return json.loads(data)
            return None
        except Exception:
            return None

    async def l4_set(self, text: str, results: List[Dict[str, Any]]) -> bool:
        if not self.client:
            return False
        try:
            await self.client.setex(
                self._l4_key(text), self.ttl, json.dumps(results),
            )
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    async def invalidate_query(self, query: str) -> bool:
        if not self.client:
            return False
        try:
            deleted = await self.client.delete(self._l1_key(query))
            return deleted > 0
        except Exception:
            return False

    async def clear_all(self) -> int:
        """Clear all Forge cache entries."""
        if not self.client:
            return 0
        total = 0
        for prefix in (self.L1_PREFIX, self.L2_PREFIX, self.L3_PREFIX, self.L4_PREFIX):
            cursor = 0
            while True:
                cursor, keys = await self.client.scan(cursor=cursor, match=f"{prefix}*", count=200)
                if keys:
                    total += await self.client.delete(*keys)
                if cursor == 0:
                    break
        self.stats = CacheStats()
        logger.info(f"ForgeCache cleared: {total} keys deleted")
        return total

    async def get_stats(self) -> Dict[str, Any]:
        stats = self.stats.to_dict()
        if self.client:
            try:
                info = await self.client.info("memory")
                stats["redis_memory_mb"] = round(
                    int(info.get("used_memory", 0)) / (1024 * 1024), 2,
                )
            except Exception:
                pass
        return stats
