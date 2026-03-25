"""
Forge - Ingestion Pipeline Orchestrator

Full pipeline: parse -> chunk -> contextualize -> extract propositions
-> build graph -> embed with BGE-M3 -> upsert to Qdrant.

Provides progress reporting for the /api/ingest/status endpoint.
"""

import logging
import time
import uuid
from typing import List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from forge.ingestion.parser import DocumentParser, DocumentTree
from forge.ingestion.chunker import HierarchicalChunker, ChunkData
from forge.ingestion.contextual import ContextualEnricher
from forge.ingestion.propositions import PropositionExtractor
from forge.ingestion.graph import GraphBuilder

logger = logging.getLogger(__name__)


@dataclass
class IngestProgress:
    """Tracks ingestion pipeline progress."""
    status: str = "idle"  # idle | running | completed | failed
    progress: float = 0.0
    current_document: Optional[str] = None
    documents_total: int = 0
    documents_completed: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class ForgeIndexer:
    """
    Orchestrates the full ingestion pipeline for a list of documents.
    """

    def __init__(self, container):
        """
        Args:
            container: ServiceContainer providing embeddings, vectorstore,
                       llm, cache, and config.
        """
        self.container = container
        self.progress = IngestProgress()
        self._parser = DocumentParser()

    async def ingest_documents(self, file_paths: List[str]) -> IngestProgress:
        """
        Run the full ingestion pipeline on a list of file paths.

        Returns IngestProgress with final status.
        """
        self.progress = IngestProgress(
            status="running",
            documents_total=len(file_paths),
            started_at=datetime.utcnow().isoformat(),
        )

        config = self.container.config
        embeddings_svc = await self.container.get_embeddings()
        vectorstore = await self.container.get_vectorstore()
        llm = await self.container.get_llm()

        # Redis client for graph adjacency (optional)
        redis_client = None
        try:
            cache = await self.container.get_cache()
            redis_client = cache.client
        except Exception:
            logger.warning("Redis unavailable — graph adjacency disabled")

        # Build pipeline components
        chunker = HierarchicalChunker(
            llm=llm,
            embed_fn=self._make_sync_embed(embeddings_svc),
            min_chunk_size=config.semantic_chunking.min_chunk_size,
            max_chunk_size=config.semantic_chunking.max_chunk_size,
            breakpoint_threshold=config.semantic_chunking.breakpoint_threshold,
            buffer_size=config.semantic_chunking.buffer_size,
        )
        enricher = ContextualEnricher(
            llm=llm if config.contextual_retrieval.enable else None,
            batch_size=config.contextual_retrieval.batch_size,
        )
        prop_extractor = PropositionExtractor(
            llm=llm if config.propositions.enable else None,
            max_propositions=config.propositions.max_propositions_per_chunk,
        )
        graph_builder = GraphBuilder(
            llm=llm if config.graph.enable else None,
            redis_client=redis_client,
            entity_types=config.graph.entity_types,
            relationship_types=config.graph.relationship_types,
            max_entities=config.graph.max_entities_per_chunk,
            max_relationships=config.graph.max_relationships_per_chunk,
        )

        for i, fpath in enumerate(file_paths):
            self.progress.current_document = fpath
            try:
                await self._ingest_one(
                    fpath, chunker, enricher, prop_extractor,
                    graph_builder, embeddings_svc, vectorstore,
                )
                self.progress.documents_completed += 1
            except Exception as e:
                msg = f"{fpath}: {e}"
                logger.error(f"Ingest failed — {msg}", exc_info=True)
                self.progress.errors.append(msg)

            self.progress.progress = (i + 1) / len(file_paths)

        self.progress.status = "completed" if not self.progress.errors else "completed"
        self.progress.completed_at = datetime.utcnow().isoformat()
        self.progress.current_document = None
        logger.info(
            f"Ingestion complete: {self.progress.documents_completed}/{self.progress.documents_total} "
            f"documents, {len(self.progress.errors)} errors"
        )
        return self.progress

    async def _ingest_one(
        self,
        file_path: str,
        chunker: HierarchicalChunker,
        enricher: ContextualEnricher,
        prop_extractor: PropositionExtractor,
        graph_builder: GraphBuilder,
        embeddings_svc,
        vectorstore,
    ):
        start = time.perf_counter()
        logger.info(f"Ingesting: {file_path}")

        # 1. Parse
        tree: DocumentTree = self._parser.parse(file_path)

        # 2. Chunk (L0, L1, L2)
        chunks: List[ChunkData] = await chunker.chunk_document(tree)

        # 3. Contextual enrichment (L2)
        chunks = await enricher.enrich(chunks, tree.raw_text)

        # 4. Proposition extraction (L3)
        chunks = await prop_extractor.extract(chunks)

        # 5. Knowledge graph
        chunks = await graph_builder.build(chunks)

        # 6. Embed with BGE-M3
        texts = [c.content for c in chunks]
        embed_results = await embeddings_svc.embed_documents(texts, return_colbert=True)

        # 7. Build Qdrant points and upsert
        points = []
        for idx, chunk in enumerate(chunks):
            payload = {
                "level": chunk.level,
                "content": chunk.content,
                "original_content": chunk.metadata.get("original_content", chunk.content),
                "context_prefix": chunk.metadata.get("context_prefix", ""),
                "parent_id": chunk.parent_id or "",
                "document_id": chunk.document_id,
                "section_path": chunk.section_path,
                "file_name": chunk.file_name,
                "file_type": chunk.file_type,
                "chunk_index": chunk.chunk_index,
                "propositions": [],
                "entities": chunk.metadata.get("entities", []),
                "relationships": chunk.metadata.get("relationships", []),
                "indexed_at": datetime.utcnow().isoformat(),
            }

            # For L2 chunks, attach their L3 propositions as payload field
            if chunk.level == "L2":
                child_props = [
                    c.content for c in chunks
                    if c.level == "L3" and c.parent_id == chunk.id
                ]
                payload["propositions"] = child_props

            point = {
                "id": chunk.id,
                "dense": embed_results["dense"][idx].tolist()
                    if hasattr(embed_results["dense"][idx], "tolist")
                    else list(embed_results["dense"][idx]),
                "sparse": embed_results["sparse"][idx],
                "colbert": embed_results["colbert"][idx],
                "payload": payload,
            }
            points.append(point)

        await vectorstore.upsert_points(points)

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            f"Ingested {tree.file_name}: {len(chunks)} chunks "
            f"({len([c for c in chunks if c.level == 'L3'])} propositions) "
            f"in {elapsed:.0f}ms"
        )

    @staticmethod
    def _make_sync_embed(embeddings_svc) -> Callable:
        """Create a sync embedding function for the chunker's L2 semantic splitting."""
        def _embed(texts: List[str]) -> List[List[float]]:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run,
                            embeddings_svc.embed_documents(texts, return_colbert=False),
                        )
                        result = future.result()
                else:
                    result = asyncio.run(
                        embeddings_svc.embed_documents(texts, return_colbert=False),
                    )
            except RuntimeError:
                result = asyncio.run(
                    embeddings_svc.embed_documents(texts, return_colbert=False),
                )
            return [v.tolist() if hasattr(v, "tolist") else list(v) for v in result["dense"]]
        return _embed
