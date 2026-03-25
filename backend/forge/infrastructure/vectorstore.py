"""
Forge - Qdrant Vector Store with Named Vectors

Rewritten for Qdrant named vectors:
  "dense"   (1024-dim, cosine)
  "sparse"  (BGE-M3 native sparse)
  "colbert" (multi-vector, late-interaction reranking)

Collection: forge_documents (configurable)
HNSW: m=16, ef_construct=128
"""

import logging
import asyncio
import uuid
from typing import List, Dict, Optional, Any

import numpy as np
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    HnswConfigDiff,
    OptimizersConfigDiff,
    Prefetch,
    FusionQuery,
    Fusion,
    Filter,
    FieldCondition,
    MatchValue,
    NamedVector,
    NamedSparseVector,
)

logger = logging.getLogger(__name__)


class ForgeVectorStore:
    """
    Qdrant vector store with dense + sparse + ColBERT named vectors.

    Methods mirror the plan: create_collection, upsert_points, search_dense,
    search_sparse, search_hybrid, rerank_colbert, get_by_id, get_by_parent_id,
    filter_by_level.
    """

    def __init__(
        self,
        collection_name: str = "forge_documents",
        host: str = "localhost",
        port: int = 6333,
        dense_dim: int = 1024,
    ):
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.dense_dim = dense_dim
        self.client: Optional[AsyncQdrantClient] = None
        self.initialized = False

    async def initialize(self, recreate: bool = False) -> bool:
        """Connect to Qdrant and ensure the collection exists."""
        try:
            self.client = AsyncQdrantClient(
                host=self.host, port=self.port, check_compatibility=False,
            )
            await self.client.get_collections()  # connection check

            exists = await self._collection_exists()

            if exists and recreate:
                logger.warning(f"Deleting collection {self.collection_name} (recreate=True)")
                await self.client.delete_collection(self.collection_name)
                exists = False

            if not exists:
                await self._create_collection()

            self.initialized = True
            logger.info(f"Qdrant collection '{self.collection_name}' ready")
            return True

        except Exception as e:
            logger.error(f"Qdrant init failed: {e}", exc_info=True)
            return False

    async def _collection_exists(self) -> bool:
        try:
            return await self.client.collection_exists(self.collection_name)
        except Exception:
            # Fallback for older Qdrant versions
            resp = await self.client.get_collections()
            return self.collection_name in [c.name for c in resp.collections]

    async def _create_collection(self):
        """Create collection with dense + sparse named vectors and HNSW tuning."""

        vectors_config = {
            "dense": VectorParams(size=self.dense_dim, distance=Distance.COSINE),
        }

        sparse_vectors_config = {
            "sparse": SparseVectorParams(),
        }

        # ColBERT multi-vector support requires qdrant-client >=1.12
        # We store ColBERT vectors as a payload field (list of float lists)
        # and do late-interaction scoring client-side — simpler, no schema change.

        hnsw = HnswConfigDiff(
            m=16,
            ef_construct=128,
            full_scan_threshold=10000,
            on_disk=False,
        )

        optimizer = OptimizersConfigDiff(
            deleted_threshold=0.2,
            indexing_threshold=20000,
            flush_interval_sec=5,
        )

        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=vectors_config,
            sparse_vectors_config=sparse_vectors_config,
            hnsw_config=hnsw,
            optimizers_config=optimizer,
            on_disk_payload=False,
        )
        logger.info(f"Created collection '{self.collection_name}' with dense+sparse vectors")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def upsert_points(
        self,
        points: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> int:
        """
        Upsert points into Qdrant.

        Each point dict must have:
            id: str (UUID)
            dense: list[float] (1024-dim)
            sparse: {"indices": [...], "values": [...]}
            payload: dict
        Optionally:
            colbert: list[list[float]] — stored in payload
        """
        self._require_init()
        total = 0

        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            structs = []

            for p in batch:
                point_id = p["id"]
                vectors = {
                    "dense": p["dense"],
                }
                payload = dict(p.get("payload", {}))

                # Store ColBERT vectors in payload for client-side reranking
                if "colbert" in p and p["colbert"] is not None:
                    colbert = p["colbert"]
                    if isinstance(colbert, np.ndarray):
                        colbert = colbert.tolist()
                    payload["_colbert_vecs"] = colbert

                structs.append(PointStruct(
                    id=point_id,
                    vector=vectors,
                    payload=payload,
                ))

                # Sparse vector — add via the named sparse vector field
                sparse_data = p.get("sparse", {})
                if sparse_data.get("indices"):
                    structs[-1].vector["sparse"] = SparseVector(
                        indices=sparse_data["indices"],
                        values=sparse_data["values"],
                    )

            await self.client.upsert(
                collection_name=self.collection_name,
                points=structs,
            )
            total += len(batch)

        logger.info(f"Upserted {total} points to '{self.collection_name}'")
        return total

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_dense(
        self,
        vector: List[float],
        top_k: int = 20,
        query_filter: Optional[Filter] = None,
    ) -> List[Dict[str, Any]]:
        """Dense-only cosine search."""
        self._require_init()
        results = await self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            using="dense",
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        return self._to_dicts(results.points)

    async def search_sparse(
        self,
        sparse_vector: Dict[str, Any],
        top_k: int = 20,
        query_filter: Optional[Filter] = None,
    ) -> List[Dict[str, Any]]:
        """Sparse-only (keyword) search."""
        self._require_init()
        sv = SparseVector(
            indices=sparse_vector["indices"],
            values=sparse_vector["values"],
        )
        results = await self.client.query_points(
            collection_name=self.collection_name,
            query=sv,
            using="sparse",
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        return self._to_dicts(results.points)

    async def search_hybrid(
        self,
        dense_vector: List[float],
        sparse_vector: Dict[str, Any],
        top_k: int = 20,
        dense_limit: int = 40,
        sparse_limit: int = 40,
        query_filter: Optional[Filter] = None,
    ) -> List[Dict[str, Any]]:
        """Hybrid search with RRF fusion over dense + sparse prefetch."""
        self._require_init()
        sv = SparseVector(
            indices=sparse_vector["indices"],
            values=sparse_vector["values"],
        )
        results = await self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(query=dense_vector, using="dense", limit=dense_limit),
                Prefetch(query=sv, using="sparse", limit=sparse_limit),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        return self._to_dicts(results.points)

    async def rerank_colbert(
        self,
        query_colbert: np.ndarray,
        candidates: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Client-side ColBERT MaxSim reranking.

        Args:
            query_colbert: (num_query_tokens, dim) from BGE-M3
            candidates: list of point dicts (must have payload._colbert_vecs)
            top_k: how many to return after reranking
        """
        scored = []
        for cand in candidates:
            doc_vecs = cand.get("payload", {}).get("_colbert_vecs")
            if doc_vecs is None:
                scored.append((cand, cand.get("score", 0.0)))
                continue
            doc_arr = np.array(doc_vecs, dtype=np.float32)
            # MaxSim: for each query token, take max cosine sim to any doc token
            # sim_matrix: (num_query_tokens, num_doc_tokens)
            sim_matrix = query_colbert @ doc_arr.T
            max_sims = sim_matrix.max(axis=1)  # max over doc tokens
            colbert_score = float(max_sims.mean())  # average over query tokens
            scored.append((cand, colbert_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        for cand, score in scored:
            cand["colbert_score"] = score
        return [c for c, _ in scored[:top_k]]

    # ------------------------------------------------------------------
    # Point-level access
    # ------------------------------------------------------------------

    async def get_by_id(self, point_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single point by ID."""
        self._require_init()
        results = await self.client.retrieve(
            collection_name=self.collection_name,
            ids=[point_id],
            with_payload=True,
            with_vectors=False,
        )
        if results:
            p = results[0]
            return {"id": str(p.id), "payload": p.payload, "score": 0.0}
        return None

    async def get_by_parent_id(
        self, parent_id: str, top_k: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get all children of a parent chunk."""
        self._require_init()
        filt = Filter(must=[FieldCondition(key="parent_id", match=MatchValue(value=parent_id))])
        results = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filt,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        points, _ = results
        return [{"id": str(p.id), "payload": p.payload, "score": 0.0} for p in points]

    async def filter_by_level(
        self, level: str, top_k: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get points filtered by level (L0, L1, L2, L3)."""
        self._require_init()
        filt = Filter(must=[FieldCondition(key="level", match=MatchValue(value=level))])
        results = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filt,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        points, _ = results
        return [{"id": str(p.id), "payload": p.payload, "score": 0.0} for p in points]

    # ------------------------------------------------------------------
    # Info & lifecycle
    # ------------------------------------------------------------------

    async def get_collection_info(self) -> Dict[str, Any]:
        self._require_init()
        info = await self.client.get_collection(self.collection_name)
        return {
            "name": self.collection_name,
            "points_count": info.points_count,
            "status": info.status.value,
        }

    async def close(self):
        if self.client and hasattr(self.client, "close"):
            await self.client.close()
        logger.info("Qdrant client closed")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _require_init(self):
        if not self.initialized:
            raise RuntimeError("ForgeVectorStore not initialized")

    @staticmethod
    def _to_dicts(points) -> List[Dict[str, Any]]:
        return [
            {"id": str(p.id), "score": p.score, "payload": p.payload}
            for p in points
        ]
