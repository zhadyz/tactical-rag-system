"""
Forge - BGE-M3 Embedding Service

Single class producing dense, sparse, AND multi-vector (ColBERT) representations
using the FlagEmbedding library. Runs on CPU (~2.3GB RAM).

All three vector types are produced in a single forward pass per text.
"""

import logging
import time
from typing import List, Tuple, Optional, Dict, Any

import numpy as np

logger = logging.getLogger(__name__)


class BGEM3Service:
    """
    BGE-M3 embedding service producing dense + sparse + ColBERT vectors.

    Usage:
        svc = BGEM3Service(model_name="BAAI/bge-m3", device="cpu")
        await svc.initialize()
        dense, sparse, colbert = await svc.embed_query("What is RAG?")
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cpu",
        batch_size: int = 64,
        max_length: int = 8192,
        normalize: bool = True,
        cache=None,
    ):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.max_length = max_length
        self.normalize = normalize
        self.cache = cache  # optional EmbeddingCache / ForgeCache for L3 lookups
        self._model = None

    async def initialize(self) -> bool:
        """Load the BGE-M3 model (blocking, run once at startup)."""
        import asyncio

        def _load():
            from FlagEmbedding import BGEM3FlagModel
            return BGEM3FlagModel(
                self.model_name,
                use_fp16=False,  # CPU — fp16 not beneficial
                device=self.device,
            )

        try:
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(None, _load)
            logger.info(f"BGE-M3 loaded on {self.device} (model={self.model_name})")
            return True
        except Exception as e:
            logger.error(f"Failed to load BGE-M3: {e}", exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed_query(
        self, text: str
    ) -> Tuple[np.ndarray, Dict[str, Any], Optional[np.ndarray]]:
        """
        Embed a single query text.

        Returns:
            (dense_vec, sparse_dict, colbert_vecs)
            - dense_vec: np.ndarray shape (1024,)
            - sparse_dict: {"indices": [...], "values": [...]}
            - colbert_vecs: np.ndarray shape (num_tokens, 1024) or None
        """
        results = await self._encode([text], return_colbert=True)
        dense = results["dense"][0]
        sparse = self._extract_sparse(results["sparse"], 0)
        colbert = results["colbert"][0] if results.get("colbert") is not None else None
        return dense, sparse, colbert

    async def embed_documents(
        self, texts: List[str], return_colbert: bool = True,
    ) -> Dict[str, Any]:
        """
        Embed a batch of document texts.

        Returns dict with keys:
            "dense":   list of np.ndarray (1024,)
            "sparse":  list of {"indices": [...], "values": [...]}
            "colbert": list of np.ndarray (tokens, 1024) or None
        """
        results = await self._encode(texts, return_colbert=return_colbert)
        dense_list = list(results["dense"])
        sparse_list = [
            self._extract_sparse(results["sparse"], i)
            for i in range(len(texts))
        ]
        colbert_list = (
            list(results["colbert"])
            if results.get("colbert") is not None
            else [None] * len(texts)
        )
        return {
            "dense": dense_list,
            "sparse": sparse_list,
            "colbert": colbert_list,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _encode(
        self, texts: List[str], return_colbert: bool = True,
    ) -> Dict[str, Any]:
        """Run the model forward pass in a thread executor."""
        import asyncio

        if self._model is None:
            raise RuntimeError("BGE-M3 not initialized. Call initialize() first.")

        def _run():
            return self._model.encode(
                texts,
                batch_size=self.batch_size,
                max_length=self.max_length,
                return_dense=True,
                return_sparse=True,
                return_colbert_vecs=return_colbert,
            )

        loop = asyncio.get_event_loop()
        start = time.perf_counter()
        output = await loop.run_in_executor(None, _run)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"BGE-M3 encoded {len(texts)} texts in {elapsed:.1f}ms")

        result: Dict[str, Any] = {
            "dense": output["dense_vecs"],
            "sparse": output["lexical_weights"],
        }
        if return_colbert and "colbert_vecs" in output:
            result["colbert"] = output["colbert_vecs"]
        else:
            result["colbert"] = None
        return result

    @staticmethod
    def _extract_sparse(lexical_weights_list, idx: int) -> Dict[str, Any]:
        """Convert FlagEmbedding lexical weights dict to indices/values format."""
        weights = lexical_weights_list[idx]  # dict[token_id -> weight]
        if not weights:
            return {"indices": [], "values": []}
        indices = list(weights.keys())
        values = [float(weights[k]) for k in indices]
        return {"indices": indices, "values": values}
