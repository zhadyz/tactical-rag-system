"""
Integration Tests for Feedback System
Tests feedback collection, storage, and analysis
"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime

from feedback_system import FeedbackManager


class TestFeedbackIntegration:
    """Integration tests for feedback system"""

    @pytest.fixture
    def temp_feedback_file(self, tmp_path):
        """Create temporary feedback file"""
        feedback_file = tmp_path / "test_feedback.json"
        yield str(feedback_file)
        # Cleanup
        if feedback_file.exists():
            feedback_file.unlink()

    @pytest.fixture
    def feedback_manager(self, temp_feedback_file):
        """Create feedback manager with temp file"""
        return FeedbackManager(storage_file=temp_feedback_file)

    def test_initialization(self, feedback_manager, temp_feedback_file):
        """Test feedback manager initialization"""
        assert feedback_manager.storage_file == temp_feedback_file
        assert len(feedback_manager.feedback_data) == 0

        # Should create empty file
        assert Path(temp_feedback_file).exists()

    def test_add_positive_feedback(self, feedback_manager):
        """Test adding thumbs up feedback"""
        success = feedback_manager.add_feedback(
            query="What is RAG?",
            answer="RAG is Retrieval-Augmented Generation.",
            rating="thumbs_up",
            query_type="simple",
            strategy_used="simple_dense"
        )

        assert success
        assert len(feedback_manager.feedback_data) == 1

        entry = feedback_manager.feedback_data[0]
        assert entry["query"] == "What is RAG?"
        assert entry["rating"] == "thumbs_up"
        assert entry["query_type"] == "simple"
        assert "timestamp" in entry

    def test_add_negative_feedback(self, feedback_manager):
        """Test adding thumbs down feedback"""
        success = feedback_manager.add_feedback(
            query="Complex query about system architecture",
            answer="Answer provided",
            rating="thumbs_down",
            query_type="complex",
            strategy_used="advanced_expanded"
        )

        assert success
        assert len(feedback_manager.feedback_data) == 1
        assert feedback_manager.feedback_data[0]["rating"] == "thumbs_down"

    def test_multiple_feedback_entries(self, feedback_manager):
        """Test adding multiple feedback entries"""
        queries = [
            ("Query 1", "Answer 1", "thumbs_up", "simple"),
            ("Query 2", "Answer 2", "thumbs_down", "moderate"),
            ("Query 3", "Answer 3", "thumbs_up", "complex"),
            ("Query 4", "Answer 4", "thumbs_up", "simple"),
        ]

        for query, answer, rating, qtype in queries:
            feedback_manager.add_feedback(
                query=query,
                answer=answer,
                rating=rating,
                query_type=qtype,
                strategy_used="test_strategy"
            )

        assert len(feedback_manager.feedback_data) == 4

    def test_persistence(self, temp_feedback_file):
        """Test feedback persistence across instances"""
        # Create first manager and add feedback
        manager1 = FeedbackManager(storage_file=temp_feedback_file)
        manager1.add_feedback(
            query="Test query",
            answer="Test answer",
            rating="thumbs_up"
        )

        # Create second manager - should load existing data
        manager2 = FeedbackManager(storage_file=temp_feedback_file)
        assert len(manager2.feedback_data) == 1
        assert manager2.feedback_data[0]["query"] == "Test query"

    def test_get_feedback_stats_empty(self, feedback_manager):
        """Test statistics on empty feedback"""
        stats = feedback_manager.get_feedback_stats()

        assert stats["total_feedback"] == 0
        assert stats["thumbs_up_count"] == 0
        assert stats["thumbs_down_count"] == 0
        assert stats["satisfaction_rate"] == 0.0
        assert len(stats["by_query_type"]) == 0
        assert len(stats["by_strategy"]) == 0

    def test_get_feedback_stats_with_data(self, feedback_manager):
        """Test statistics with feedback data"""
        # Add mixed feedback
        feedback_entries = [
            ("Q1", "A1", "thumbs_up", "simple", "simple_dense"),
            ("Q2", "A2", "thumbs_up", "simple", "simple_dense"),
            ("Q3", "A3", "thumbs_down", "simple", "simple_dense"),
            ("Q4", "A4", "thumbs_up", "moderate", "hybrid_reranked"),
            ("Q5", "A5", "thumbs_down", "moderate", "hybrid_reranked"),
            ("Q6", "A6", "thumbs_down", "complex", "advanced_expanded"),
        ]

        for q, a, rating, qtype, strategy in feedback_entries:
            feedback_manager.add_feedback(q, a, rating, qtype, strategy)

        stats = feedback_manager.get_feedback_stats()

        # Overall stats
        assert stats["total_feedback"] == 6
        assert stats["thumbs_up_count"] == 3
        assert stats["thumbs_down_count"] == 3
        assert stats["satisfaction_rate"] == 50.0

        # By query type
        assert "simple" in stats["by_query_type"]
        assert stats["by_query_type"]["simple"]["thumbs_up"] == 2
        assert stats["by_query_type"]["simple"]["thumbs_down"] == 1

        assert "moderate" in stats["by_query_type"]
        assert stats["by_query_type"]["moderate"]["thumbs_up"] == 1
        assert stats["by_query_type"]["moderate"]["thumbs_down"] == 1

        # By strategy
        assert "simple_dense" in stats["by_strategy"]
        assert stats["by_strategy"]["simple_dense"]["thumbs_up"] == 2
        assert stats["by_strategy"]["simple_dense"]["thumbs_down"] == 1

    def test_get_low_rated_queries(self, feedback_manager):
        """Test identifying low-rated queries"""
        # Add feedback with some low-rated queries
        feedback_manager.add_feedback(
            "Why is the sky blue?", "Because...", "thumbs_down", "complex", "advanced"
        )
        feedback_manager.add_feedback(
            "What is 2+2?", "4", "thumbs_up", "simple", "simple"
        )
        feedback_manager.add_feedback(
            "Explain quantum physics", "Complex answer", "thumbs_down", "complex", "advanced"
        )

        low_rated = feedback_manager.get_low_rated_queries()

        assert len(low_rated) == 2
        assert all(entry["rating"] == "thumbs_down" for entry in low_rated)
        assert low_rated[0]["query"] in ["Why is the sky blue?", "Explain quantum physics"]

    def test_get_recent_feedback(self, feedback_manager):
        """Test retrieving recent feedback"""
        # Add 10 feedback entries
        for i in range(10):
            feedback_manager.add_feedback(
                f"Query {i}",
                f"Answer {i}",
                "thumbs_up" if i % 2 == 0 else "thumbs_down"
            )

        # Get last 5
        recent = feedback_manager.get_recent_feedback(limit=5)

        assert len(recent) == 5
        # Most recent should be Query 9
        assert recent[0]["query"] == "Query 9"
        assert recent[4]["query"] == "Query 5"

    def test_satisfaction_by_query_type(self, feedback_manager):
        """Test satisfaction rate calculation by query type"""
        # Simple: 2 up, 1 down = 66.7%
        feedback_manager.add_feedback("S1", "A1", "thumbs_up", "simple", "s")
        feedback_manager.add_feedback("S2", "A2", "thumbs_up", "simple", "s")
        feedback_manager.add_feedback("S3", "A3", "thumbs_down", "simple", "s")

        # Moderate: 1 up, 3 down = 25%
        feedback_manager.add_feedback("M1", "A1", "thumbs_up", "moderate", "m")
        feedback_manager.add_feedback("M2", "A2", "thumbs_down", "moderate", "m")
        feedback_manager.add_feedback("M3", "A3", "thumbs_down", "moderate", "m")
        feedback_manager.add_feedback("M4", "A4", "thumbs_down", "moderate", "m")

        stats = feedback_manager.get_feedback_stats()

        # Calculate satisfaction rates
        simple_total = stats["by_query_type"]["simple"]["thumbs_up"] + stats["by_query_type"]["simple"]["thumbs_down"]
        simple_satisfaction = (stats["by_query_type"]["simple"]["thumbs_up"] / simple_total) * 100
        assert 66.0 <= simple_satisfaction <= 67.0

        moderate_total = stats["by_query_type"]["moderate"]["thumbs_up"] + stats["by_query_type"]["moderate"]["thumbs_down"]
        moderate_satisfaction = (stats["by_query_type"]["moderate"]["thumbs_up"] / moderate_total) * 100
        assert moderate_satisfaction == 25.0

    def test_invalid_rating(self, feedback_manager):
        """Test handling invalid rating values"""
        success = feedback_manager.add_feedback(
            "Test query",
            "Test answer",
            "invalid_rating"  # Invalid
        )

        # Should still succeed but store the invalid rating
        assert success
        assert len(feedback_manager.feedback_data) == 1

    def test_missing_optional_fields(self, feedback_manager):
        """Test feedback with missing optional fields"""
        success = feedback_manager.add_feedback(
            query="Test query",
            answer="Test answer",
            rating="thumbs_up"
            # query_type and strategy_used are optional
        )

        assert success
        entry = feedback_manager.feedback_data[0]
        assert entry["query_type"] is None
        assert entry["strategy_used"] is None

    def test_feedback_timestamps(self, feedback_manager):
        """Test that timestamps are properly recorded"""
        import time

        feedback_manager.add_feedback("Q1", "A1", "thumbs_up")
        time.sleep(0.1)
        feedback_manager.add_feedback("Q2", "A2", "thumbs_down")

        assert len(feedback_manager.feedback_data) == 2

        ts1 = datetime.fromisoformat(feedback_manager.feedback_data[0]["timestamp"])
        ts2 = datetime.fromisoformat(feedback_manager.feedback_data[1]["timestamp"])

        # Second feedback should have later timestamp
        assert ts2 > ts1

    def test_large_feedback_dataset(self, feedback_manager):
        """Test with large number of feedback entries"""
        # Add 100 feedback entries
        for i in range(100):
            feedback_manager.add_feedback(
                f"Query {i}",
                f"Answer {i}",
                "thumbs_up" if i % 3 != 0 else "thumbs_down",
                query_type=["simple", "moderate", "complex"][i % 3],
                strategy_used="test_strategy"
            )

        assert len(feedback_manager.feedback_data) == 100

        stats = feedback_manager.get_feedback_stats()
        assert stats["total_feedback"] == 100

        # ~66% positive (multiples of 3 are negative)
        expected_positive = 67  # 100 - 33 (multiples of 3)
        assert abs(stats["thumbs_up_count"] - expected_positive) <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
