"""
ATLAS Protocol - Confidence Scoring

Calculates confidence scores for RAG answers based on multiple signals:
- Retrieval scores (document relevance)
- Answer-document semantic alignment
- Answer completeness heuristics
- Cross-reference consistency

Output: Confidence score 0-100 with interpretation (low/medium/high/very high)
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Calculates multi-signal confidence scores for RAG answers.

    Signals:
    1. Retrieval quality (avg relevance score)
    2. Semantic alignment (answer-document similarity)
    3. Answer completeness (length, specificity)
    4. Consistency (cross-reference agreement)

    Score Interpretation:
    - 0-30: Low confidence (may be hallucination)
    - 30-60: Medium confidence (partial information)
    - 60-85: High confidence (good answer)
    - 85-100: Very high confidence (excellent answer)
    """

    def __init__(self, embeddings=None):
        """
        Initialize confidence scorer.

        Args:
            embeddings: Embedding model for semantic alignment calculation
        """
        self.embeddings = embeddings
        logger.debug("ConfidenceScorer initialized")

    def calculate_confidence(
        self,
        query: str,
        answer: str,
        documents: List[Any],
        retrieval_scores: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate confidence score for an answer.

        Args:
            query: User's query
            answer: Generated answer
            documents: Retrieved documents
            retrieval_scores: Relevance scores for documents

        Returns:
            Dict with overall score, interpretation, and signal breakdown
        """
        signals = {}

        # Signal 1: Retrieval quality (30% weight)
        if retrieval_scores:
            avg_score = np.mean(retrieval_scores[:3])  # Top 3 docs
            signals["retrieval_quality"] = min(100, avg_score * 100)
        else:
            signals["retrieval_quality"] = 0

        # Signal 2: Answer completeness (30% weight)
        signals["answer_completeness"] = self._score_completeness(answer, query)

        # Signal 3: Semantic alignment (25% weight)
        if self.embeddings and documents:
            signals["semantic_alignment"] = self._score_alignment(
                answer, documents[:3]
            )
        else:
            signals["semantic_alignment"] = 50  # Neutral if can't compute

        # Signal 4: Consistency (15% weight)
        signals["consistency"] = self._score_consistency(answer, documents)

        # Weighted average
        overall_score = (
            signals["retrieval_quality"] * 0.30 +
            signals["answer_completeness"] * 0.30 +
            signals["semantic_alignment"] * 0.25 +
            signals["consistency"] * 0.15
        )

        # Interpretation
        interpretation = self._interpret_score(overall_score)

        logger.debug(
            f"Confidence: {overall_score:.1f} ({interpretation}) - "
            f"R={signals['retrieval_quality']:.0f} "
            f"C={signals['answer_completeness']:.0f} "
            f"A={signals['semantic_alignment']:.0f} "
            f"X={signals['consistency']:.0f}"
        )

        return {
            "overall": overall_score,
            "interpretation": interpretation,
            "signals": signals
        }

    def _score_completeness(self, answer: str, query: str) -> float:
        """
        Score answer completeness based on length and specificity.

        Args:
            answer: Generated answer
            query: User query

        Returns:
            Completeness score 0-100
        """
        # Length score (longer = more complete, up to a point)
        word_count = len(answer.split())

        if word_count < 10:
            length_score = word_count * 5  # Very short answers penalized
        elif word_count < 50:
            length_score = 50 + (word_count - 10)  # Normal range
        else:
            length_score = min(100, 90 + (word_count - 50) * 0.2)  # Diminishing returns

        # Specificity score (mentions numbers, names, specific terms)
        specificity_score = 50

        # Has numbers
        if any(char.isdigit() for char in answer):
            specificity_score += 15

        # Has proper nouns (capitalized words mid-sentence)
        words = answer.split()
        if len(words) > 3:
            capitalized = sum(1 for w in words[1:-1] if w and w[0].isupper())
            if capitalized > 0:
                specificity_score += min(20, capitalized * 5)

        # Has citations (like [1] [2])
        if '[' in answer and ']' in answer:
            specificity_score += 15

        # Weighted average
        completeness = length_score * 0.6 + specificity_score * 0.4

        return min(100, completeness)

    def _score_alignment(self, answer: str, documents: List[Any]) -> float:
        """
        Score semantic alignment between answer and source documents.

        Args:
            answer: Generated answer
            documents: Source documents

        Returns:
            Alignment score 0-100
        """
        try:
            if not self.embeddings or not documents:
                return 50  # Neutral

            # Get answer embedding
            answer_embedding = self.embeddings.embed_query(answer)

            # Get document embeddings and compare
            similarities = []
            for doc in documents[:3]:  # Top 3 docs
                doc_embedding = self.embeddings.embed_query(doc.page_content[:500])

                # Cosine similarity
                similarity = np.dot(answer_embedding, doc_embedding) / (
                    np.linalg.norm(answer_embedding) * np.linalg.norm(doc_embedding)
                )
                similarities.append(similarity)

            # Average similarity, convert to 0-100 scale
            avg_similarity = np.mean(similarities)
            # Similarity is typically 0.3-0.9, map to 0-100
            score = min(100, max(0, (avg_similarity - 0.3) / 0.6 * 100))

            return score

        except Exception as e:
            logger.warning(f"Alignment scoring failed: {e}")
            return 50  # Neutral on error

    def _score_consistency(self, answer: str, documents: List[Any]) -> float:
        """
        Score consistency based on cross-document agreement.

        Args:
            answer: Generated answer
            documents: Source documents

        Returns:
            Consistency score 0-100
        """
        # Simple heuristic: more documents = more confidence in answer
        num_docs = len(documents)

        if num_docs >= 5:
            return 100  # Multiple sources confirm
        elif num_docs >= 3:
            return 80   # Good support
        elif num_docs >= 2:
            return 60   # Some support
        elif num_docs >= 1:
            return 40   # Single source
        else:
            return 20   # No sources

    def _interpret_score(self, score: float) -> str:
        """Interpret numerical score"""
        if score >= 85:
            return "very_high"
        elif score >= 60:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"
