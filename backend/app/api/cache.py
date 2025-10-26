"""
Cache Statistics API - ATLAS Protocol Implementation

Mission: Expose embedding cache metrics via FastAPI endpoints
Architecture: Prometheus-compatible metrics + JSON statistics
Performance Monitoring: Real-time cache hit rate and latency tracking

Research Source: V3.5_AUGMENTATION_REPORT.md Section 13 (Monitoring)
Implementation Date: 2025-10-23
Lead: THE DIDACT (Research Specialist)
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/cache", tags=["cache"])


class CacheStatistics(BaseModel):
    """Cache performance statistics model"""

    hits: int = Field(..., description="Total cache hits")
    misses: int = Field(..., description="Total cache misses")
    hit_rate_percent: float = Field(..., description="Cache hit rate as percentage")
    avg_latency_ms: float = Field(..., description="Average cache operation latency in milliseconds")
    total_operations: int = Field(..., description="Total cache operations")
    redis_memory_used_mb: Optional[float] = Field(None, description="Redis memory usage in MB")


class RetrieverStatistics(BaseModel):
    """Retriever performance statistics model"""

    total_queries: int = Field(..., description="Total queries processed")
    cache_hits: int = Field(..., description="Embedding cache hits")
    cache_hit_rate_percent: float = Field(..., description="Embedding cache hit rate")
    avg_embedding_time_ms: float = Field(..., description="Average embedding generation time")
    cache_enabled: bool = Field(..., description="Whether caching is enabled")


class CombinedStatistics(BaseModel):
    """Combined cache and retriever statistics"""

    embedding_cache: CacheStatistics
    retriever: RetrieverStatistics
    timestamp: str = Field(..., description="Statistics collection timestamp (ISO 8601)")


@router.get(
    "/stats",
    response_model=CombinedStatistics,
    summary="Get cache statistics",
    description="Retrieve comprehensive cache performance metrics including hit rates and latencies"
)
async def get_cache_statistics():
    """
    Get embedding cache and retriever statistics

    Returns:
        Combined statistics for cache performance monitoring

    Raises:
        HTTPException: If cache instance is not available
    """
    from datetime import datetime, timezone

    try:
        # Import RAG engine (lazy import to avoid circular dependencies)
        from ..core.rag_engine import rag_engine

        if not rag_engine or not rag_engine.initialized:
            raise HTTPException(
                status_code=503,
                detail="RAG engine not initialized. Cache statistics unavailable."
            )

        # Get embedding cache statistics
        if rag_engine.embedding_cache:
            cache_stats = await rag_engine.embedding_cache.get_stats()
        else:
            raise HTTPException(
                status_code=503,
                detail="Embedding cache not available"
            )

        # Get retriever statistics
        if rag_engine.retrieval_engine:
            retriever_stats = rag_engine.retrieval_engine.get_performance_stats()
        else:
            retriever_stats = {
                "total_queries": 0,
                "cache_hits": 0,
                "cache_hit_rate_percent": 0.0,
                "avg_embedding_time_ms": 0.0,
                "cache_enabled": False
            }

        return CombinedStatistics(
            embedding_cache=CacheStatistics(**cache_stats),
            retriever=RetrieverStatistics(**retriever_stats),
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve cache statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error retrieving cache statistics: {str(e)}"
        )


@router.post(
    "/invalidate",
    summary="Invalidate cache entry",
    description="Manually invalidate cache entry for specific text"
)
async def invalidate_cache_entry(text: str):
    """
    Invalidate cache entry for specific text

    Args:
        text: Text to invalidate cache for

    Returns:
        Success message

    Raises:
        HTTPException: If invalidation fails
    """
    try:
        from ..core.rag_engine import rag_engine

        if not rag_engine or not rag_engine.embedding_cache:
            raise HTTPException(
                status_code=503,
                detail="Embedding cache not available"
            )

        success = await rag_engine.embedding_cache.invalidate(text)

        if success:
            return {"status": "success", "message": f"Cache invalidated for text"}
        else:
            return {"status": "not_found", "message": "No cache entry found for text"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invalidate cache entry: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error invalidating cache: {str(e)}"
        )


@router.post(
    "/clear",
    summary="Clear all cache",
    description="Clear all cached embeddings (DESTRUCTIVE OPERATION)"
)
async def clear_all_cache():
    """
    Clear all cached embeddings

    WARNING: This is a destructive operation that will delete all cached embeddings.

    Returns:
        Success message with count of deleted entries

    Raises:
        HTTPException: If clear operation fails
    """
    try:
        from ..core.rag_engine import rag_engine

        if not rag_engine or not rag_engine.embedding_cache:
            raise HTTPException(
                status_code=503,
                detail="Embedding cache not available"
            )

        success = await rag_engine.embedding_cache.clear_all()

        if success:
            logger.warning("Cache cleared via API endpoint")
            return {
                "status": "success",
                "message": "All cache entries cleared",
                "warning": "This operation cannot be undone"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to clear cache"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error clearing cache: {str(e)}"
        )


@router.get(
    "/metrics",
    summary="Get Prometheus metrics",
    description="Get cache metrics in Prometheus format",
    response_class=None  # Plain text response
)
async def get_prometheus_metrics():
    """
    Get cache metrics in Prometheus format

    Returns:
        Prometheus-compatible metrics text

    Example Output:
        # HELP embedding_cache_hit_rate Cache hit rate percentage
        # TYPE embedding_cache_hit_rate gauge
        embedding_cache_hit_rate 72.5

        # HELP embedding_cache_latency_ms Average cache latency in milliseconds
        # TYPE embedding_cache_latency_ms gauge
        embedding_cache_latency_ms 0.85
    """
    try:
        from ..core.rag_engine import rag_engine
        from fastapi.responses import PlainTextResponse

        if not rag_engine or not rag_engine.embedding_cache:
            raise HTTPException(
                status_code=503,
                detail="Embedding cache not available"
            )

        cache_stats = await rag_engine.embedding_cache.get_stats()

        # Generate Prometheus metrics
        metrics_lines = [
            "# HELP embedding_cache_hit_rate Cache hit rate percentage",
            "# TYPE embedding_cache_hit_rate gauge",
            f"embedding_cache_hit_rate {cache_stats['hit_rate_percent']}",
            "",
            "# HELP embedding_cache_latency_ms Average cache latency in milliseconds",
            "# TYPE embedding_cache_latency_ms gauge",
            f"embedding_cache_latency_ms {cache_stats['avg_latency_ms']}",
            "",
            "# HELP embedding_cache_hits_total Total cache hits",
            "# TYPE embedding_cache_hits_total counter",
            f"embedding_cache_hits_total {cache_stats['hits']}",
            "",
            "# HELP embedding_cache_misses_total Total cache misses",
            "# TYPE embedding_cache_misses_total counter",
            f"embedding_cache_misses_total {cache_stats['misses']}",
            "",
            "# HELP embedding_cache_operations_total Total cache operations",
            "# TYPE embedding_cache_operations_total counter",
            f"embedding_cache_operations_total {cache_stats['total_operations']}",
            ""
        ]

        # Add Redis memory metric if available
        if "redis_memory_used_mb" in cache_stats and cache_stats["redis_memory_used_mb"]:
            metrics_lines.extend([
                "# HELP redis_memory_used_mb Redis memory usage in megabytes",
                "# TYPE redis_memory_used_mb gauge",
                f"redis_memory_used_mb {cache_stats['redis_memory_used_mb']}",
                ""
            ])

        metrics_text = "\n".join(metrics_lines)

        return PlainTextResponse(content=metrics_text, media_type="text/plain")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate Prometheus metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error generating metrics: {str(e)}"
        )


@router.get(
    "/health",
    summary="Cache health check",
    description="Check if cache is operational"
)
async def cache_health_check():
    """
    Health check for embedding cache

    Returns:
        Health status and basic information

    Example Response:
        {
            "status": "healthy",
            "cache_enabled": true,
            "redis_connected": true,
            "hit_rate_percent": 72.5
        }
    """
    try:
        from ..core.rag_engine import rag_engine

        if not rag_engine:
            return {
                "status": "unavailable",
                "cache_enabled": False,
                "redis_connected": False,
                "message": "RAG engine not initialized"
            }

        cache_enabled = bool(rag_engine.embedding_cache)

        if cache_enabled:
            # Test Redis connection
            try:
                cache_stats = await rag_engine.embedding_cache.get_stats()
                redis_connected = True
                hit_rate = cache_stats.get("hit_rate_percent", 0.0)
            except Exception as e:
                redis_connected = False
                hit_rate = 0.0
                logger.warning(f"Redis connection test failed: {e}")
        else:
            redis_connected = False
            hit_rate = 0.0

        status = "healthy" if (cache_enabled and redis_connected) else "degraded"

        return {
            "status": status,
            "cache_enabled": cache_enabled,
            "redis_connected": redis_connected,
            "hit_rate_percent": hit_rate
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "cache_enabled": False,
            "redis_connected": False,
            "error": str(e)
        }
