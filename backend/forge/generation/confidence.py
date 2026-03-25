"""
Forge - Enhanced Multi-Signal Confidence Scoring

Adapted from _src/confidence_scoring.py with two new signals:
  - CRAG quality (average CRAG score of approved documents)
  - Verification coverage (percentage of claims that are supported)

Weights:
  retrieval  25%  |  completeness  20%  |  alignment  20%
  consistency 10% |  crag_quality  15%  |  verification 10%
"""

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ForgeConfidenceScorer:
    """
    Enhanced confidence scorer with 6 signals.

    Score interpretation:
      0-30:  low  (likely hallucination)
      30-60: medium (partial information)
      60-85: high (good answer)
      85-100: very_high (excellent answer)
    """

    def __init__(self, embeddings=None):
        self.embeddings = embeddings

    def calculate(
        self,
        query: str,
        answer: str,
        documents: list[Any],
        retrieval_scores: list[float],
        crag_scores: list[float] | None = None,
        verification_results: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Calculate overall confidence.

        Args:
            query: User query.
            answer: Generated answer.
            documents: Source documents used.
            retrieval_scores: Relevance scores for top docs.
            crag_scores: CRAG evaluator scores (0-1 each).
            verification_results: List of dicts with 'supported' bool.

        Returns:
            Dict with overall score, interpretation, and signal breakdown.
        """
        signals: dict[str, float] = {}

        # Signal 1: Retrieval quality (25%)
        if retrieval_scores:
            avg = float(np.mean(retrieval_scores[:5]))
            signals["retrieval_quality"] = min(100.0, avg * 100)
        else:
            signals["retrieval_quality"] = 0.0

        # Signal 2: Answer completeness (20%)
        signals["answer_completeness"] = self._score_completeness(answer, query)

        # Signal 3: Semantic alignment (20%)
        if self.embeddings and documents:
            signals["semantic_alignment"] = self._score_alignment(answer, documents[:3])
        else:
            signals["semantic_alignment"] = 50.0

        # Signal 4: Consistency (10%)
        signals["consistency"] = self._score_consistency(answer, documents)

        # Signal 5: CRAG quality (15%) -- NEW
        if crag_scores:
            avg_crag = float(np.mean(crag_scores))
            signals["crag_quality"] = min(100.0, avg_crag * 100)
        else:
            signals["crag_quality"] = 50.0  # neutral when unavailable

        # Signal 6: Verification coverage (10%) -- NEW
        if verification_results:
            total = len(verification_results)
            supported = sum(1 for v in verification_results if v.get("supported"))
            signals["verification_coverage"] = (supported / total) * 100 if total else 50.0
        else:
            signals["verification_coverage"] = 50.0

        # Weighted combination
        overall = (
            signals["retrieval_quality"] * 0.25
            + signals["answer_completeness"] * 0.20
            + signals["semantic_alignment"] * 0.20
            + signals["consistency"] * 0.10
            + signals["crag_quality"] * 0.15
            + signals["verification_coverage"] * 0.10
        )

        interpretation = self._interpret(overall)

        logger.debug(
            f"Confidence: {overall:.1f} ({interpretation}) — "
            f"R={signals['retrieval_quality']:.0f} "
            f"C={signals['answer_completeness']:.0f} "
            f"A={signals['semantic_alignment']:.0f} "
            f"X={signals['consistency']:.0f} "
            f"Q={signals['crag_quality']:.0f} "
            f"V={signals['verification_coverage']:.0f}"
        )

        return {
            "overall": overall,
            "interpretation": interpretation,
            "signals": signals,
        }

    # ------------------------------------------------------------------
    # Private signal calculators (adapted from existing ConfidenceScorer)
    # ------------------------------------------------------------------

    def _score_completeness(self, answer: str, query: str) -> float:
        word_count = len(answer.split())

        if word_count < 10:
            length_score = word_count * 5.0
        elif word_count < 50:
            length_score = 50.0 + (word_count - 10)
        else:
            length_score = min(100.0, 90.0 + (word_count - 50) * 0.2)

        specificity = 50.0
        if any(c.isdigit() for c in answer):
            specificity += 15.0
        words = answer.split()
        if len(words) > 3:
            caps = sum(1 for w in words[1:-1] if w and w[0].isupper())
            specificity += min(20.0, caps * 5.0)
        if "[" in answer and "]" in answer:
            specificity += 15.0

        return min(100.0, length_score * 0.6 + specificity * 0.4)

    def _score_alignment(self, answer: str, documents: list[Any]) -> float:
        try:
            if not self.embeddings or not documents:
                return 50.0

            answer_emb = self.embeddings.embed_query(answer)

            similarities: list[float] = []
            for doc in documents[:3]:
                text = doc.page_content[:500] if hasattr(doc, "page_content") else str(doc)[:500]
                doc_emb = self.embeddings.embed_query(text)
                sim = float(
                    np.dot(answer_emb, doc_emb)
                    / (np.linalg.norm(answer_emb) * np.linalg.norm(doc_emb) + 1e-9)
                )
                similarities.append(sim)

            avg = float(np.mean(similarities))
            return min(100.0, max(0.0, (avg - 0.3) / 0.6 * 100))

        except Exception as e:
            logger.warning(f"Alignment scoring failed: {e}")
            return 50.0

    def _score_consistency(self, answer: str, documents: list[Any]) -> float:
        n = len(documents)
        if n >= 5:
            return 100.0
        if n >= 3:
            return 80.0
        if n >= 2:
            return 60.0
        if n >= 1:
            return 40.0
        return 20.0

    @staticmethod
    def _interpret(score: float) -> str:
        if score >= 85:
            return "very_high"
        if score >= 60:
            return "high"
        if score >= 30:
            return "medium"
        return "low"
