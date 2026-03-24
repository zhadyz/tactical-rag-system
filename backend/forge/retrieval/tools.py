"""
Forge - Agent Tools for Agentic RAG Pipeline

Six LangGraph-compatible tool functions that the agent can invoke
during the retrieval phase. Each tool accesses the ServiceContainer
through a module-level reference set during initialization.
"""

import logging
import time
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level container reference (set via init_tools)
# ---------------------------------------------------------------------------

_container = None


def init_tools(container) -> None:
    """Set the ServiceContainer reference for all tools."""
    global _container
    _container = container


def _require_container():
    if _container is None:
        raise RuntimeError("Tools not initialized. Call init_tools(container) first.")
    return _container


# ---------------------------------------------------------------------------
# Tool 1: Semantic Search (dense + sparse hybrid via BGE-M3)
# ---------------------------------------------------------------------------

@tool
async def semantic_search(query: str, level: str = "L2", k: int = 20) -> list[dict]:
    """Search documents using dense+sparse hybrid via BGE-M3.

    Args:
        query: The search query.
        level: Hierarchy level to filter (L0/L1/L2/L3). Default L2.
        k: Number of results to return.

    Returns:
        List of dicts with content, score, and metadata.
    """
    container = _require_container()
    start = time.perf_counter()

    try:
        vectorstore = await container.get_vectorstore()
        embeddings = await container.get_embeddings()

        # Generate dense + sparse embeddings
        dense_vector = await embeddings.embed_query(query)
        sparse_vector = await embeddings.embed_sparse(query)

        # Hybrid search in Qdrant with level filter
        results = await vectorstore.hybrid_search(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            k=k,
            filters={"level": level},
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"[semantic_search] level={level} k={k} results={len(results)} "
            f"time={elapsed_ms:.1f}ms"
        )

        return [
            {
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
                "metadata": r.get("metadata", {}),
                "id": r.get("id", ""),
            }
            for r in results
        ]

    except Exception as e:
        logger.error(f"[semantic_search] failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Tool 2: Proposition Search (L3 atomic claims)
# ---------------------------------------------------------------------------

@tool
async def proposition_search(query: str, k: int = 10) -> list[dict]:
    """Search the proposition index for precise factual matches.

    Searches only L3 (proposition-level) chunks for fine-grained fact retrieval.

    Args:
        query: The search query.
        k: Number of results to return.

    Returns:
        List of dicts with content, score, and metadata.
    """
    # Delegate to semantic_search with level=L3
    return await semantic_search.ainvoke({"query": query, "level": "L3", "k": k})


# ---------------------------------------------------------------------------
# Tool 3: Keyword Search (sparse-only for exact terms)
# ---------------------------------------------------------------------------

@tool
async def keyword_search(query: str, k: int = 20) -> list[dict]:
    """Sparse-only search for exact terms, acronyms, regulation numbers.

    Uses only sparse vectors (no dense), ideal for finding exact matches
    like 'DAFI 36-2903', 'AFI 33-360', or specific acronyms.

    Args:
        query: The search query containing exact terms.
        k: Number of results to return.

    Returns:
        List of dicts with content, score, and metadata.
    """
    container = _require_container()
    start = time.perf_counter()

    try:
        vectorstore = await container.get_vectorstore()
        embeddings = await container.get_embeddings()

        sparse_vector = await embeddings.embed_sparse(query)

        results = await vectorstore.sparse_search(
            sparse_vector=sparse_vector,
            k=k,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"[keyword_search] k={k} results={len(results)} "
            f"time={elapsed_ms:.1f}ms"
        )

        return [
            {
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
                "metadata": r.get("metadata", {}),
                "id": r.get("id", ""),
            }
            for r in results
        ]

    except Exception as e:
        logger.error(f"[keyword_search] failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Tool 4: Graph Traverse (knowledge graph edges via Redis)
# ---------------------------------------------------------------------------

@tool
async def graph_traverse(
    entity: str, relationship: Optional[str] = None, depth: int = 2
) -> list[dict]:
    """Follow relationships in the knowledge graph.

    Traverses the Redis-backed adjacency list to find entities connected
    to the given entity, optionally filtering by relationship type.

    Args:
        entity: The entity name to start traversal from.
        relationship: Optional relationship type filter (e.g. 'references').
        depth: Maximum traversal depth. Default 2.

    Returns:
        List of dicts with entity, relationship, and depth information.
    """
    container = _require_container()
    start = time.perf_counter()

    try:
        cache = await container.get_cache()

        visited: set[str] = set()
        results: list[dict] = []
        frontier = [(entity, 0)]

        while frontier:
            current_entity, current_depth = frontier.pop(0)

            if current_entity in visited or current_depth > depth:
                continue
            visited.add(current_entity)

            # Read adjacency list from Redis
            key = f"graph:edges:{current_entity}"
            edges_raw = await cache.get(key)

            if edges_raw is None:
                continue

            edges = edges_raw if isinstance(edges_raw, list) else []

            for edge in edges:
                rel_type = edge.get("relationship", "")
                target = edge.get("target", "")

                if relationship and rel_type != relationship:
                    continue

                results.append({
                    "source": current_entity,
                    "target": target,
                    "relationship": rel_type,
                    "depth": current_depth,
                })

                if current_depth + 1 <= depth and target not in visited:
                    frontier.append((target, current_depth + 1))

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"[graph_traverse] entity='{entity}' rel={relationship} depth={depth} "
            f"edges={len(results)} time={elapsed_ms:.1f}ms"
        )

        return results

    except Exception as e:
        logger.error(f"[graph_traverse] failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Tool 5: Chunk Read (full chunk + parent context)
# ---------------------------------------------------------------------------

@tool
async def chunk_read(chunk_id: str) -> dict:
    """Read full chunk content plus its parent section for context.

    Fetches the chunk from Qdrant by ID and also retrieves the parent
    chunk (via parent_id) for additional context.

    Args:
        chunk_id: The Qdrant point ID of the chunk to read.

    Returns:
        Dict with chunk content, metadata, and parent context.
    """
    container = _require_container()
    start = time.perf_counter()

    try:
        vectorstore = await container.get_vectorstore()

        chunk = await vectorstore.get_by_id(chunk_id)

        if chunk is None:
            logger.warning(f"[chunk_read] chunk not found: {chunk_id}")
            return {"error": f"Chunk {chunk_id} not found"}

        result = {
            "id": chunk_id,
            "content": chunk.get("content", ""),
            "metadata": chunk.get("metadata", {}),
            "parent_content": None,
        }

        # Fetch parent chunk for additional context
        parent_id = chunk.get("metadata", {}).get("parent_id")
        if parent_id:
            parent = await vectorstore.get_by_id(parent_id)
            if parent:
                result["parent_content"] = parent.get("content", "")

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"[chunk_read] id={chunk_id} has_parent={parent_id is not None} "
            f"time={elapsed_ms:.1f}ms"
        )

        return result

    except Exception as e:
        logger.error(f"[chunk_read] failed: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 6: Section Read (full L1 section summary)
# ---------------------------------------------------------------------------

@tool
async def section_read(section_id: str) -> dict:
    """Read a full L1 section summary.

    Retrieves the L1 (section-level) summary from Qdrant by ID.

    Args:
        section_id: The Qdrant point ID of the L1 section.

    Returns:
        Dict with section content and metadata.
    """
    container = _require_container()
    start = time.perf_counter()

    try:
        vectorstore = await container.get_vectorstore()

        section = await vectorstore.get_by_id(section_id)

        if section is None:
            logger.warning(f"[section_read] section not found: {section_id}")
            return {"error": f"Section {section_id} not found"}

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(f"[section_read] id={section_id} time={elapsed_ms:.1f}ms")

        return {
            "id": section_id,
            "content": section.get("content", ""),
            "metadata": section.get("metadata", {}),
        }

    except Exception as e:
        logger.error(f"[section_read] failed: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# All tools list (for agent binding)
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    semantic_search,
    proposition_search,
    keyword_search,
    graph_traverse,
    chunk_read,
    section_read,
]
