"""
Feedback System - User feedback collection and analysis for RAG quality improvement

Captures thumbs up/down ratings and provides analytics to identify problematic queries
"""

import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class FeedbackEntry:
    """Single feedback entry for a query/answer pair"""

    query: str
    answer: str
    rating: str  # "thumbs_up" or "thumbs_down"
    timestamp: str
    query_type: Optional[str] = None
    strategy_used: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class FeedbackManager:
    """
    Manages user feedback collection and analysis.

    Features:
    - JSON-based persistent storage
    - Thumbs up/down rating system
    - Feedback analytics and reporting
    - Identifies low-rated queries and patterns
    - Tracks feedback trends over time
    """

    def __init__(self, storage_file: str = "feedback.json"):
        """
        Initialize FeedbackManager.

        Args:
            storage_file: Path to JSON file for feedback storage
        """
        self.storage_file = Path(storage_file)
        self.feedback_data: List[FeedbackEntry] = []

        # Load existing feedback
        self._load_feedback()

        logger.info(f"FeedbackManager initialized (loaded {len(self.feedback_data)} entries)")

    def _load_feedback(self):
        """Load feedback from JSON file"""
        if not self.storage_file.exists():
            logger.info("No existing feedback file found. Starting fresh.")
            self.feedback_data = []
            return

        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert dicts back to FeedbackEntry objects
            self.feedback_data = [
                FeedbackEntry(**entry) for entry in data
            ]

            logger.info(f"Loaded {len(self.feedback_data)} feedback entries")

        except Exception as e:
            logger.error(f"Failed to load feedback: {e}")
            self.feedback_data = []

    def _save_feedback(self):
        """Save feedback to JSON file"""
        try:
            # Convert to dicts for JSON serialization
            data = [entry.to_dict() for entry in self.feedback_data]

            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self.feedback_data)} feedback entries")

        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")

    def add_feedback(
        self,
        query: str,
        answer: str,
        rating: str,
        query_type: Optional[str] = None,
        strategy_used: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Add new feedback entry.

        Args:
            query: User's question
            answer: System's response
            rating: "thumbs_up" or "thumbs_down"
            query_type: Classification (simple/moderate/complex)
            strategy_used: Retrieval strategy used
            session_id: Optional session identifier

        Returns:
            True if feedback added successfully, False otherwise
        """
        if rating not in ["thumbs_up", "thumbs_down"]:
            logger.error(f"Invalid rating: {rating}")
            return False

        entry = FeedbackEntry(
            query=query,
            answer=answer,
            rating=rating,
            timestamp=datetime.now().isoformat(),
            query_type=query_type,
            strategy_used=strategy_used,
            session_id=session_id
        )

        self.feedback_data.append(entry)
        self._save_feedback()

        logger.info(f"Feedback added: {rating} for query '{query[:50]}...'")
        return True

    def get_all_feedback(self) -> List[Dict]:
        """
        Get all feedback entries.

        Returns:
            List of feedback dictionaries
        """
        return [entry.to_dict() for entry in self.feedback_data]

    def get_feedback_stats(self) -> Dict:
        """
        Get overall feedback statistics.

        Returns:
            Dictionary with:
            - total_feedback: Total number of ratings
            - thumbs_up_count: Number of positive ratings
            - thumbs_down_count: Number of negative ratings
            - satisfaction_rate: Percentage of positive ratings
            - by_query_type: Breakdown by query classification
            - by_strategy: Breakdown by retrieval strategy
        """
        if not self.feedback_data:
            return {
                "total_feedback": 0,
                "thumbs_up_count": 0,
                "thumbs_down_count": 0,
                "satisfaction_rate": 0.0,
                "by_query_type": {},
                "by_strategy": {}
            }

        thumbs_up = sum(1 for e in self.feedback_data if e.rating == "thumbs_up")
        thumbs_down = sum(1 for e in self.feedback_data if e.rating == "thumbs_down")
        total = len(self.feedback_data)

        # Breakdown by query type
        by_type = defaultdict(lambda: {"thumbs_up": 0, "thumbs_down": 0})
        for entry in self.feedback_data:
            if entry.query_type:
                by_type[entry.query_type][entry.rating] += 1

        # Breakdown by strategy
        by_strategy = defaultdict(lambda: {"thumbs_up": 0, "thumbs_down": 0})
        for entry in self.feedback_data:
            if entry.strategy_used:
                by_strategy[entry.strategy_used][entry.rating] += 1

        return {
            "total_feedback": total,
            "thumbs_up_count": thumbs_up,
            "thumbs_down_count": thumbs_down,
            "satisfaction_rate": (thumbs_up / total * 100) if total > 0 else 0.0,
            "by_query_type": dict(by_type),
            "by_strategy": dict(by_strategy)
        }

    def get_low_rated_queries(self, limit: int = 10) -> List[Dict]:
        """
        Get queries with thumbs down ratings.

        Args:
            limit: Maximum number of results

        Returns:
            List of low-rated query details
        """
        low_rated = [
            {
                "query": entry.query,
                "answer": entry.answer[:200] + "...",  # Truncate for display
                "timestamp": entry.timestamp,
                "query_type": entry.query_type,
                "strategy_used": entry.strategy_used
            }
            for entry in self.feedback_data
            if entry.rating == "thumbs_down"
        ]

        # Sort by most recent first
        low_rated.sort(key=lambda x: x["timestamp"], reverse=True)

        return low_rated[:limit]

    def identify_failure_patterns(self) -> Dict:
        """
        Analyze feedback to identify common failure patterns.

        Returns:
            Dictionary with:
            - problematic_query_types: Query types with low satisfaction
            - problematic_strategies: Strategies with low satisfaction
            - common_issues: Patterns in low-rated queries
        """
        if not self.feedback_data:
            return {
                "problematic_query_types": [],
                "problematic_strategies": [],
                "common_issues": "Insufficient feedback data for pattern analysis"
            }

        stats = self.get_feedback_stats()

        # Identify query types with <50% satisfaction
        problematic_types = []
        for query_type, counts in stats["by_query_type"].items():
            total = counts["thumbs_up"] + counts["thumbs_down"]
            if total >= 3:  # At least 3 samples
                satisfaction = counts["thumbs_up"] / total
                if satisfaction < 0.5:
                    problematic_types.append({
                        "query_type": query_type,
                        "satisfaction_rate": satisfaction * 100,
                        "sample_size": total
                    })

        # Identify strategies with <50% satisfaction
        problematic_strategies = []
        for strategy, counts in stats["by_strategy"].items():
            total = counts["thumbs_up"] + counts["thumbs_down"]
            if total >= 3:  # At least 3 samples
                satisfaction = counts["thumbs_up"] / total
                if satisfaction < 0.5:
                    problematic_strategies.append({
                        "strategy": strategy,
                        "satisfaction_rate": satisfaction * 100,
                        "sample_size": total
                    })

        # Analyze common words in low-rated queries
        low_rated_queries = [
            e.query.lower() for e in self.feedback_data
            if e.rating == "thumbs_down"
        ]

        # Simple word frequency analysis
        word_freq = defaultdict(int)
        for query in low_rated_queries:
            words = query.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] += 1

        common_words = sorted(
            word_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        common_issues = "Low-rated queries often contain: " + ", ".join(
            [f"{word} ({count}x)" for word, count in common_words]
        ) if common_words else "No clear patterns detected"

        return {
            "problematic_query_types": problematic_types,
            "problematic_strategies": problematic_strategies,
            "common_issues": common_issues
        }

    def get_recent_feedback(self, limit: int = 20) -> List[Dict]:
        """
        Get most recent feedback entries.

        Args:
            limit: Number of entries to return

        Returns:
            List of recent feedback dictionaries
        """
        # Sort by timestamp descending
        sorted_feedback = sorted(
            self.feedback_data,
            key=lambda x: x.timestamp,
            reverse=True
        )

        return [entry.to_dict() for entry in sorted_feedback[:limit]]

    def clear_feedback(self):
        """Clear all feedback data (for testing/reset)"""
        self.feedback_data = []
        self._save_feedback()
        logger.info("All feedback cleared")

    def export_feedback(self, output_file: str) -> bool:
        """
        Export feedback to a different file.

        Args:
            output_file: Path to export file

        Returns:
            True if export successful
        """
        try:
            data = [entry.to_dict() for entry in self.feedback_data]

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {len(self.feedback_data)} entries to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
