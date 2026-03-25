"""
Forge - ColBERT + Cross-Encoder Reranker

Primary: ColBERT late-interaction via Qdrant multi-vector MaxSim scoring.
Fallback: Cross-encoder when ColBERT vectors are unavailable.
"""

import logging
import os
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Lazy cross-encoder singleton (shared with CRAG module via same pattern)
_cross_encoder = None


def _get_cross_encoder(model_name: str):
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder

        device = "cpu" if os.getenv("FORCE_TORCH_CPU") == "1" else "cpu"
        _cross_encoder = CrossEncoder(model_name, device=device)
        logger.info(f"[Reranker] CrossEncoder loaded: {model_name} (device={device})")
    return _cross_encoder


@dataclass
class RankedDocument:
    """A document with its reranking score."""
    content: str
    score: float
    metadata: dict
    id: str = ""
    colbert_score: float | None = None
    cross_encoder_score: float | None = None


class ForgeReranker:
    """
    Two-stage reranker: ColBERT MaxSim (primary) + cross-encoder (fallback).

    ColBERT late-interaction scoring uses multi-vectors stored in Qdrant.
    When ColBERT vectors are not available for a document, falls back to
    the cross-encoder model.

    Args:
        cross_encoder_model: Model identifier for cross-encoder fallback.
        colbert_weight: Weight for ColBERT score in combined scoring (0-1).
        container: ServiceContainer for vectorstore access.
    """

    def __init__(
        self,
        cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2",
        colbert_weight: float = 0.6,
        container=None,
    ):
        self.cross_encoder_model = cross_encoder_model
        self.colbert_weight = colbert_weight
        self.container = container

    async def rerank(
        self, query: str, documents: list[dict], k: int = 8
    ) -> list[RankedDocument]:
        """
        Rerank documents using ColBERT MaxSim with cross-encoder fallback.

        Args:
            query: The user query.
            documents: Retrieved documents with content, metadata, id.
            k: Number of top documents to return.

        Returns:
            Top-k RankedDocument instances sorted by final score.
        """
        if not documents:
            return []

        start = time.perf_counter()

        # ------------------------------------------------------------------
        # Stage 1: Try ColBERT MaxSim via Qdrant
        # ------------------------------------------------------------------
        colbert_scores: dict[str, float] = {}
        colbert_available = False

        if self.container:
            try:
                vectorstore = await self.container.get_vectorstore()
                embeddings = await self.container.get_embeddings()

                query_colbert = await embeddings.embed_colbert(query)

                if query_colbert is not None:
                    doc_ids = [
                        d.get("id", "") for d in documents if d.get("id")
                    ]
                    if doc_ids:
                        scores = await vectorstore.colbert_rescore(
                            query_colbert=query_colbert,
                            point_ids=doc_ids,
                        )
                        colbert_scores = scores or {}
                        colbert_available = bool(colbert_scores)

            except Exception as e:
                logger.warning(f"[Reranker] ColBERT scoring failed, using fallback: {e}")

        # ------------------------------------------------------------------
        # Stage 2: Cross-encoder scoring (always run as fallback / complement)
        # ------------------------------------------------------------------
        cross_encoder = _get_cross_encoder(self.cross_encoder_model)

        pairs = [
            (query, doc.get("content", "")[:1500])
            for doc in documents
        ]
        import numpy as np

        raw_scores = cross_encoder.predict(pairs)
        ce_scores = 1.0 / (1.0 + np.exp(-np.array(raw_scores)))

        # ------------------------------------------------------------------
        # Combine scores
        # ------------------------------------------------------------------
        ranked: list[RankedDocument] = []

        for doc, ce_score in zip(documents, ce_scores):
            doc_id = doc.get("id", "")
            ce_f = float(ce_score)

            cb_f = colbert_scores.get(doc_id)

            if cb_f is not None and colbert_available:
                final_score = (
                    self.colbert_weight * cb_f
                    + (1 - self.colbert_weight) * ce_f
                )
            else:
                final_score = ce_f

            ranked.append(RankedDocument(
                content=doc.get("content", ""),
                score=final_score,
                metadata=doc.get("metadata", {}),
                id=doc_id,
                colbert_score=cb_f,
                cross_encoder_score=ce_f,
            ))

        ranked.sort(key=lambda r: r.score, reverse=True)
        ranked = ranked[:k]

        elapsed_ms = (time.perf_counter() - start) * 1000
        method = "colbert+ce" if colbert_available else "cross-encoder"
        logger.info(
            f"[Reranker] method={method} input={len(documents)} output={len(ranked)} "
            f"top_score={ranked[0].score:.4f} time={elapsed_ms:.1f}ms"
        )

        return ranked
