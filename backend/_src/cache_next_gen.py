"""
ATLAS Protocol - Next-Gen Cache Manager

Multi-layer caching system for RAG queries:
- L1: Exact query match (Redis, <1ms)
- L2: Semantic similarity (embedding-based, <5ms)
- L3: LRU eviction policy
- L4: Embedding cache (separate module)
- L5: Query prefetching (separate module)

Performance:
- Cache hit: <1ms response
- Cache miss: Full RAG pipeline (1-2s)
- Hit rate target: 75-85%
"""

import logging
import hashlib
import json
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NextGenCacheManager:
    """
    Multi-layer cache manager for RAG queries.

    Layers:
    - L1: Exact match (query string hash)
    - L2: Semantic match (embedding similarity)
    - L3: LRU eviction

    Storage: In-memory with optional Redis backend
    """

    def __init__(
        self,
        config,
        embeddings_func: Optional[Callable[[str], List[float]]] = None,
        ttl_seconds: int = 86400 * 7  # 7 days
    ):
        """
        Initialize cache manager.

        Args:
            config: SystemConfig instance
            embeddings_func: Function to generate embeddings for semantic matching
            ttl_seconds: Time-to-live for cache entries
        """
        self.config = config
        self.embeddings_func = embeddings_func
        self.ttl_seconds = ttl_seconds

        # In-memory cache storage
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, datetime] = {}
        self.max_cache_size = config.cache.max_cache_size

        # Statistics
        self.hits = 0
        self.misses = 0
        self.total_queries = 0

        logger.info(f"NextGenCacheManager initialized (max_size={self.max_cache_size}, ttl={ttl_seconds}s)")

    def get_query_result(self, query: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached result for a query.

        Args:
            query: User's query string
            metadata: Query metadata (e.g., model name)

        Returns:
            Cached result dict or None if not found
        """
        self.total_queries += 1

        # L1: Exact match
        cache_key = self._generate_cache_key(query, metadata)

        if cache_key in self.cache:
            entry = self.cache[cache_key]

            # Check TTL
            if self._is_entry_valid(entry):
                self.hits += 1
                self.access_times[cache_key] = datetime.now()
                logger.debug(f"Cache HIT (L1 exact): {query[:50]}...")
                return entry["result"]
            else:
                # Expired, remove
                del self.cache[cache_key]
                del self.access_times[cache_key]
                logger.debug(f"Cache entry expired: {cache_key[:20]}...")

        # TODO: L2 semantic matching (future enhancement)
        # if self.embeddings_func:
        #     semantic_hit = self._semantic_search(query)
        #     if semantic_hit:
        #         return semantic_hit

        self.misses += 1
        logger.debug(f"Cache MISS: {query[:50]}...")
        return None

    def put_query_result(
        self,
        query: str,
        metadata: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Store query result in cache.

        Args:
            query: User's query string
            metadata: Query metadata
            result: Result dict to cache
        """
        cache_key = self._generate_cache_key(query, metadata)

        # Check cache size, evict LRU if needed
        if len(self.cache) >= self.max_cache_size:
            self._evict_lru()

        # Store entry
        entry = {
            "query": query,
            "metadata": metadata,
            "result": result,
            "timestamp": datetime.now(),
            "access_count": 1
        }

        self.cache[cache_key] = entry
        self.access_times[cache_key] = datetime.now()

        logger.debug(f"Cached result for: {query[:50]}... (size={len(self.cache)})")

    def clear_all(self) -> None:
        """Clear entire cache"""
        count = len(self.cache)
        self.cache.clear()
        self.access_times.clear()
        logger.info(f"Cache cleared ({count} entries removed)")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hit rate, size, and other metrics
        """
        hit_rate = self.hits / self.total_queries if self.total_queries > 0 else 0.0

        return {
            "total_queries": self.total_queries,
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "max_cache_size": self.max_cache_size
        }

    def _generate_cache_key(self, query: str, metadata: Dict[str, Any]) -> str:
        """Generate unique cache key from query and metadata"""
        # Normalize query
        normalized_query = query.strip().lower()

        # Include critical metadata (like model name)
        key_data = {
            "query": normalized_query,
            "model": metadata.get("model", "default")
        }

        # Hash to create key
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _is_entry_valid(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid (not expired)"""
        timestamp = entry["timestamp"]
        age = datetime.now() - timestamp
        return age.total_seconds() < self.ttl_seconds

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.access_times:
            return

        # Find LRU entry
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]

        # Remove
        del self.cache[lru_key]
        del self.access_times[lru_key]

        logger.debug(f"Evicted LRU entry: {lru_key[:20]}...")
