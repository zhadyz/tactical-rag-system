"""
Unit Tests for Explainability System

Tests query explanation generation, classification reasoning, and explanation text generation.
"""

import unittest
from explainability import (
    QueryExplanation,
    create_query_explanation
)


class TestQueryExplanation(unittest.TestCase):
    """Test QueryExplanation dataclass"""

    def test_initialization(self):
        """Test basic initialization"""
        explanation = QueryExplanation(
            query_type="simple",
            complexity_score=1,
            scoring_breakdown={"length": "5 words (+0)"},
            thresholds_used={"simple": 1, "moderate": 3},
            strategy_selected="simple_dense",
            strategy_reasoning="Straightforward query",
            key_factors=["length"]
        )

        self.assertEqual(explanation.query_type, "simple")
        self.assertEqual(explanation.complexity_score, 1)
        self.assertEqual(explanation.strategy_selected, "simple_dense")

    def test_to_dict(self):
        """Test dictionary conversion"""
        explanation = QueryExplanation(
            query_type="moderate",
            complexity_score=2,
            scoring_breakdown={"length": "8 words (+1)"},
            thresholds_used={"simple": 1, "moderate": 3}
        )

        result = explanation.to_dict()

        self.assertIsInstance(result, dict)
        self.assertEqual(result['query_type'], "moderate")
        self.assertEqual(result['complexity_score'], 2)
        self.assertIn('scoring_breakdown', result)

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            'query_type': 'complex',
            'complexity_score': 5,
            'scoring_breakdown': {"length": "15 words (+2)"},
            'thresholds_used': {"simple": 1, "moderate": 3},
            'strategy_selected': 'advanced_expanded',
            'strategy_reasoning': 'High complexity',
            'key_factors': ['length', 'question_type'],
            'example_text': 'Test explanation'
        }

        explanation = QueryExplanation.from_dict(data)

        self.assertEqual(explanation.query_type, 'complex')
        self.assertEqual(explanation.complexity_score, 5)
        self.assertEqual(len(explanation.key_factors), 2)

    def test_generate_explanation_text(self):
        """Test human-readable explanation generation"""
        explanation = QueryExplanation(
            query_type="complex",
            complexity_score=4,
            scoring_breakdown={
                "length": "12 words (+2)",
                "question_type": "why (+3)",
                "has_and_operator": "yes (+1)"
            },
            thresholds_used={"simple": 1, "moderate": 3},
            strategy_selected="advanced_expanded",
            strategy_reasoning="High complexity requires query expansion",
            key_factors=["length", "question_type", "has_and_operator"]
        )

        text = explanation.generate_explanation_text()

        self.assertIn("COMPLEX", text)
        self.assertIn("score: 4", text)
        self.assertIn("12 words (+2)", text)
        self.assertIn("advanced_expanded", text)
        self.assertIn("High complexity", text)


