"""
Forge - LLM Answer Generation with Citations

Generates answers from retrieved documents using llama.cpp via the
infrastructure LLM service. Instructs the model to cite sources as
[Source N]. Supports both batch and streaming generation.
"""

import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are Forge, an expert assistant for Air Force policies and regulations.
Answer the user's question using ONLY the provided source documents.
Cite your sources using [Source N] notation inline with your statements.
If the sources do not contain enough information, say so explicitly.
Do not make up information that is not in the sources."""

_CONTEXT_TEMPLATE = """\
## Source Documents

{sources}

## Conversation Context

{conversation_context}

## Question

{query}

## Instructions

Answer the question using the sources above. Cite each fact with [Source N].
Be specific, use exact numbers/dates/names from the sources when available.
"""


def _build_prompt(
    query: str,
    documents: list[dict],
    conversation_context: str = "",
) -> str:
    """Build the full generation prompt with numbered source documents."""
    source_blocks: list[str] = []
    for i, doc in enumerate(documents, 1):
        content = doc.get("content", "")
        file_name = doc.get("metadata", {}).get("file_name", "Unknown")
        section = doc.get("metadata", {}).get("section_path", "")
        header = f"[Source {i}] ({file_name}"
        if section:
            header += f" > {section}"
        header += ")"
        source_blocks.append(f"{header}\n{content}")

    sources_text = "\n\n".join(source_blocks) if source_blocks else "(No sources available)"

    ctx = conversation_context.strip() if conversation_context else "(No prior context)"

    return _CONTEXT_TEMPLATE.format(
        sources=sources_text,
        conversation_context=ctx,
        query=query,
    )


class ForgeGenerator:
    """
    LLM answer generation with explicit source citations.

    Args:
        container: ServiceContainer for LLM access.
        max_source_chars: Maximum characters per source in the prompt.
    """

    def __init__(self, container=None, max_source_chars: int = 2000):
        self.container = container
        self.max_source_chars = max_source_chars

    async def generate(
        self,
        query: str,
        documents: list[dict],
        conversation_context: str = "",
    ) -> str:
        """
        Generate a full answer (non-streaming).

        Args:
            query: The user question.
            documents: Approved documents to use as context.
            conversation_context: Prior conversation turns (optional).

        Returns:
            Generated answer string with [Source N] citations.
        """
        if self.container is None:
            raise RuntimeError("Generator requires a ServiceContainer")

        llm = await self.container.get_llm()

        # Truncate sources to fit context window
        truncated_docs = [
            {**d, "content": d.get("content", "")[:self.max_source_chars]}
            for d in documents
        ]

        prompt = _build_prompt(query, truncated_docs, conversation_context)

        answer = await llm.generate(
            prompt,
            system_prompt=_SYSTEM_PROMPT,
        )

        logger.info(
            f"[Generator] generated {len(answer)} chars from {len(documents)} sources"
        )
        return answer.strip()

    async def generate_stream(
        self,
        query: str,
        documents: list[dict],
        conversation_context: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        Stream answer tokens as they are generated.

        Args:
            query: The user question.
            documents: Approved documents to use as context.
            conversation_context: Prior conversation turns (optional).

        Yields:
            Individual text tokens / chunks.
        """
        if self.container is None:
            raise RuntimeError("Generator requires a ServiceContainer")

        llm = await self.container.get_llm()

        truncated_docs = [
            {**d, "content": d.get("content", "")[:self.max_source_chars]}
            for d in documents
        ]

        prompt = _build_prompt(query, truncated_docs, conversation_context)

        token_count = 0
        async for token in llm.generate_stream(
            prompt,
            system_prompt=_SYSTEM_PROMPT,
        ):
            token_count += 1
            yield token

        logger.info(
            f"[Generator] streamed {token_count} tokens from {len(documents)} sources"
        )
