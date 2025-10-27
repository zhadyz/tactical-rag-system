"""
Embedding Cache Layer (L4) - ATLAS Protocol Implementation

Mission: Reduce embedding latency by -98% through Redis-backed caching
Architecture: SHA-256 keyed deduplication with 7-day TTL
Performance Target: 60-70% cache hit rate, <1ms retrieval latency

Research Source: V3.5_AUGMENTATION_REPORT.md Section 4 (Caching Strategy)
Implementation Date: 2025-10-23
Lead: THE DIDACT (Research Specialist)
"""

import asyncio
import hashlib
import json
import logging
import pickle
from typing import List, Optional, Dict, Any, Union
from datetime import timedelta

import redis.asyncio as aioredis
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingCacheStats:
    """Statistics tracking for cache performance monitoring"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.total_latency_ms = 0.0
        self.cache_operations = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage"""
        total = self.hits + self.misses
        return (self.hits / total * 100.0) if total > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average cache operation latency"""
        return (self.total_latency_ms / self.cache_operations) if self.cache_operations > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Export statistics as dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(self.hit_rate, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 3),
            "total_operations": self.cache_operations
        }


class EmbeddingCache:
    """
    L4 Embedding Cache - Redis-backed with SHA-256 deduplication

    Performance Characteristics:
    - Cache hit: <1ms retrieval latency
    - Cache miss: 50-100ms embedding computation
    - Expected hit rate: 60-80% in production (source: waadi.ai)
    - Latency reduction: -98% for cached embeddings

    Architecture:
    - Key: SHA-256 hash of normalized text
    - Value: Pickled numpy array (embedding vector)
    - TTL: 7 days (configurable)
    - Async operations: aioredis for non-blocking I/O

    Integration Points:
    - Adaptive retrieval query embeddings
    - Document indexing batch embeddings
    - Reranking query expansions
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl: int = 86400 * 7,  # 7 days in seconds
        key_prefix: str = "emb:v1:",
        db: int = 0
    ):
        """
        Initialize Embedding Cache

        Args:
            redis_url: Redis connection URL (format: redis://host:port)
            ttl: Time-to-live for cached embeddings in seconds (default: 7 days)
            key_prefix: Prefix for cache keys to avoid collisions (default: "emb:v1:")
            db: Redis database number (default: 0)
        """
        self.redis_url = redis_url
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.db = db

        self.redis_client: Optional[aioredis.Redis] = None
        self.stats = EmbeddingCacheStats()

        logger.info(f"EmbeddingCache initialized: TTL={ttl}s, prefix={key_prefix}")

    async def connect(self):
        """Establish async Redis connection"""
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                db=self.db,
                decode_responses=False,  # We handle binary data (pickle)
                encoding="utf-8"
            )
            # Test connection
            await self.redis_client.ping()
            logger.info(f"✓ Redis connection established: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self):
        """Close Redis connection gracefully"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    def _generate_cache_key(self, text: str) -> str:
        """
        Generate deterministic cache key from text using SHA-256

        Normalization Strategy:
        - Strip whitespace
        - Lowercase (preserves semantic meaning for embeddings)
        - SHA-256 hash for fixed-length key (64 hex chars)

        Args:
            text: Input text to generate key from

        Returns:
            Cache key in format: {prefix}{sha256_hash}
        """
        # Normalize text
        normalized = text.strip().lower()

        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()

        return f"{self.key_prefix}{hash_hex}"

    async def get(self, text: str) -> Optional[np.ndarray]:
        """
        Retrieve cached embedding for text

        Args:
            text: Input text to lookup

        Returns:
            Cached embedding vector as numpy array, or None if not cached
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        import time
        start_time = time.perf_counter()

        try:
            cache_key = self._generate_cache_key(text)
            cached_data = await self.redis_client.get(cache_key)

            latency_ms = (time.perf_counter() - start_time) * 1000
            self.stats.total_latency_ms += latency_ms
            self.stats.cache_operations += 1

            if cached_data:
                self.stats.hits += 1
                embedding = pickle.loads(cached_data)
                logger.debug(f"Cache HIT: {cache_key[:16]}... ({latency_ms:.2f}ms)")
                return embedding
            else:
                self.stats.misses += 1
                logger.debug(f"Cache MISS: {cache_key[:16]}... ({latency_ms:.2f}ms)")
                return None

        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            self.stats.misses += 1
            return None

    async def set(self, text: str, embedding: np.ndarray) -> bool:
        """
        Store embedding in cache with TTL

        Args:
            text: Input text (used to generate cache key)
            embedding: Embedding vector to cache

        Returns:
            True if successfully cached, False otherwise
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            cache_key = self._generate_cache_key(text)
            serialized_data = pickle.dumps(embedding, protocol=pickle.HIGHEST_PROTOCOL)

            # Set with TTL
            await self.redis_client.setex(
                cache_key,
                self.ttl,
                serialized_data
            )

            logger.debug(f"Cache SET: {cache_key[:16]}... (size: {len(serialized_data)} bytes)")
            return True

        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False

    async def get_or_compute(
        self,
        text: str,
        compute_fn,
        *args,
        **kwargs
    ) -> np.ndarray:
        """
        Get embedding from cache, or compute and cache if missing

        This is the primary interface for embedding retrieval with automatic caching.

        Args:
            text: Input text to embed
            compute_fn: Callable that computes embedding (e.g., embeddings.embed_query)
            *args, **kwargs: Arguments to pass to compute_fn

        Returns:
            Embedding vector (from cache or freshly computed)

        Example:
            >>> embedding = await cache.get_or_compute(
            ...     "What is RAG?",
            ...     embeddings.embed_query
            ... )
        """
        # Try cache first
        cached = await self.get(text)
        if cached is not None:
            return cached

        # Cache miss - compute embedding
        if asyncio.iscoroutinefunction(compute_fn):
            embedding = await compute_fn(text, *args, **kwargs)
        else:
            # Run sync function in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(None, compute_fn, text, *args, **kwargs)

        # Convert to numpy array if needed
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding, dtype=np.float32)

        # Store in cache for future use
        await self.set(text, embedding)

        return embedding

    async def batch_get(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Retrieve multiple embeddings in batch (optimized with Redis pipeline)

        Args:
            texts: List of input texts

        Returns:
            List of embeddings (None for cache misses)
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        import time
        start_time = time.perf_counter()

        try:
            # Generate all cache keys
            cache_keys = [self._generate_cache_key(text) for text in texts]

            # Use pipeline for batch retrieval
            pipeline = self.redis_client.pipeline()
            for key in cache_keys:
                pipeline.get(key)

            cached_data_list = await pipeline.execute()

            latency_ms = (time.perf_counter() - start_time) * 1000
            self.stats.total_latency_ms += latency_ms
            self.stats.cache_operations += len(texts)

            # Deserialize results
            embeddings = []
            for cached_data in cached_data_list:
                if cached_data:
                    self.stats.hits += 1
                    embeddings.append(pickle.loads(cached_data))
                else:
                    self.stats.misses += 1
                    embeddings.append(None)

            hits = sum(1 for e in embeddings if e is not None)
            logger.debug(f"Batch cache retrieval: {hits}/{len(texts)} hits ({latency_ms:.2f}ms)")

            return embeddings

        except Exception as e:
            logger.error(f"Batch cache retrieval error: {e}")
            self.stats.misses += len(texts)
            return [None] * len(texts)

    async def batch_set(self, texts: List[str], embeddings: List[np.ndarray]) -> int:
        """
        Store multiple embeddings in batch (optimized with Redis pipeline)

        Args:
            texts: List of input texts
            embeddings: List of embedding vectors

        Returns:
            Number of successfully cached embeddings
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        if len(texts) != len(embeddings):
            raise ValueError("texts and embeddings must have same length")

        try:
            # Use pipeline for batch storage
            pipeline = self.redis_client.pipeline()

            for text, embedding in zip(texts, embeddings):
                cache_key = self._generate_cache_key(text)
                serialized_data = pickle.dumps(embedding, protocol=pickle.HIGHEST_PROTOCOL)
                pipeline.setex(cache_key, self.ttl, serialized_data)

            await pipeline.execute()

            logger.debug(f"Batch cache storage: {len(texts)} embeddings cached")
            return len(texts)

        except Exception as e:
            logger.error(f"Batch cache storage error: {e}")
            return 0

    async def invalidate(self, text: str) -> bool:
        """
        Manually invalidate cache entry for specific text

        Args:
            text: Text to invalidate cache for

        Returns:
            True if entry was deleted, False if not found
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            cache_key = self._generate_cache_key(text)
            result = await self.redis_client.delete(cache_key)

            if result > 0:
                logger.info(f"Cache invalidated: {cache_key[:16]}...")
                return True
            return False

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False

    async def clear_all(self) -> bool:
        """
        Clear all cached embeddings with matching key prefix

        WARNING: This is a destructive operation. Use with caution.

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            pattern = f"{self.key_prefix}*"
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    deleted_count += await self.redis_client.delete(*keys)

                if cursor == 0:
                    break

            logger.warning(f"Cache cleared: {deleted_count} entries deleted (prefix: {self.key_prefix})")

            # Reset statistics
            self.stats = EmbeddingCacheStats()

            return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics

        Returns:
            Dictionary with cache metrics
        """
        stats_dict = self.stats.to_dict()

        # Add cache size information
        if self.redis_client:
            try:
                info = await self.redis_client.info("memory")
                stats_dict["redis_memory_used_mb"] = round(
                    int(info.get("used_memory", 0)) / (1024 * 1024), 2
                )
            except Exception as e:
                logger.warning(f"Could not fetch Redis memory info: {e}")

        return stats_dict

    def __repr__(self) -> str:
        """String representation of cache instance"""
        return (
            f"EmbeddingCache("
            f"url={self.redis_url}, "
            f"ttl={self.ttl}s, "
            f"hit_rate={self.stats.hit_rate:.1f}%"
            f")"
        )


# Singleton instance for global access (optional)
_global_cache_instance: Optional[EmbeddingCache] = None


async def get_embedding_cache(
    redis_url: str = "redis://localhost:6379",
    ttl: int = 86400 * 7
) -> EmbeddingCache:
    """
    Get or create global embedding cache instance

    Args:
        redis_url: Redis connection URL
        ttl: Time-to-live in seconds

    Returns:
        Global EmbeddingCache instance
    """
    global _global_cache_instance

    if _global_cache_instance is None:
        _global_cache_instance = EmbeddingCache(redis_url=redis_url, ttl=ttl)
        await _global_cache_instance.connect()

    return _global_cache_instance