class TestCreateQueryExplanation(unittest.TestCase):
    """Test query explanation factory function"""

    def test_simple_query_explanation(self):
        """Test explanation for simple query"""
        explanation = create_query_explanation(
            query="Who is John Smith?",
            query_type="simple",
            complexity_score=0,
            scoring_breakdown={"length": "4 words (+0)", "question_type": "who (+0)"},
            simple_threshold=1,
            moderate_threshold=3
        )

        self.assertEqual(explanation.query_type, "simple")
        self.assertEqual(explanation.strategy_selected, "simple_dense")
        self.assertIn("Straightforward", explanation.strategy_reasoning)
        self.assertEqual(explanation.thresholds_used['simple'], 1)

    def test_moderate_query_explanation(self):
        """Test explanation for moderate query"""
        explanation = create_query_explanation(
            query="What are the key features of the system?",
            query_type="moderate",
            complexity_score=2,
            scoring_breakdown={
                "length": "8 words (+1)",
                "question_type": "what (+1)"
            },
            simple_threshold=1,
            moderate_threshold=3
        )

        self.assertEqual(explanation.query_type, "moderate")
        self.assertEqual(explanation.strategy_selected, "hybrid_reranked")
        self.assertIn("hybrid", explanation.strategy_reasoning.lower())

    def test_complex_query_explanation(self):
        """Test explanation for complex query"""
        explanation = create_query_explanation(
            query="Why does the system use this approach and what are the benefits?",
            query_type="complex",
            complexity_score=5,
            scoring_breakdown={
                "length": "12 words (+2)",
                "question_type": "why (+3)",
                "has_and_operator": "yes (+1)"
            },
            simple_threshold=1,
            moderate_threshold=3
        )

        self.assertEqual(explanation.query_type, "complex")
        self.assertEqual(explanation.strategy_selected, "advanced_expanded")
        self.assertIn("expansion", explanation.strategy_reasoning.lower())

    def test_key_factors_extraction(self):
        """Test that key factors are correctly extracted"""
        explanation = create_query_explanation(
            query="How does this work and why?",
            query_type="complex",
            complexity_score=4,
            scoring_breakdown={
                "length": "6 words (no points)",
                "question_type": "how does (+3)",
                "has_and_operator": "yes (+1)"
            },
            simple_threshold=1,
            moderate_threshold=3
        )

        # Key factors should only include those with + points
        self.assertIn("question_type", explanation.key_factors)
        self.assertIn("has_and_operator", explanation.key_factors)
        # Length should not be in key factors since it didn't contribute points
        self.assertEqual(len(explanation.key_factors), 2)

    def test_explanation_text_generation(self):
        """Test that example_text is auto-generated"""
        explanation = create_query_explanation(
            query="What is the capital?",
            query_type="moderate",
            complexity_score=1,
            scoring_breakdown={"length": "5 words (+0)", "question_type": "what (+1)"},
            simple_threshold=1,
            moderate_threshold=3
        )

        self.assertIsNotNone(explanation.example_text)
        self.assertIn("MODERATE", explanation.example_text)
        self.assertIn("score: 1", explanation.example_text)

    def test_threshold_values_included(self):
        """Test that thresholds are included in explanation"""
        explanation = create_query_explanation(
            query="Test query",
            query_type="simple",
            complexity_score=0,
            scoring_breakdown={"length": "2 words (+0)"},
            simple_threshold=2,
            moderate_threshold=5
        )

        self.assertEqual(explanation.thresholds_used['simple'], 2)
        self.assertEqual(explanation.thresholds_used['moderate'], 5)


class TestExplanationIntegration(unittest.TestCase):
    """Integration tests for explanation workflow"""

    def test_round_trip_serialization(self):
        """Test serialization and deserialization"""
        original = create_query_explanation(
            query="Why is the sky blue?",
            query_type="complex",
            complexity_score=3,
            scoring_breakdown={"question_type": "why (+3)"},
            simple_threshold=1,
            moderate_threshold=3
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = QueryExplanation.from_dict(data)

        self.assertEqual(original.query_type, restored.query_type)
        self.assertEqual(original.complexity_score, restored.complexity_score)
        self.assertEqual(original.strategy_selected, restored.strategy_selected)

    def test_explanation_completeness(self):
        """Test that all required fields are populated"""
        explanation = create_query_explanation(
            query="Explain the differences",
            query_type="complex",
            complexity_score=3,
            scoring_breakdown={"question_type": "explain (+3)"},
            simple_threshold=1,
            moderate_threshold=3
        )

        # All fields should be populated
        self.assertIsNotNone(explanation.query_type)
        self.assertIsNotNone(explanation.complexity_score)
        self.assertIsNotNone(explanation.scoring_breakdown)
        self.assertIsNotNone(explanation.thresholds_used)
        self.assertIsNotNone(explanation.strategy_selected)
        self.assertIsNotNone(explanation.strategy_reasoning)
        self.assertIsNotNone(explanation.example_text)


if __name__ == '__main__':
    unittest.main()
