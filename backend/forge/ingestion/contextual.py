"""
Forge - Contextual Retrieval Enrichment (Anthropic technique)

For each L2 chunk, calls the LLM to generate a 50-100 token context prefix
that situates the chunk within the full document and section.
The prefix is prepended to the chunk text before embedding.
"""

import logging
from typing import List, Optional

from forge.ingestion.chunker import ChunkData

logger = logging.getLogger(__name__)

CONTEXT_PROMPT = """\
Given the full document and section context below, write a short context \
(50-100 tokens) that situates this chunk within the document. Include the \
document name, section heading, and what the surrounding sections discuss. \
Do NOT summarize the chunk itself — only provide context.

Document: {file_name}
Section path: {section_path}

Full document excerpt (first 3000 chars):
{doc_excerpt}

Chunk text:
{chunk_text}

Context prefix:"""


class ContextualEnricher:
    """
    Adds a context_prefix to each L2 chunk and prepends it to the
    chunk content before embedding.
    """

    def __init__(self, llm=None, batch_size: int = 10):
        self.llm = llm
        self.batch_size = batch_size

    async def enrich(
        self,
        chunks: List[ChunkData],
        doc_raw_text: str,
    ) -> List[ChunkData]:
        """
        For every L2 chunk, generate and prepend a context prefix.

        Returns the same list (mutated in place) with updated content
        and metadata.context_prefix / metadata.original_content fields.
        """
        if not self.llm:
            logger.warning("No LLM provided — skipping contextual enrichment")
            return chunks

        l2_chunks = [c for c in chunks if c.level == "L2"]
        if not l2_chunks:
            return chunks

        logger.info(f"Enriching {len(l2_chunks)} L2 chunks with context prefixes")
        doc_excerpt = doc_raw_text[:3000]

        for i in range(0, len(l2_chunks), self.batch_size):
            batch = l2_chunks[i:i + self.batch_size]
            for chunk in batch:
                try:
                    prefix = await self._generate_prefix(chunk, doc_excerpt)
                    chunk.metadata["original_content"] = chunk.content
                    chunk.metadata["context_prefix"] = prefix
                    chunk.content = f"{prefix}\n\n{chunk.content}"
                except Exception as e:
                    logger.warning(f"Context prefix failed for chunk {chunk.id}: {e}")

        logger.info(f"Contextual enrichment complete for {len(l2_chunks)} chunks")
        return chunks

    async def _generate_prefix(self, chunk: ChunkData, doc_excerpt: str) -> str:
        prompt = CONTEXT_PROMPT.format(
            file_name=chunk.file_name,
            section_path=chunk.section_path,
            doc_excerpt=doc_excerpt,
            chunk_text=chunk.content[:1000],
        )
        if hasattr(self.llm, "ainvoke"):
            return (await self.llm.ainvoke(prompt)).strip()
        if hasattr(self.llm, "generate"):
            return (await self.llm.generate(prompt)).strip()
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.llm.invoke, prompt)
        return result.strip()
