"""
Forge - Hierarchical Chunker

Produces 4 levels:
  L0: LLM-generated full document summary (200-300 words)
  L1: LLM-generated section summaries (50-100 words each)
  L2: Semantic chunking within sections (200-2000 chars, similarity-based)
  L3: Placeholder — propositions added by propositions.py
"""

import logging
import re
import uuid
from typing import List, Optional
from dataclasses import dataclass, field

import numpy as np

from forge.ingestion.parser import DocumentTree, Section

logger = logging.getLogger(__name__)


@dataclass
class ChunkData:
    """A single chunk produced by the hierarchical chunker."""
    id: str = ""
    level: str = "L2"  # L0 | L1 | L2 | L3
    content: str = ""
    parent_id: Optional[str] = None
    document_id: str = ""
    section_path: str = ""
    file_name: str = ""
    file_type: str = ""
    chunk_index: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


class HierarchicalChunker:
    """
    Produces L0, L1, L2 chunks from a DocumentTree.

    Requires:
        llm   — for L0/L1 summarization (invoke(prompt) -> str)
        embed_fn — callable(texts: list[str]) -> list[list[float]]  for L2 semantic splitting
    """

    def __init__(
        self,
        llm=None,
        embed_fn=None,
        min_chunk_size: int = 200,
        max_chunk_size: int = 2000,
        breakpoint_threshold: float = 0.75,
        buffer_size: int = 1,
    ):
        self.llm = llm
        self.embed_fn = embed_fn
        self.min_chunk = min_chunk_size
        self.max_chunk = max_chunk_size
        self.bp_threshold = breakpoint_threshold
        self.buffer_size = buffer_size

    async def chunk_document(self, tree: DocumentTree) -> List[ChunkData]:
        """Produce L0 + L1 + L2 chunks from a parsed DocumentTree."""
        doc_id = str(uuid.uuid4())
        chunks: List[ChunkData] = []
        idx = 0

        # --- L0: full-document summary ---
        l0_chunk = await self._make_l0(tree, doc_id)
        l0_chunk.chunk_index = idx
        chunks.append(l0_chunk)
        idx += 1

        # --- L1 + L2 per section (recursively) ---
        for sec in tree.sections:
            sec_chunks, idx = await self._process_section(
                sec, doc_id, tree.file_name, tree.file_type,
                path_prefix="", parent_id=l0_chunk.id, idx=idx,
            )
            chunks.extend(sec_chunks)

        logger.info(f"Chunked '{tree.file_name}': {len(chunks)} total chunks (L0/L1/L2)")
        return chunks

    # ------------------------------------------------------------------
    # L0 — Document summary
    # ------------------------------------------------------------------

    async def _make_l0(self, tree: DocumentTree, doc_id: str) -> ChunkData:
        raw_excerpt = tree.raw_text[:6000]
        if self.llm:
            prompt = (
                "Summarize the following document in 200-300 words. "
                "Focus on the main topics, purpose, and key requirements.\n\n"
                f"Document: {tree.file_name}\n\n{raw_excerpt}\n\nSummary:"
            )
            try:
                summary = await self._invoke_llm(prompt)
            except Exception as e:
                logger.warning(f"L0 summarization failed: {e}")
                summary = raw_excerpt[:1000]
        else:
            summary = raw_excerpt[:1000]

        return ChunkData(
            level="L0",
            content=summary,
            document_id=doc_id,
            section_path="Full Document",
            file_name=tree.file_name,
            file_type=tree.file_type,
        )

    # ------------------------------------------------------------------
    # L1 + L2 — Section summaries + semantic chunks
    # ------------------------------------------------------------------

    async def _process_section(
        self,
        section: Section,
        doc_id: str,
        file_name: str,
        file_type: str,
        path_prefix: str,
        parent_id: str,
        idx: int,
    ) -> tuple[List[ChunkData], int]:
        chunks: List[ChunkData] = []
        section_path = f"{path_prefix} > {section.heading}".strip(" > ")

        # L1 summary
        l1_chunk = await self._make_l1(
            section, doc_id, file_name, file_type, section_path, parent_id,
        )
        l1_chunk.chunk_index = idx
        chunks.append(l1_chunk)
        idx += 1

        # L2 semantic chunks from this section's own content
        if section.content.strip():
            l2_chunks = self._make_l2(
                section.content, doc_id, file_name, file_type,
                section_path, l1_chunk.id,
            )
            for c in l2_chunks:
                c.chunk_index = idx
                idx += 1
            chunks.extend(l2_chunks)

        # Recurse into subsections
        for sub in section.subsections:
            sub_chunks, idx = await self._process_section(
                sub, doc_id, file_name, file_type,
                section_path, l1_chunk.id, idx,
            )
            chunks.extend(sub_chunks)

        return chunks, idx

    async def _make_l1(
        self, section: Section, doc_id, file_name, file_type, section_path, parent_id,
    ) -> ChunkData:
        text = section.content[:3000] if section.content else section.heading
        if self.llm:
            prompt = (
                "Summarize this document section in 50-100 words. "
                f"Section: {section.heading}\n\n{text}\n\nSummary:"
            )
            try:
                summary = await self._invoke_llm(prompt)
            except Exception as e:
                logger.warning(f"L1 summarization failed: {e}")
                summary = text[:500]
        else:
            summary = text[:500]

        return ChunkData(
            level="L1",
            content=summary,
            parent_id=parent_id,
            document_id=doc_id,
            section_path=section_path,
            file_name=file_name,
            file_type=file_type,
        )

    # ------------------------------------------------------------------
    # L2 — Semantic chunking (adapted from _src/semantic_chunking.py)
    # ------------------------------------------------------------------

    def _make_l2(
        self, text: str, doc_id, file_name, file_type, section_path, parent_id,
    ) -> List[ChunkData]:
        """Split section text into semantic chunks."""
        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            if len(text) > self.min_chunk:
                return [ChunkData(
                    level="L2", content=text, parent_id=parent_id,
                    document_id=doc_id, section_path=section_path,
                    file_name=file_name, file_type=file_type,
                )]
            return []

        # If no embedding function, fall back to size-based splitting
        if not self.embed_fn:
            return self._size_based_split(
                text, doc_id, file_name, file_type, section_path, parent_id,
            )

        # Semantic splitting via embedding similarity
        groups = self._sentence_groups(sentences)
        try:
            embeddings = self.embed_fn(groups)
        except Exception:
            return self._size_based_split(
                text, doc_id, file_name, file_type, section_path, parent_id,
            )

        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine(embeddings[i], embeddings[i + 1])
            similarities.append(sim)

        breakpoints = self._find_breakpoints(similarities)

        raw_chunks = self._sentences_to_chunks(sentences, breakpoints)
        # Enforce min/max size
        final = self._enforce_sizes(raw_chunks)

        return [
            ChunkData(
                level="L2", content=c, parent_id=parent_id,
                document_id=doc_id, section_path=section_path,
                file_name=file_name, file_type=file_type,
            )
            for c in final if len(c) >= self.min_chunk
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in parts if s.strip()]

    def _sentence_groups(self, sentences: List[str]) -> List[str]:
        groups = []
        for i in range(len(sentences)):
            start = max(0, i - self.buffer_size)
            end = min(len(sentences), i + self.buffer_size + 1)
            groups.append(" ".join(sentences[start:end]))
        return groups

    @staticmethod
    def _cosine(a, b) -> float:
        a, b = np.array(a), np.array(b)
        n1, n2 = np.linalg.norm(a), np.linalg.norm(b)
        if n1 == 0 or n2 == 0:
            return 0.0
        return float(np.dot(a, b) / (n1 * n2))

    def _find_breakpoints(self, similarities: List[float]) -> List[int]:
        if not similarities:
            return []
        arr = np.array(similarities)
        threshold = np.percentile(arr, (1 - self.bp_threshold) * 100)
        return [i + 1 for i, s in enumerate(similarities) if s < threshold]

    @staticmethod
    def _sentences_to_chunks(sentences: List[str], breakpoints: List[int]) -> List[str]:
        chunks = []
        start = 0
        for bp in breakpoints:
            if bp > start:
                chunks.append(" ".join(sentences[start:bp]))
                start = bp
        if start < len(sentences):
            chunks.append(" ".join(sentences[start:]))
        return chunks

    def _enforce_sizes(self, chunks: List[str]) -> List[str]:
        result: List[str] = []
        for c in chunks:
            if len(c) > self.max_chunk:
                # Split oversized
                pos = 0
                while pos < len(c):
                    result.append(c[pos:pos + self.max_chunk])
                    pos += self.max_chunk
            elif len(c) < self.min_chunk and result:
                merged = result[-1] + " " + c
                if len(merged) <= self.max_chunk:
                    result[-1] = merged
                else:
                    result.append(c)
            else:
                result.append(c)
        return result

    def _size_based_split(
        self, text, doc_id, file_name, file_type, section_path, parent_id,
    ) -> List[ChunkData]:
        """Simple size-based fallback."""
        chunks = []
        pos = 0
        while pos < len(text):
            end = min(pos + self.max_chunk, len(text))
            segment = text[pos:end]
            if len(segment) >= self.min_chunk:
                chunks.append(ChunkData(
                    level="L2", content=segment, parent_id=parent_id,
                    document_id=doc_id, section_path=section_path,
                    file_name=file_name, file_type=file_type,
                ))
            pos = end
        return chunks

    async def _invoke_llm(self, prompt: str) -> str:
        """Call LLM (sync or async)."""
        if hasattr(self.llm, "ainvoke"):
            return await self.llm.ainvoke(prompt)
        if hasattr(self.llm, "generate"):
            return await self.llm.generate(prompt)
        # Sync fallback
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.llm.invoke, prompt)
