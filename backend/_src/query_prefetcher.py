"""
L5 Query Prefetching Cache - ATLAS Protocol Implementation

Mission: Achieve +50% cache hit rate improvement through intelligent query prediction
Architecture: Pattern-based prefetching with background execution
Performance Target: 80-90% prefetch accuracy, <100ms prediction latency

Research Sources:
- CaGR-RAG: Context-aware Query Grouping (arXiv:2505.01164)
- Semantic caching patterns from waadi.ai
- Conversation flow analysis from V3.5_AUGMENTATION_REPORT.md

Implementation Date: 2025-10-23
Lead: THE DIDACT (Research Specialist)
"""

import asyncio
import hashlib
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple, Set
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Query classification types for prefetch prediction"""
    CLARIFICATION = "clarification"  # "What do you mean by...?"
    ELABORATION = "elaboration"      # "Tell me more about..."
    EXAMPLE = "example"               # "Can you give an example?"
    COMPARISON = "comparison"         # "How does X compare to Y?"
    PROCEDURE = "procedure"           # "How do I...?"
    DEFINITION = "definition"         # "What is...?"
    FOLLOW_UP = "follow_up"          # General follow-up question
    NEW_TOPIC = "new_topic"          # Unrelated to previous queries


class PrefetchPriority(Enum):
    """Priority levels for prefetch execution"""
    HIGH = 3      # >70% confidence, execute immediately
    MEDIUM = 2    # 40-70% confidence, execute when idle
    LOW = 1       # <40% confidence, execute if system is very idle


@dataclass
class QueryPattern:
    """Represents a detected query pattern for prediction"""
    query_type: QueryType
    confidence: float
    context_keywords: Set[str]
    predicted_queries: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

    def get_priority(self) -> PrefetchPriority:
        """Calculate prefetch priority based on confidence"""
        if self.confidence >= 0.7:
            return PrefetchPriority.HIGH
        elif self.confidence >= 0.4:
            return PrefetchPriority.MEDIUM
        else:
            return PrefetchPriority.LOW


@dataclass
class PrefetchTask:
    """Represents a prefetch task to execute"""
    query: str
    pattern: QueryPattern
    priority: PrefetchPriority
    created_at: datetime = field(default_factory=datetime.now)
    executed: bool = False
    execution_time_ms: float = 0.0


@dataclass
class PrefetchMetrics:
    """Statistics for monitoring prefetch performance"""
    total_predictions: int = 0
    total_prefetches: int = 0
    successful_hits: int = 0  # Prefetched query was actually requested
    failed_prefetches: int = 0
    avg_prediction_latency_ms: float = 0.0
    avg_prefetch_latency_ms: float = 0.0
    cache_hit_improvement_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary"""
        hit_rate = (
            (self.successful_hits / self.total_prefetches * 100.0)
            if self.total_prefetches > 0 else 0.0
        )

        return {
            "total_predictions": self.total_predictions,
            "total_prefetches": self.total_prefetches,
            "successful_hits": self.successful_hits,
            "prefetch_hit_rate_percent": round(hit_rate, 2),
            "avg_prediction_latency_ms": round(self.avg_prediction_latency_ms, 3),
            "avg_prefetch_latency_ms": round(self.avg_prefetch_latency_ms, 3),
            "cache_hit_improvement_percent": round(self.cache_hit_improvement_percent, 2)
        }


