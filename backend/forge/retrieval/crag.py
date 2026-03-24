"""
Forge - CRAG (Corrective RAG) Quality Gate

Evaluates retrieved documents for relevance using a cross-encoder model,
classifying each as CORRECT / AMBIGUOUS / INCORRECT. Ambiguous documents
get expanded to their parent section. If too few survive, the agent is
instructed to re-retrieve.
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy cross-encoder singleton
_cross_encoder = None


def _get_cross_encoder(model_name: str):
    """Lazy-load the cross-encoder (CPU only to leave GPU for LLM)."""
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder

        device = "cpu" if os.getenv("FORCE_TORCH_CPU") == "1" else "cpu"
        _cross_encoder = CrossEncoder(model_name, device=device)
        logger.info(f"[CRAG] CrossEncoder loaded: {model_name} (device={device})")
    return _cross_encoder


@dataclass
class CRAGResult:
    """Result of a single document evaluation."""
    doc_id: str
    score: float
    verdict: str  # "correct" | "ambiguous" | "incorrect"
    content: str = ""
    metadata: dict | None = None
    expanded: bool = False  # True if replaced with parent content


class CRAGEvaluator:
    """
    CRAG Quality Gate.

    Uses a cross-encoder to score query-document relevance:
    - CORRECT   (score >= threshold_correct):  keep as-is
    - AMBIGUOUS (threshold_ambiguous <= score < threshold_correct): expand to parent
    - INCORRECT (score < threshold_ambiguous):  discard

    Args:
        model_name: Cross-encoder model identifier.
        threshold_correct: Minimum score to accept outright.
        threshold_ambiguous: Minimum score for ambiguous (below = incorrect).
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2",
        threshold_correct: float = 0.7,
        threshold_ambiguous: float = 0.3,
        container=None,
    ):
        self.model_name = model_name
        self.threshold_correct = threshold_correct
        self.threshold_ambiguous = threshold_ambiguous
        self.container = container

    async def evaluate(
        self, query: str, documents: list[dict]
    ) -> list[CRAGResult]:
        """
        Evaluate and filter a list of retrieved documents.

        Args:
            query: The user query.
            documents: List of dicts with at least 'content' and 'id' keys.

        Returns:
            Ordered list of CRAGResult (correct first, then expanded ambiguous).
        """
        if not documents:
            return []

        start = time.perf_counter()

        # ------------------------------------------------------------------
        # Score every document with cross-encoder
        # ------------------------------------------------------------------
        cross_encoder = _get_cross_encoder(self.model_name)

        pairs = [
            (query, doc.get("content", "")[:1500])
            for doc in documents
        ]

        raw_scores = cross_encoder.predict(pairs)

        # Normalise to 0-1 via sigmoid if model outputs logits
        import numpy as np

        scores = 1.0 / (1.0 + np.exp(-np.array(raw_scores)))

        # ------------------------------------------------------------------
        # Classify each document
        # ------------------------------------------------------------------
        correct: list[CRAGResult] = []
        ambiguous: list[CRAGResult] = []
        incorrect_count = 0

        for doc, score in zip(documents, scores):
            score_f = float(score)
            doc_id = doc.get("id", doc.get("metadata", {}).get("id", "unknown"))

            if score_f >= self.threshold_correct:
                verdict = "correct"
                correct.append(CRAGResult(
                    doc_id=doc_id,
                    score=score_f,
                    verdict=verdict,
                    content=doc.get("content", ""),
                    metadata=doc.get("metadata", {}),
                ))
            elif score_f >= self.threshold_ambiguous:
                verdict = "ambiguous"
                ambiguous.append(CRAGResult(
                    doc_id=doc_id,
                    score=score_f,
                    verdict=verdict,
                    content=doc.get("content", ""),
                    metadata=doc.get("metadata", {}),
                ))
            else:
                incorrect_count += 1

        # ------------------------------------------------------------------
        # Expand ambiguous docs to parent section
        # ------------------------------------------------------------------
        if ambiguous and self.container:
            try:
                vectorstore = await self.container.get_vectorstore()
                for result in ambiguous:
                    parent_id = (result.metadata or {}).get("parent_id")
                    if parent_id:
                        parent = await vectorstore.get_by_id(parent_id)
                        if parent:
                            result.content = parent.get("content", result.content)
                            result.expanded = True
            except Exception as e:
                logger.warning(f"[CRAG] Parent expansion failed: {e}")

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"[CRAG] evaluated {len(documents)} docs in {elapsed_ms:.1f}ms — "
            f"correct={len(correct)} ambiguous={len(ambiguous)} "
            f"incorrect={incorrect_count}"
        )

        # Return correct first, then expanded ambiguous
        return correct + ambiguous
