"""
Forge - Knowledge Graph Construction

Extracts entities and relationships from chunks using the LLM with
structured output parsing.  Stores results in:
  1. Qdrant point payloads (entities + relationships fields)
  2. Redis adjacency list for fast graph traversal
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional

from forge.ingestion.chunker import ChunkData

logger = logging.getLogger(__name__)

GRAPH_PROMPT = """\
Extract entities and relationships from the text below.

Entity types: {entity_types}
Relationship types: {relationship_types}

Return valid JSON with this exact structure:
{{
  "entities": [
    {{"name": "...", "type": "..."}}
  ],
  "relationships": [
    {{"source": "...", "target": "...", "type": "..."}}
  ]
}}

Text:
{chunk_text}

JSON:"""


class GraphBuilder:
    """
    Extracts entities and relationships from chunks and stores them
    as payload fields and in a Redis adjacency list.
    """

    def __init__(
        self,
        llm=None,
        redis_client=None,
        entity_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        max_entities: int = 20,
        max_relationships: int = 30,
    ):
        self.llm = llm
        self.redis = redis_client
        self.entity_types = entity_types or [
            "regulation", "role", "procedure", "requirement",
            "date", "organization", "location", "equipment",
        ]
        self.relationship_types = relationship_types or [
            "authorizes", "requires", "references", "supersedes",
            "applies_to", "defines", "amends",
        ]
        self.max_entities = max_entities
        self.max_rels = max_relationships

    async def build(self, chunks: List[ChunkData]) -> List[ChunkData]:
        """
        For each chunk, extract entities/relationships and store them
        in chunk.metadata["entities"] and chunk.metadata["relationships"].

        Also writes to Redis adjacency list if redis_client is set.
        """
        if not self.llm:
            logger.warning("No LLM — skipping graph construction")
            return chunks

        target_chunks = [c for c in chunks if c.level in ("L1", "L2")]
        logger.info(f"Building knowledge graph from {len(target_chunks)} chunks")

        for chunk in target_chunks:
            try:
                graph_data = await self._extract_graph(chunk)
                entities = graph_data.get("entities", [])[:self.max_entities]
                relationships = graph_data.get("relationships", [])[:self.max_rels]

                chunk.metadata["entities"] = entities
                chunk.metadata["relationships"] = relationships

                # Write adjacency list to Redis
                if self.redis:
                    await self._store_adjacency(entities, relationships, chunk.id)

            except Exception as e:
                logger.warning(f"Graph extraction failed for {chunk.id}: {e}")
                chunk.metadata.setdefault("entities", [])
                chunk.metadata.setdefault("relationships", [])

        logger.info("Knowledge graph construction complete")
        return chunks

    async def _extract_graph(self, chunk: ChunkData) -> Dict[str, Any]:
        text = chunk.metadata.get("original_content", chunk.content)
        prompt = GRAPH_PROMPT.format(
            entity_types=", ".join(self.entity_types),
            relationship_types=", ".join(self.relationship_types),
            chunk_text=text[:2000],
        )

        if hasattr(self.llm, "ainvoke"):
            raw = await self.llm.ainvoke(prompt)
        elif hasattr(self.llm, "generate"):
            raw = await self.llm.generate(prompt)
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(None, self.llm.invoke, prompt)

        return self._parse_json(raw)

    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        """Extract JSON from LLM response (handles markdown fences)."""
        # Try direct parse
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from code fences
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse graph JSON from LLM response")
        return {"entities": [], "relationships": []}

    async def _store_adjacency(
        self,
        entities: List[Dict],
        relationships: List[Dict],
        chunk_id: str,
    ):
        """Store entity adjacency list in Redis for traversal."""
        try:
            for rel in relationships:
                src = rel.get("source", "")
                tgt = rel.get("target", "")
                rel_type = rel.get("type", "related")
                if src and tgt:
                    key = f"forge:graph:{src}"
                    value = json.dumps({
                        "target": tgt,
                        "type": rel_type,
                        "chunk_id": chunk_id,
                    })
                    await self.redis.sadd(key, value)

                    # Reverse edge for bidirectional traversal
                    rkey = f"forge:graph:{tgt}"
                    rvalue = json.dumps({
                        "target": src,
                        "type": f"inverse_{rel_type}",
                        "chunk_id": chunk_id,
                    })
                    await self.redis.sadd(rkey, rvalue)

            # Store entity -> chunk mapping
            for ent in entities:
                name = ent.get("name", "")
                if name:
                    await self.redis.sadd(
                        f"forge:entity_chunks:{name}",
                        chunk_id,
                    )
        except Exception as e:
            logger.warning(f"Redis adjacency store failed: {e}")
