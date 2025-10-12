"""
Explainability Module - Query Classification and Retrieval Reasoning

Provides QueryExplanation dataclass to capture decision reasoning for:
- Query classification (why simple/moderate/complex)
- Retrieval strategy selection (why this approach)
- Scoring breakdown and threshold values
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class QueryExplanation:
    """
    Captures the reasoning behind query classification and retrieval decisions.

    Attributes:
        query_type: Classification result (simple/moderate/complex)
        complexity_score: Total complexity score
        scoring_breakdown: Dict of factors and their contributions
        thresholds_used: Dict of threshold values applied
        strategy_selected: Retrieval strategy chosen
        strategy_reasoning: Why this strategy was selected
        key_factors: List of primary factors influencing the decision
        example_text: Human-readable explanation
    """
    query_type: str  # "simple", "moderate", "complex"
    complexity_score: int
    scoring_breakdown: Dict[str, int] = field(default_factory=dict)
    thresholds_used: Dict[str, int] = field(default_factory=dict)
    strategy_selected: str = ""
    strategy_reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)
    example_text: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'query_type': self.query_type,
            'complexity_score': self.complexity_score,
            'scoring_breakdown': self.scoring_breakdown,
            'thresholds_used': self.thresholds_used,
            'strategy_selected': self.strategy_selected,
            'strategy_reasoning': self.strategy_reasoning,
            'key_factors': self.key_factors,
            'example_text': self.example_text
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'QueryExplanation':
        """Create from dictionary"""
        return cls(
            query_type=data.get('query_type', 'unknown'),
            complexity_score=data.get('complexity_score', 0),
            scoring_breakdown=data.get('scoring_breakdown', {}),
            thresholds_used=data.get('thresholds_used', {}),
            strategy_selected=data.get('strategy_selected', ''),
            strategy_reasoning=data.get('strategy_reasoning', ''),
            key_factors=data.get('key_factors', []),
            example_text=data.get('example_text', '')
        )

    def generate_explanation_text(self) -> str:
        """
        Generate human-readable explanation text.

        Example:
        "Query classified as COMPLEX (score: 4) because: length=12 words (+2),
        question type=why (+2), has 'and' operator (+1).
        Using Advanced strategy with query expansion."
        """
        breakdown_text = ", ".join([
            f"{factor}={details}"
            for factor, details in self.scoring_breakdown.items()
        ])

        threshold_text = ", ".join([
            f"{name}≤{value}"
            for name, value in self.thresholds_used.items()
        ])

        factors_text = "; ".join(self.key_factors) if self.key_factors else "standard factors"

        text = (
            f"Query classified as {self.query_type.upper()} (score: {self.complexity_score}) "
            f"because: {breakdown_text}. "
            f"Thresholds: {threshold_text}. "
            f"Using {self.strategy_selected} strategy. "
            f"Reasoning: {self.strategy_reasoning}"
        )

        return text


def create_query_explanation(
    query: str,
    query_type: str,
    complexity_score: int,
    scoring_breakdown: Dict[str, str],
    simple_threshold: int,
    moderate_threshold: int
) -> QueryExplanation:
    """
    Factory function to create QueryExplanation from classification results.

    Args:
        query: Original query string
        query_type: Classification result (simple/moderate/complex)
        complexity_score: Total complexity score
        scoring_breakdown: Dict of factors and their score contributions
        simple_threshold: Simple classification threshold
        moderate_threshold: Moderate classification threshold

    Returns:
        QueryExplanation object with full reasoning
    """
    # Determine strategy based on query type
    strategy_map = {
        'simple': 'simple_dense',
        'moderate': 'hybrid_reranked',
        'complex': 'advanced_expanded'
    }

    strategy_reasoning_map = {
        'simple': 'Straightforward query requires only dense vector retrieval',
        'moderate': 'Moderate complexity benefits from hybrid BM25+dense with reranking',
        'complex': 'High complexity requires query expansion and advanced fusion'
    }

    # Extract key factors (those that contributed points)
    key_factors = [
        factor for factor, value in scoring_breakdown.items()
        if '+' in str(value)
    ]

    explanation = QueryExplanation(
        query_type=query_type,
        complexity_score=complexity_score,
        scoring_breakdown=scoring_breakdown,
        thresholds_used={
            'simple': simple_threshold,
            'moderate': moderate_threshold
        },
        strategy_selected=strategy_map.get(query_type, 'unknown'),
        strategy_reasoning=strategy_reasoning_map.get(query_type, ''),
        key_factors=key_factors
    )

    # Generate human-readable text
    explanation.example_text = explanation.generate_explanation_text()

    return explanation
