"""
Forge - Conversation Memory

Adapted from _src/conversation_memory.py with minimal changes.
Maintains conversation context across queries with auto-summarization.
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Stores query-response exchanges with automatic summarization
    when history exceeds a threshold.
    """

    def __init__(
        self,
        llm=None,
        max_exchanges: int = 10,
        summarization_threshold: int = 5,
        enable_summarization: bool = True,
    ):
        self.llm = llm
        self.max_exchanges = max_exchanges
        self.summarization_threshold = summarization_threshold
        self.enable_summarization = enable_summarization

        self.exchanges: List[Dict[str, Any]] = []
        self.summary: Optional[str] = None

    def set_llm(self, llm):
        """Set or update the LLM used for summarization."""
        self.llm = llm

    def add(
        self,
        query: str,
        response: str,
        retrieved_docs: Optional[List] = None,
        query_type: str = "simple",
        strategy_used: str = "direct",
    ) -> None:
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "query_type": query_type,
            "strategy_used": strategy_used,
            "num_docs": len(retrieved_docs) if retrieved_docs else 0,
        }
        self.exchanges.append(exchange)

        if len(self.exchanges) > self.max_exchanges:
            self.exchanges = self.exchanges[-self.max_exchanges:]

        if (
            self.enable_summarization
            and len(self.exchanges) >= self.summarization_threshold
            and not self.summary
        ):
            self._summarize()

    def get_relevant_context_for_query(
        self, current_query: str, max_exchanges: int = 3,
    ) -> Tuple[str, int]:
        if not self.exchanges:
            return current_query, 0

        recent = self.exchanges[-max_exchanges:]
        parts = []
        if self.summary:
            parts.append(f"Previous conversation summary: {self.summary}")
        for ex in recent:
            parts.append(f"User: {ex['query']}")
            parts.append(f"Assistant: {ex['response'][:200]}...")
        context = "\n".join(parts)
        return f"{context}\n\nCurrent question: {current_query}", len(context)

    def _summarize(self) -> None:
        if not self.llm or not self.exchanges:
            return
        try:
            conv = "\n".join(
                f"User: {ex['query']}\nAssistant: {ex['response']}"
                for ex in self.exchanges
            )
            prompt = (
                "Summarize this conversation in 2-3 sentences, "
                f"focusing on key topics and decisions:\n\n{conv}\n\nSummary:"
            )
            self.summary = self.llm.invoke(prompt)
            logger.info("Conversation summarized")
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")

    def clear(self) -> None:
        self.exchanges.clear()
        self.summary = None

    def get_history(self, last_n: int = 5) -> List[Dict[str, Any]]:
        return self.exchanges[-last_n:] if self.exchanges else []

    def __len__(self) -> int:
        return len(self.exchanges)
