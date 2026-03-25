"""
Forge - Dense-X Proposition Extraction

For each L2 chunk, calls the LLM to extract atomic, self-contained claims.
Each proposition becomes an L3 point with parent_id linking to its L2 chunk.
"""

import logging
import uuid
import re
from typing import List

from forge.ingestion.chunker import ChunkData

logger = logging.getLogger(__name__)

PROPOSITION_PROMPT = """\
Extract all atomic factual claims from the text below. Each claim should be \
self-contained and understandable without any additional context. Return one \
claim per line, numbered.

Text:
{chunk_text}

Atomic claims:"""


class PropositionExtractor:
    """Extracts L3 proposition chunks from L2 chunks."""

    def __init__(self, llm=None, max_propositions: int = 10):
        self.llm = llm
        self.max_propositions = max_propositions

    async def extract(self, chunks: List[ChunkData]) -> List[ChunkData]:
        """
        For every L2 chunk, extract propositions and return new L3 chunks.

        Returns the full list: original chunks + new L3 chunks appended.
        """
        if not self.llm:
            logger.warning("No LLM — skipping proposition extraction")
            return chunks

        l2_chunks = [c for c in chunks if c.level == "L2"]
        if not l2_chunks:
            return chunks

        logger.info(f"Extracting propositions from {len(l2_chunks)} L2 chunks")
        new_l3: List[ChunkData] = []

        for chunk in l2_chunks:
            try:
                props = await self._extract_propositions(chunk)
                for prop_text in props[:self.max_propositions]:
                    l3 = ChunkData(
                        id=str(uuid.uuid4()),
                        level="L3",
                        content=prop_text,
                        parent_id=chunk.id,
                        document_id=chunk.document_id,
                        section_path=chunk.section_path,
                        file_name=chunk.file_name,
                        file_type=chunk.file_type,
                        metadata={"source_chunk_id": chunk.id},
                    )
                    new_l3.append(l3)
            except Exception as e:
                logger.warning(f"Proposition extraction failed for {chunk.id}: {e}")

        logger.info(f"Extracted {len(new_l3)} L3 propositions")
        return chunks + new_l3

    async def _extract_propositions(self, chunk: ChunkData) -> List[str]:
        # Use original_content if available (pre-contextual text)
        text = chunk.metadata.get("original_content", chunk.content)
        prompt = PROPOSITION_PROMPT.format(chunk_text=text[:2000])

        if hasattr(self.llm, "ainvoke"):
            raw = await self.llm.ainvoke(prompt)
        elif hasattr(self.llm, "generate"):
            raw = await self.llm.generate(prompt)
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(None, self.llm.invoke, prompt)

        return self._parse_propositions(raw)

    @staticmethod
    def _parse_propositions(raw: str) -> List[str]:
        """Parse numbered or bulleted list of propositions."""
        lines = raw.strip().split("\n")
        props = []
        for line in lines:
            # Strip numbering like "1.", "- ", "* ", etc.
            cleaned = re.sub(r"^\s*(?:\d+[.)]\s*|[-*]\s*)", "", line).strip()
            if cleaned and len(cleaned) > 10:
                props.append(cleaned)
        return props
