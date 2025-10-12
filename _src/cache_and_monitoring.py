"""
Enterprise RAG System - Caching and Monitoring Infrastructure
Multi-layer caching, metrics collection, and performance monitoring
"""

import time
import hashlib
import logging
from typing import Any, Optional, Dict, List, Callable
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import json
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

# Optional Redis support
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - using in-memory cache only")


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class LRUCache:
    """Thread-safe LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.stats = CacheStats()
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        
        with self.lock:
            if key not in self.cache:
                self.stats.misses += 1
                return None
            
            # Check TTL
            if self._is_expired(key):
                self._remove(key)
                self.stats.misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.stats.hits += 1
            return self.cache[key]
    
    def put(self, key: str, value: Any) -> None:
        """Put value into cache"""
        
        with self.lock:
            # Update existing
            if key in self.cache:
                self.cache.move_to_end(key)
                self.cache[key] = value
                self.timestamps[key] = time.time()
                return
            
            # Evict if necessary
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            # Add new
            self.cache[key] = value
            self.timestamps[key] = time.time()
            self.stats.total_size = len(self.cache)
    
    def clear(self) -> None:
        """Clear entire cache"""
        
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.stats.total_size = 0
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        
        if key not in self.timestamps:
            return True
        
        age = time.time() - self.timestamps[key]
        return age > self.ttl
    
    def _remove(self, key: str) -> None:
        """Remove key from cache"""
        
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
            self.stats.total_size = len(self.cache)
    
    def _evict_oldest(self) -> None:
        """Evict oldest entry"""
        
        if self.cache:
            oldest_key = next(iter(self.cache))
            self._remove(oldest_key)
            self.stats.evictions += 1
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        
        with self.lock:
            return {
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "evictions": self.stats.evictions,
                "size": self.stats.total_size,
                "hit_rate": self.stats.hit_rate,
                "max_size": self.max_size
            }


class RedisEmbeddingCache:
    """Redis-backed embedding cache with automatic serialization"""

    def __init__(self, redis_client, ttl: int = 3600, prefix: str = "emb:"):
        self.redis = redis_client
        self.ttl = ttl
        self.prefix = prefix
        self.stats = CacheStats()
        self.lock = threading.RLock()

        logger.info(f"Redis embedding cache initialized (TTL: {ttl}s)")

    def get(self, text: str) -> Optional[List[float]]:
        """Get embedding from Redis"""

        try:
            key = self.prefix + hashlib.md5(text.encode()).hexdigest()

            value = self.redis.get(key)

            if value is None:
                with self.lock:
                    self.stats.misses += 1
                return None

            # Deserialize numpy array
            embedding = np.frombuffer(value, dtype=np.float32).tolist()

            with self.lock:
                self.stats.hits += 1

            return embedding

        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
            with self.lock:
                self.stats.misses += 1
            return None

    def put(self, text: str, embedding: List[float]) -> None:
        """Store embedding in Redis"""

        try:
            key = self.prefix + hashlib.md5(text.encode()).hexdigest()

            # Serialize as numpy array for efficiency
            value = np.array(embedding, dtype=np.float32).tobytes()

            self.redis.setex(key, self.ttl, value)

            with self.lock:
                self.stats.total_size += 1

        except Exception as e:
            logger.warning(f"Redis put failed: {e}")

    def clear(self) -> None:
        """Clear all embeddings with this prefix"""

        try:
            pattern = self.prefix + "*"
            cursor = 0

            while True:
                cursor, keys = self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    self.redis.delete(*keys)
                if cursor == 0:
                    break

            with self.lock:
                self.stats.total_size = 0

            logger.info("Redis embedding cache cleared")

        except Exception as e:
            logger.warning(f"Redis clear failed: {e}")

    def get_stats(self) -> Dict:
        """Get cache statistics"""

        with self.lock:
            return {
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "size": self.stats.total_size,
                "hit_rate": self.stats.hit_rate,
                "backend": "redis"
            }


class RedisSemanticCache:
    """
    Redis-backed semantic cache for query results
    Uses embedding similarity to match semantically similar queries
    """

    def __init__(
        self,
        redis_client,
        embeddings_func: Callable,
        ttl: int = 3600,
        similarity_threshold: float = 0.95,
        prefix: str = "semantic:"
    ):
        self.redis = redis_client
        self.embeddings_func = embeddings_func
        self.ttl = ttl
        self.similarity_threshold = similarity_threshold
        self.prefix = prefix
        self.stats = CacheStats()
        self.lock = threading.RLock()

        logger.info(f"Redis semantic cache initialized (similarity: {similarity_threshold})")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""

        a = np.array(vec1)
        b = np.array(vec2)

        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def get(self, query: str) -> Optional[Any]:
        """Get cached result for semantically similar query"""

        try:
            # Get query embedding
            query_embedding = self.embeddings_func(query)

            # Search for similar cached queries
            pattern = self.prefix + "*"
            cursor = 0
            best_match = None
            best_similarity = 0.0

            while True:
                cursor, keys = self.redis.scan(cursor, match=pattern, count=100)

                for key in keys:
                    # Get cached embedding and result
                    data = self.redis.get(key)

                    if data is None:
                        continue

                    cache_entry = json.loads(data)
                    cached_embedding = cache_entry.get("embedding")

                    if not cached_embedding:
                        continue

                    # Calculate similarity
                    similarity = self._cosine_similarity(query_embedding, cached_embedding)

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = cache_entry.get("result")

                if cursor == 0:
                    break

            # Return if similarity above threshold
            if best_similarity >= self.similarity_threshold and best_match:
                with self.lock:
                    self.stats.hits += 1
                logger.info(f"Semantic cache hit (similarity: {best_similarity:.3f})")
                return best_match

            with self.lock:
                self.stats.misses += 1
            return None

        except Exception as e:
            logger.warning(f"Redis semantic cache get failed: {e}")
            with self.lock:
                self.stats.misses += 1
            return None

    def put(self, query: str, result: Any) -> None:
        """Cache query result with embedding"""

        try:
            # Get query embedding
            query_embedding = self.embeddings_func(query)

            # Create cache entry
            cache_entry = {
                "query": query,
                "embedding": query_embedding,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

            # Store with query hash as key
            key = self.prefix + hashlib.md5(query.encode()).hexdigest()
            value = json.dumps(cache_entry)

            self.redis.setex(key, self.ttl, value)

            with self.lock:
                self.stats.total_size += 1

        except Exception as e:
            logger.warning(f"Redis semantic cache put failed: {e}")

    def clear(self) -> None:
        """Clear all semantic cache entries"""

        try:
            pattern = self.prefix + "*"
            cursor = 0

            while True:
                cursor, keys = self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    self.redis.delete(*keys)
                if cursor == 0:
                    break

            with self.lock:
                self.stats.total_size = 0

            logger.info("Redis semantic cache cleared")

        except Exception as e:
            logger.warning(f"Redis semantic cache clear failed: {e}")

    def get_stats(self) -> Dict:
        """Get cache statistics"""

        with self.lock:
            return {
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "size": self.stats.total_size,
                "hit_rate": self.stats.hit_rate,
                "similarity_threshold": self.similarity_threshold,
                "backend": "redis"
            }


class CacheManager:
    """Multi-layer cache manager with optional Redis support"""

    def __init__(self, config, embeddings_func: Optional[Callable] = None):
        self.config = config
        self.embeddings_func = embeddings_func
        self.redis_client = None
        self.redis_embedding_cache = None
        self.redis_semantic_cache = None

        # Try to connect to Redis if enabled
        if config.cache.use_redis and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=config.cache.redis_host,
                    port=config.cache.redis_port,
                    db=config.cache.redis_db,
                    decode_responses=False,  # Binary for embeddings
                    socket_connect_timeout=2,
                    socket_timeout=2
                )

                # Test connection
                self.redis_client.ping()

                logger.info(f"Redis connected: {config.cache.redis_host}:{config.cache.redis_port}")

                # Initialize Redis caches
                if config.cache.enable_embedding_cache:
                    self.redis_embedding_cache = RedisEmbeddingCache(
                        self.redis_client,
                        ttl=config.cache.cache_ttl
                    )

                if config.cache.enable_query_cache and embeddings_func:
                    self.redis_semantic_cache = RedisSemanticCache(
                        self.redis_client,
                        embeddings_func,
                        ttl=config.cache.cache_ttl,
                        similarity_threshold=0.95
                    )

            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Falling back to in-memory cache")
                self.redis_client = None

        # Initialize local caches (always available as fallback)
        self.embedding_cache = LRUCache(
            max_size=config.cache.max_cache_size,
            ttl=config.cache.cache_ttl
        ) if config.cache.enable_embedding_cache else None

        self.query_cache = LRUCache(
            max_size=config.cache.max_cache_size // 10,
            ttl=config.cache.cache_ttl
        ) if config.cache.enable_query_cache else None

        self.result_cache = LRUCache(
            max_size=config.cache.max_cache_size // 5,
            ttl=config.cache.cache_ttl
        ) if config.cache.enable_result_cache else None

        cache_type = "Redis" if self.redis_client else "In-Memory"
        logger.info(f"Cache manager initialized ({cache_type})")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding (Redis first, then local)"""

        # Try Redis first if available
        if self.redis_embedding_cache:
            result = self.redis_embedding_cache.get(text)
            if result is not None:
                return result

        # Fall back to local cache
        if not self.embedding_cache:
            return None

        cache_key = self._hash_text(text)
        return self.embedding_cache.get(cache_key)

    def put_embedding(self, text: str, embedding: List[float]) -> None:
        """Cache embedding (both Redis and local)"""

        # Store in Redis if available
        if self.redis_embedding_cache:
            self.redis_embedding_cache.put(text, embedding)

        # Store in local cache
        if not self.embedding_cache:
            return

        cache_key = self._hash_text(text)
        self.embedding_cache.put(cache_key, embedding)
    
    def get_query_result(self, query: str, params: Dict) -> Optional[Any]:
        """Get cached query result (semantic cache first, then local)"""

        # Try Redis semantic cache first if available
        if self.redis_semantic_cache:
            result = self.redis_semantic_cache.get(query)
            if result is not None:
                return result

        # Fall back to local cache (exact match only)
        if not self.query_cache:
            return None

        cache_key = self._hash_query(query, params)
        return self.query_cache.get(cache_key)

    def put_query_result(self, query: str, params: Dict, result: Any) -> None:
        """Cache query result (both semantic and local)"""

        # Store in Redis semantic cache if available
        if self.redis_semantic_cache:
            self.redis_semantic_cache.put(query, result)

        # Store in local cache
        if not self.query_cache:
            return

        cache_key = self._hash_query(query, params)
        self.query_cache.put(cache_key, result)
    
    def get_retrieval_result(self, query: str) -> Optional[Any]:
        """Get cached retrieval result"""
        
        if not self.result_cache:
            return None
        
        cache_key = self._hash_text(query)
        return self.result_cache.get(cache_key)
    
    def put_retrieval_result(self, query: str, result: Any) -> None:
        """Cache retrieval result"""
        
        if not self.result_cache:
            return
        
        cache_key = self._hash_text(query)
        self.result_cache.put(cache_key, result)
    
    def clear_all(self) -> None:
        """Clear all caches (both Redis and local)"""

        # Clear Redis caches
        if self.redis_embedding_cache:
            self.redis_embedding_cache.clear()
        if self.redis_semantic_cache:
            self.redis_semantic_cache.clear()

        # Clear local caches
        if self.embedding_cache:
            self.embedding_cache.clear()
        if self.query_cache:
            self.query_cache.clear()
        if self.result_cache:
            self.result_cache.clear()

        logger.info("All caches cleared (Redis + local)")
    
    def get_stats(self) -> Dict:
        """Get statistics for all caches (Redis + local)"""

        stats = {}

        # Redis cache stats
        if self.redis_embedding_cache:
            stats["redis_embedding_cache"] = self.redis_embedding_cache.get_stats()

        if self.redis_semantic_cache:
            stats["redis_semantic_cache"] = self.redis_semantic_cache.get_stats()

        # Local cache stats
        if self.embedding_cache:
            stats["local_embedding_cache"] = self.embedding_cache.get_stats()

        if self.query_cache:
            stats["local_query_cache"] = self.query_cache.get_stats()

        if self.result_cache:
            stats["result_cache"] = self.result_cache.get_stats()

        return stats
    
    def _hash_text(self, text: str) -> str:
        """Hash text for cache key"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _hash_query(self, query: str, params: Dict) -> str:
        """Hash query with parameters"""
        combined = f"{query}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(combined.encode()).hexdigest()


@dataclass
class Metric:
    """Performance metric"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collect and aggregate performance metrics"""
    
    def __init__(self, config):
        self.config = config
        self.metrics: List[Metric] = []
        self.counters: Dict[str, int] = {}
        self.timers: Dict[str, List[float]] = {}
        self.lock = threading.RLock()
        
        # Aggregated stats
        self.query_count = 0
        self.total_latency = 0.0
        self.error_count = 0
        
        logger.info("Metrics collector initialized")
    
    def record_query(self, latency: float, success: bool = True) -> None:
        """Record query metrics"""
        
        with self.lock:
            self.query_count += 1
            self.total_latency += latency
            
            if not success:
                self.error_count += 1
            
            self.metrics.append(Metric(
                name="query_latency",
                value=latency,
                timestamp=datetime.now(),
                labels={"success": str(success)}
            ))
    
    def record_retrieval(
        self,
        stage: str,
        latency: float,
        num_docs: int
    ) -> None:
        """Record retrieval metrics"""
        
        with self.lock:
            self.metrics.append(Metric(
                name=f"retrieval_{stage}_latency",
                value=latency,
                timestamp=datetime.now(),
                labels={"num_docs": str(num_docs)}
            ))
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment counter"""
        
        with self.lock:
            self.counters[name] = self.counters.get(name, 0) + value
    
    def record_timer(self, name: str, value: float) -> None:
        """Record timer value"""
        
        with self.lock:
            if name not in self.timers:
                self.timers[name] = []
            self.timers[name].append(value)
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        
        with self.lock:
            avg_latency = (
                self.total_latency / self.query_count
                if self.query_count > 0 else 0
            )
            
            error_rate = (
                self.error_count / self.query_count
                if self.query_count > 0 else 0
            )
            
            # Timer statistics
            timer_stats = {}
            for name, values in self.timers.items():
                if values:
                    timer_stats[name] = {
                        "count": len(values),
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "p50": self._percentile(values, 50),
                        "p95": self._percentile(values, 95),
                        "p99": self._percentile(values, 99)
                    }
            
            return {
                "query_count": self.query_count,
                "avg_latency": avg_latency,
                "error_count": self.error_count,
                "error_rate": error_rate,
                "counters": dict(self.counters),
                "timers": timer_stats
            }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def reset(self) -> None:
        """Reset all metrics"""
        
        with self.lock:
            self.metrics.clear()
            self.counters.clear()
            self.timers.clear()
            self.query_count = 0
            self.total_latency = 0.0
            self.error_count = 0


class PerformanceMonitor:
    """Complete performance monitoring system"""
    
    def __init__(self, config, cache_manager: CacheManager):
        self.config = config
        self.cache_manager = cache_manager
        self.metrics = MetricsCollector(config)
        self.start_time = time.time()
        
        logger.info("Performance monitor initialized")
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "metrics": self.metrics.get_summary(),
            "cache": self.cache_manager.get_stats(),
            "timestamp": datetime.now().isoformat()
        }
    
    def log_stats(self) -> None:
        """Log current statistics"""
        
        stats = self.get_system_stats()
        
        logger.info("=" * 60)
        logger.info("SYSTEM STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Uptime: {stats['uptime_formatted']}")
        logger.info(f"Total Queries: {stats['metrics']['query_count']}")
        logger.info(f"Avg Latency: {stats['metrics']['avg_latency']:.3f}s")
        logger.info(f"Error Rate: {stats['metrics']['error_rate']:.2%}")
        
        # Cache stats
        for cache_name, cache_stats in stats['cache'].items():
            logger.info(f"\n{cache_name}:")
            logger.info(f"  Hit Rate: {cache_stats['hit_rate']:.2%}")
            logger.info(f"  Size: {cache_stats['size']}/{cache_stats['max_size']}")
        
        logger.info("=" * 60)
    
    def save_stats(self, output_file: Path) -> None:
        """Save statistics to file"""
        
        stats = self.get_system_stats()
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Stats saved to {output_file}")


class Timer:
    """Context manager for timing operations"""

    def __init__(self, metrics: MetricsCollector, name: str):
        self.metrics = metrics
        self.name = name
        self.start_time = None
        self.elapsed = 0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        self.metrics.record_timer(self.name, self.elapsed)
        return False


@dataclass
class ProfileData:
    """Single query profile data"""
    query: str
    query_type: str
    strategy_used: str
    timings: Dict[str, float]
    success: bool
    timestamp: str
    error: Optional[str] = None


class PerformanceProfiler:
    """
    Comprehensive performance profiler for RAG pipeline
    Tracks timing for each stage: embedding, search, rerank, LLM
    """

    def __init__(self, output_dir: Path = Path("logs")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

        self.profiles: List[ProfileData] = []
        self.current_profile: Dict[str, Any] = {}
        self.lock = threading.RLock()

        logger.info("Performance profiler initialized")

    def start_profile(self, query: str) -> None:
        """Start profiling a new query"""

        with self.lock:
            self.current_profile = {
                "query": query,
                "query_type": None,
                "strategy_used": None,
                "timings": {},
                "success": False,
                "start_time": time.time(),
                "timestamp": datetime.now().isoformat(),
                "error": None
            }

    def record_stage(self, stage: str, duration_ms: float) -> None:
        """Record timing for a specific stage"""

        with self.lock:
            if self.current_profile:
                self.current_profile["timings"][stage] = duration_ms

    def set_metadata(self, query_type: str = None, strategy_used: str = None) -> None:
        """Set query metadata"""

        with self.lock:
            if self.current_profile:
                if query_type:
                    self.current_profile["query_type"] = query_type
                if strategy_used:
                    self.current_profile["strategy_used"] = strategy_used

    def complete_profile(self, success: bool = True, error: str = None) -> None:
        """Complete current profile"""

        with self.lock:
            if not self.current_profile:
                return

            self.current_profile["success"] = success
            self.current_profile["error"] = error

            # Calculate total time
            total_time = (time.time() - self.current_profile["start_time"]) * 1000
            self.current_profile["timings"]["total_ms"] = total_time

            # Remove start_time (not JSON serializable context)
            self.current_profile.pop("start_time", None)

            # Create ProfileData
            profile = ProfileData(
                query=self.current_profile["query"],
                query_type=self.current_profile.get("query_type", "unknown"),
                strategy_used=self.current_profile.get("strategy_used", "unknown"),
                timings=self.current_profile["timings"],
                success=success,
                timestamp=self.current_profile["timestamp"],
                error=error
            )

            self.profiles.append(profile)
            self.current_profile = {}

    def get_summary(self) -> Dict:
        """Get profiling summary statistics"""

        with self.lock:
            if not self.profiles:
                return {
                    "total_queries": 0,
                    "successful_queries": 0,
                    "failed_queries": 0,
                    "average_times": {}
                }

            successful = [p for p in self.profiles if p.success]

            if not successful:
                return {
                    "total_queries": len(self.profiles),
                    "successful_queries": 0,
                    "failed_queries": len(self.profiles),
                    "average_times": {}
                }

            # Calculate averages
            avg_timings = {}

            # Get all timing keys
            all_keys = set()
            for profile in successful:
                all_keys.update(profile.timings.keys())

            # Calculate average for each key
            for key in all_keys:
                values = [
                    p.timings.get(key, 0)
                    for p in successful
                    if key in p.timings
                ]
                if values:
                    avg_timings[key] = sum(values) / len(values)

            return {
                "total_queries": len(self.profiles),
                "successful_queries": len(successful),
                "failed_queries": len(self.profiles) - len(successful),
                "average_times": avg_timings,
                "timestamp": datetime.now().isoformat()
            }

    def save_profiles(self, filename: str = "performance_profiles.json") -> Path:
        """Save all profiles to JSON file"""

        with self.lock:
            output_file = self.output_dir / filename

            # Convert dataclasses to dict
            profiles_dict = [
                {
                    "query": p.query,
                    "query_type": p.query_type,
                    "strategy_used": p.strategy_used,
                    "timings": p.timings,
                    "success": p.success,
                    "timestamp": p.timestamp,
                    "error": p.error
                }
                for p in self.profiles
            ]

            data = {
                "profiles": profiles_dict,
                "summary": self.get_summary()
            }

            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Profiles saved to {output_file}")
            return output_file

    def reset(self) -> None:
        """Clear all profiles"""

        with self.lock:
            self.profiles.clear()
            self.current_profile = {}
            logger.info("Profiler reset")