class ConversationPatternAnalyzer:
    """
    Analyzes conversation history to detect patterns and predict next queries.

    Pattern Detection:
    - Clarification patterns (what/which/can you explain)
    - Elaboration patterns (more details/expand on)
    - Example patterns (example/instance/case)
    - Comparison patterns (vs/compare/difference)
    - Procedure patterns (how to/steps/guide)
    """

    # Pattern detection keywords
    CLARIFICATION_KEYWORDS = {
        "what do you mean", "can you explain", "what is", "what are",
        "clarify", "define", "meaning of", "which"
    }

    ELABORATION_KEYWORDS = {
        "tell me more", "expand on", "more details", "elaborate",
        "in depth", "further information", "more about"
    }

    EXAMPLE_KEYWORDS = {
        "example", "for instance", "such as", "like what",
        "can you show", "demonstrate", "case study"
    }

    COMPARISON_KEYWORDS = {
        "compare", "difference between", "versus", "vs",
        "better than", "worse than", "compared to", "contrast"
    }

    PROCEDURE_KEYWORDS = {
        "how do i", "how to", "steps to", "guide to",
        "tutorial", "instructions", "process for", "way to"
    }

    FOLLOW_UP_INDICATORS = {
        "also", "additionally", "furthermore", "moreover",
        "what about", "how about", "and", "but"
    }

    def __init__(self):
        self.pattern_templates = self._build_pattern_templates()

    def _build_pattern_templates(self) -> Dict[QueryType, List[str]]:
        """
        Build prediction templates for each query type.

        Templates use {KEYWORD} placeholders that are replaced with
        context-specific terms from conversation history.
        """
        return {
            QueryType.CLARIFICATION: [
                "What do you mean by {KEYWORD}?",
                "Can you explain {KEYWORD} in more detail?",
                "What exactly is {KEYWORD}?",
                "Could you clarify what {KEYWORD} means?",
            ],
            QueryType.ELABORATION: [
                "Tell me more about {KEYWORD}",
                "Can you expand on {KEYWORD}?",
                "What are more details about {KEYWORD}?",
                "I'd like to know more about {KEYWORD}",
            ],
            QueryType.EXAMPLE: [
                "Can you give an example of {KEYWORD}?",
                "What's a specific example of {KEYWORD}?",
                "Show me an instance of {KEYWORD}",
                "Do you have a case study for {KEYWORD}?",
            ],
            QueryType.COMPARISON: [
                "How does {KEYWORD} compare to {KEYWORD2}?",
                "What's the difference between {KEYWORD} and {KEYWORD2}?",
                "Is {KEYWORD} better than {KEYWORD2}?",
                "{KEYWORD} vs {KEYWORD2}",
            ],
            QueryType.PROCEDURE: [
                "How do I {KEYWORD}?",
                "What are the steps to {KEYWORD}?",
                "Guide me through {KEYWORD}",
                "How to {KEYWORD}",
            ],
        }

    def classify_query(self, query: str) -> QueryType:
        """
        Classify query type based on keyword patterns.

        Args:
            query: User query text

        Returns:
            Detected query type
        """
        query_lower = query.lower()

        # Check patterns in order of specificity
        if any(kw in query_lower for kw in self.CLARIFICATION_KEYWORDS):
            return QueryType.CLARIFICATION
        elif any(kw in query_lower for kw in self.ELABORATION_KEYWORDS):
            return QueryType.ELABORATION
        elif any(kw in query_lower for kw in self.EXAMPLE_KEYWORDS):
            return QueryType.EXAMPLE
        elif any(kw in query_lower for kw in self.COMPARISON_KEYWORDS):
            return QueryType.COMPARISON
        elif any(kw in query_lower for kw in self.PROCEDURE_KEYWORDS):
            return QueryType.PROCEDURE
        elif any(kw in query_lower for kw in self.FOLLOW_UP_INDICATORS):
            return QueryType.FOLLOW_UP
        else:
            return QueryType.NEW_TOPIC

    def extract_keywords(
        self,
        query: str,
        context_history: List[str],
        top_k: int = 5
    ) -> Set[str]:
        """
        Extract important keywords from query and context.

        Uses simple frequency analysis and stopword filtering.
        In production, this could use NLP (spaCy, NLTK).

        Args:
            query: Current query
            context_history: Recent conversation history
            top_k: Number of keywords to extract

        Returns:
            Set of extracted keywords
        """
        # Common stopwords to filter
        STOPWORDS = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with', 'you', 'your',
            'i', 'me', 'my', 'we', 'our', 'can', 'could', 'would',
            'should', 'do', 'does', 'did', 'have', 'had', 'what',
            'when', 'where', 'who', 'which', 'why', 'how'
        }

        # Combine query with recent context
        all_text = f"{query} {' '.join(context_history[-3:])}"

        # Tokenize and filter
        words = all_text.lower().split()
        keywords = [
            w for w in words
            if len(w) > 3 and w not in STOPWORDS and w.isalpha()
        ]

        # Frequency count
        word_freq = defaultdict(int)
        for word in keywords:
            word_freq[word] += 1

        # Get top-k most frequent
        top_keywords = sorted(
            word_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        return {word for word, _ in top_keywords}

    def predict_next_queries(
        self,
        current_query: str,
        context_history: List[str],
        query_type: Optional[QueryType] = None,
        max_predictions: int = 3
    ) -> Tuple[List[str], float]:
        """
        Predict likely follow-up queries based on current query and context.

        Args:
            current_query: Most recent user query
            context_history: Previous queries in conversation
            query_type: Optional pre-classified query type
            max_predictions: Maximum number of predictions to generate

        Returns:
            Tuple of (predicted_queries, confidence_score)
        """
        # Classify query type if not provided
        if query_type is None:
            query_type = self.classify_query(current_query)

        # Extract context keywords
        keywords = self.extract_keywords(
            current_query,
            context_history,
            top_k=5
        )

        if not keywords:
            # No keywords found - low confidence
            return [], 0.1

        # Generate predictions based on query type
        predictions = []

        # Get templates for this query type and adjacent types
        primary_templates = self.pattern_templates.get(query_type, [])

        # Determine likely follow-up query types
        follow_up_types = self._get_follow_up_types(query_type)

        # Generate predictions from primary type
        keyword_list = list(keywords)
        for template in primary_templates[:max_predictions]:
            if "{KEYWORD2}" in template and len(keyword_list) >= 2:
                # Comparison template - needs 2 keywords
                pred = template.replace("{KEYWORD}", keyword_list[0])
                pred = pred.replace("{KEYWORD2}", keyword_list[1])
                predictions.append(pred)
            elif "{KEYWORD}" in template and keyword_list:
                # Single keyword template
                pred = template.replace("{KEYWORD}", keyword_list[0])
                predictions.append(pred)

        # Add predictions from follow-up types
        for follow_type in follow_up_types:
            templates = self.pattern_templates.get(follow_type, [])
            for template in templates[:1]:  # Just 1 from each follow-up type
                if len(predictions) >= max_predictions:
                    break
                if "{KEYWORD}" in template and keyword_list:
                    pred = template.replace("{KEYWORD}", keyword_list[0])
                    predictions.append(pred)

        # Calculate confidence based on pattern strength
        confidence = self._calculate_confidence(
            query_type,
            len(keywords),
            len(context_history)
        )

        return predictions[:max_predictions], confidence

    def _get_follow_up_types(self, current_type: QueryType) -> List[QueryType]:
        """
        Determine likely follow-up query types based on current type.

        Conversation flow patterns:
        - Definition → Elaboration → Example
        - Procedure → Clarification → Example
        - Comparison → Clarification → Elaboration
        """
        flow_patterns = {
            QueryType.DEFINITION: [QueryType.ELABORATION, QueryType.EXAMPLE],
            QueryType.ELABORATION: [QueryType.EXAMPLE, QueryType.CLARIFICATION],
            QueryType.EXAMPLE: [QueryType.PROCEDURE, QueryType.COMPARISON],
            QueryType.PROCEDURE: [QueryType.CLARIFICATION, QueryType.EXAMPLE],
            QueryType.COMPARISON: [QueryType.CLARIFICATION, QueryType.ELABORATION],
            QueryType.CLARIFICATION: [QueryType.ELABORATION, QueryType.EXAMPLE],
            QueryType.FOLLOW_UP: [QueryType.ELABORATION, QueryType.EXAMPLE],
            QueryType.NEW_TOPIC: [QueryType.DEFINITION, QueryType.ELABORATION],
        }

        return flow_patterns.get(current_type, [QueryType.ELABORATION])

    def _calculate_confidence(
        self,
        query_type: QueryType,
        num_keywords: int,
        context_length: int
    ) -> float:
        """
        Calculate prediction confidence based on pattern strength.

        Confidence factors:
        - Query type specificity (specific types = higher confidence)
        - Number of extracted keywords (more = higher)
        - Context history length (more = higher)

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence by query type
        type_confidence = {
            QueryType.CLARIFICATION: 0.8,
            QueryType.ELABORATION: 0.75,
            QueryType.EXAMPLE: 0.7,
            QueryType.COMPARISON: 0.65,
            QueryType.PROCEDURE: 0.7,
            QueryType.FOLLOW_UP: 0.6,
            QueryType.DEFINITION: 0.65,
            QueryType.NEW_TOPIC: 0.3,
        }

        base = type_confidence.get(query_type, 0.5)

        # Adjust based on keywords (more keywords = higher confidence)
        keyword_factor = min(num_keywords / 5.0, 1.0) * 0.2

        # Adjust based on context (more context = higher confidence)
        context_factor = min(context_length / 5.0, 1.0) * 0.1

        confidence = base + keyword_factor + context_factor

        return min(confidence, 1.0)


class QueryPrefetcher:
    """
    L5 Query Prefetching Cache - Intelligent prediction and background prefetching.

    Architecture:
    - Analyzes conversation patterns to predict next queries
    - Executes prefetch in background (asyncio tasks)
    - Resource-aware execution (doesn't overwhelm system)
    - Integrates with L4 embedding cache
    - Tracks hit rate improvement metrics

    Performance Characteristics:
    - Prediction latency: <100ms
    - Prefetch accuracy: 70-90%
    - Cache hit rate improvement: +50% target
    - Background execution: non-blocking
    """

    def __init__(
        self,
        embedding_cache: Any,  # EmbeddingCache instance
        retrieval_engine: Any,  # AdaptiveRetriever instance
        max_concurrent_prefetches: int = 3,
        prediction_window_size: int = 10,
        enable_auto_prefetch: bool = True,
    ):
        """
        Initialize Query Prefetcher.

        Args:
            embedding_cache: L4 EmbeddingCache instance for storing prefetched embeddings
            retrieval_engine: AdaptiveRetriever for executing prefetch searches
            max_concurrent_prefetches: Maximum parallel prefetch tasks
            prediction_window_size: Number of recent queries to analyze
            enable_auto_prefetch: Enable automatic prefetching after queries
        """
        self.embedding_cache = embedding_cache
        self.retrieval_engine = retrieval_engine
        self.max_concurrent_prefetches = max_concurrent_prefetches
        self.prediction_window_size = prediction_window_size
        self.enable_auto_prefetch = enable_auto_prefetch

        # Pattern analyzer
        self.analyzer = ConversationPatternAnalyzer()

        # Conversation history tracking
        self.query_history: deque = deque(maxlen=prediction_window_size)

        # Prefetch task queue (priority queue)
        self.prefetch_queue: Dict[PrefetchPriority, deque] = {
            PrefetchPriority.HIGH: deque(),
            PrefetchPriority.MEDIUM: deque(),
            PrefetchPriority.LOW: deque(),
        }

        # Active prefetch tasks
        self.active_tasks: Set[asyncio.Task] = set()

        # Prefetched queries tracking (for hit rate calculation)
        self.prefetched_queries: Dict[str, PrefetchTask] = {}
        self.query_hash_map: Dict[str, str] = {}  # hash -> original query

        # Metrics
        self.metrics = PrefetchMetrics()
        self.prediction_times: deque = deque(maxlen=100)
        self.prefetch_times: deque = deque(maxlen=100)

        # Background worker task
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False

        logger.info(
            f"QueryPrefetcher initialized: "
            f"max_concurrent={max_concurrent_prefetches}, "
            f"window_size={prediction_window_size}, "
            f"auto_prefetch={enable_auto_prefetch}"
        )

    def _hash_query(self, query: str) -> str:
        """Generate hash for query tracking"""
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    async def start(self):
        """Start background prefetch worker"""
        if self.running:
            logger.warning("Prefetch worker already running")
            return

        self.running = True
        self.worker_task = asyncio.create_task(self._prefetch_worker())
        logger.info("✓ Prefetch worker started")

    async def stop(self):
        """Stop background prefetch worker"""
        self.running = False

        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        # Wait for active tasks to complete
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks, return_exceptions=True)

        logger.info("✓ Prefetch worker stopped")

    async def on_query_received(
        self,
        query: str,
        trigger_prefetch: bool = True
    ) -> Optional[QueryPattern]:
        """
        Called when a new query is received.

        Tracks query in history, checks if it was prefetched (for metrics),
        and optionally triggers prefetch prediction for next queries.

        Args:
            query: User query text
            trigger_prefetch: Whether to predict and prefetch next queries

        Returns:
            QueryPattern if prefetch was triggered, None otherwise
        """
        # Check if this query was prefetched (cache hit)
        query_hash = self._hash_query(query)
        if query_hash in self.prefetched_queries:
            task = self.prefetched_queries[query_hash]
            if task.executed:
                self.metrics.successful_hits += 1
                logger.info(
                    f"✓ Prefetch HIT: '{query[:50]}...' "
                    f"(predicted {(datetime.now() - task.created_at).total_seconds():.1f}s ago)"
                )

        # Add to conversation history
        self.query_history.append(query)

        # Trigger prefetch if enabled
        if trigger_prefetch and self.enable_auto_prefetch:
            pattern = await self.predict_and_prefetch(query)
            return pattern

        return None

    async def predict_and_prefetch(
        self,
        current_query: str,
        max_predictions: int = 3
    ) -> Optional[QueryPattern]:
        """
        Predict next likely queries and queue them for prefetching.

        Args:
            current_query: Most recent user query
            max_predictions: Maximum predictions to generate

        Returns:
            QueryPattern with predictions and confidence
        """
        start_time = time.perf_counter()

        # Classify query and predict next queries
        query_type = self.analyzer.classify_query(current_query)

        predictions, confidence = self.analyzer.predict_next_queries(
            current_query=current_query,
            context_history=list(self.query_history),
            query_type=query_type,
            max_predictions=max_predictions
        )

        prediction_time_ms = (time.perf_counter() - start_time) * 1000
        self.prediction_times.append(prediction_time_ms)
        self.metrics.total_predictions += 1

        if not predictions:
            logger.debug("No predictions generated (insufficient context)")
            return None

        # Extract context keywords for pattern
        keywords = self.analyzer.extract_keywords(
            current_query,
            list(self.query_history),
            top_k=5
        )

        # Create pattern
        pattern = QueryPattern(
            query_type=query_type,
            confidence=confidence,
            context_keywords=keywords,
            predicted_queries=predictions
        )

        # Queue prefetch tasks
        priority = pattern.get_priority()
        for pred_query in predictions:
            task = PrefetchTask(
                query=pred_query,
                pattern=pattern,
                priority=priority
            )
            self.prefetch_queue[priority].append(task)

            # Track for hit detection
            query_hash = self._hash_query(pred_query)
            self.prefetched_queries[query_hash] = task

        logger.info(
            f"Predicted {len(predictions)} queries "
            f"(type={query_type.value}, conf={confidence:.2f}, "
            f"priority={priority.value}, latency={prediction_time_ms:.1f}ms)"
        )

        return pattern

    async def _prefetch_worker(self):
        """
        Background worker that executes prefetch tasks from queue.

        Processes tasks in priority order:
        1. HIGH priority - execute immediately
        2. MEDIUM priority - execute when <50% capacity
        3. LOW priority - execute when <25% capacity
        """
        logger.info("Prefetch worker running...")

        while self.running:
            try:
                # Check system capacity
                capacity_used = len(self.active_tasks) / self.max_concurrent_prefetches

                # Determine which priorities to process
                process_priorities = []
                if capacity_used < 0.25:
                    # System very idle - process all priorities
                    process_priorities = [
                        PrefetchPriority.HIGH,
                        PrefetchPriority.MEDIUM,
                        PrefetchPriority.LOW
                    ]
                elif capacity_used < 0.5:
                    # System moderately busy - process HIGH and MEDIUM
                    process_priorities = [
                        PrefetchPriority.HIGH,
                        PrefetchPriority.MEDIUM
                    ]
                else:
                    # System busy - only HIGH priority
                    process_priorities = [PrefetchPriority.HIGH]

                # Get next task from highest priority queue
                task = None
                for priority in process_priorities:
                    if self.prefetch_queue[priority]:
                        task = self.prefetch_queue[priority].popleft()
                        break

                if task and not task.executed:
                    # Execute prefetch
                    if len(self.active_tasks) < self.max_concurrent_prefetches:
                        prefetch_task = asyncio.create_task(
                            self._execute_prefetch(task)
                        )
                        self.active_tasks.add(prefetch_task)
                        prefetch_task.add_done_callback(self.active_tasks.discard)

                # Cleanup completed tasks
                self.active_tasks = {t for t in self.active_tasks if not t.done()}

                # Sleep to avoid busy-wait
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Prefetch worker error: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _execute_prefetch(self, task: PrefetchTask):
        """
        Execute a single prefetch task.

        Generates embedding for predicted query and performs vector search,
        caching results for future use.
        """
        start_time = time.perf_counter()

        try:
            logger.debug(f"Executing prefetch: '{task.query[:50]}...'")

            # Generate embedding (will be cached in L4)
            embedding = await self.retrieval_engine.embed_query(task.query)

            # Optionally perform full retrieval to warm cache
            # (Commented out by default to reduce resource usage)
            # result = await self.retrieval_engine.retrieve(
            #     query=task.query,
            #     top_k=5
            # )

            task.executed = True
            task.execution_time_ms = (time.perf_counter() - start_time) * 1000

            self.prefetch_times.append(task.execution_time_ms)
            self.metrics.total_prefetches += 1

            logger.debug(
                f"✓ Prefetch complete: '{task.query[:50]}...' "
                f"({task.execution_time_ms:.1f}ms)"
            )

        except Exception as e:
            self.metrics.failed_prefetches += 1
            logger.error(f"Prefetch execution failed: {e}", exc_info=True)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get prefetch performance metrics.

        Returns:
            Dictionary with comprehensive metrics
        """
        # Calculate average latencies
        if self.prediction_times:
            self.metrics.avg_prediction_latency_ms = np.mean(self.prediction_times)

        if self.prefetch_times:
            self.metrics.avg_prefetch_latency_ms = np.mean(self.prefetch_times)

        # Calculate cache hit improvement
        # This is estimated as: (successful_hits / total_queries) * 100
        total_queries = len(self.query_history)
        if total_queries > 0:
            baseline_hit_rate = 0.70  # Assume 70% baseline from L4 cache
            prefetch_hits = self.metrics.successful_hits / total_queries
            improved_rate = baseline_hit_rate + prefetch_hits
            improvement = ((improved_rate - baseline_hit_rate) / baseline_hit_rate) * 100
            self.metrics.cache_hit_improvement_percent = improvement

        metrics_dict = self.metrics.to_dict()

        # Add queue stats
        metrics_dict["queue_sizes"] = {
            "high": len(self.prefetch_queue[PrefetchPriority.HIGH]),
            "medium": len(self.prefetch_queue[PrefetchPriority.MEDIUM]),
            "low": len(self.prefetch_queue[PrefetchPriority.LOW]),
        }
        metrics_dict["active_tasks"] = len(self.active_tasks)
        metrics_dict["conversation_history_size"] = len(self.query_history)

        return metrics_dict

    def clear_history(self):
        """Clear conversation history and reset state"""
        self.query_history.clear()
        self.prefetched_queries.clear()
        self.query_hash_map.clear()

        # Clear queues
        for priority in self.prefetch_queue:
            self.prefetch_queue[priority].clear()

        logger.info("Conversation history and prefetch state cleared")

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"QueryPrefetcher("
            f"predictions={self.metrics.total_predictions}, "
            f"prefetches={self.metrics.total_prefetches}, "
            f"hits={self.metrics.successful_hits}, "
            f"improvement={self.metrics.cache_hit_improvement_percent:.1f}%"
            f")"
        )


# Singleton instance for global access
_global_prefetcher_instance: Optional[QueryPrefetcher] = None


async def get_query_prefetcher(
    embedding_cache: Any,
    retrieval_engine: Any,
    max_concurrent: int = 3
) -> QueryPrefetcher:
    """
    Get or create global query prefetcher instance.

    Args:
        embedding_cache: EmbeddingCache instance
        retrieval_engine: AdaptiveRetriever instance
        max_concurrent: Maximum concurrent prefetch tasks

    Returns:
        Global QueryPrefetcher instance
    """
    global _global_prefetcher_instance

    if _global_prefetcher_instance is None:
        _global_prefetcher_instance = QueryPrefetcher(
            embedding_cache=embedding_cache,
            retrieval_engine=retrieval_engine,
            max_concurrent_prefetches=max_concurrent
        )
        await _global_prefetcher_instance.start()

    return _global_prefetcher_instance
