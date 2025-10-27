"""
ATLAS Protocol - Conversation Memory

Maintains conversation context across queries for coherent multi-turn interactions.
Implements summarization for long conversations to prevent context overflow.
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Manages conversation history with automatic summarization.

    Features:
    - Store query-response pairs with metadata
    - Retrieve relevant context for new queries
    - Auto-summarization when history exceeds threshold
    - Clear conversation state
    """

    def __init__(
        self,
        llm=None,
        max_exchanges: int = 10,
        summarization_threshold: int = 5,
        enable_summarization: bool = True
    ):
        """
        Initialize conversation memory.

        Args:
            llm: LLM instance for summarization
            max_exchanges: Maximum exchanges to keep in memory
            summarization_threshold: Trigger summarization after this many exchanges
            enable_summarization: Whether to enable auto-summarization
        """
        self.llm = llm
        self.max_exchanges = max_exchanges
        self.summarization_threshold = summarization_threshold
        self.enable_summarization = enable_summarization

        # Storage
        self.exchanges: List[Dict[str, Any]] = []
        self.summary: Optional[str] = None

        logger.info(
            f"ConversationMemory initialized (max={max_exchanges}, "
            f"summarization={'enabled' if enable_summarization else 'disabled'})"
        )

    def add(
        self,
        query: str,
        response: str,
        retrieved_docs: Optional[List] = None,
        query_type: str = "simple",
        strategy_used: str = "simple_dense"
    ) -> None:
        """
        Add a query-response exchange to memory.

        Args:
            query: User's query
            response: System's response
            retrieved_docs: Documents retrieved for this query
            query_type: Type of query (simple, moderate, complex)
            strategy_used: Retrieval strategy used
        """
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "query_type": query_type,
            "strategy_used": strategy_used,
            "num_docs": len(retrieved_docs) if retrieved_docs else 0
        }

        self.exchanges.append(exchange)

        # Trim if exceeds max
        if len(self.exchanges) > self.max_exchanges:
            self.exchanges = self.exchanges[-self.max_exchanges:]
            logger.debug(f"Trimmed conversation history to {self.max_exchanges} exchanges")

        # Trigger summarization if needed
        if (
            self.enable_summarization
            and len(self.exchanges) >= self.summarization_threshold
            and not self.summary
        ):
            self._summarize()

    def get_relevant_context_for_query(
        self,
        current_query: str,
        max_exchanges: int = 3
    ) -> Tuple[str, int]:
        """
        Get relevant conversation context for a new query.

        Args:
            current_query: The current user query
            max_exchanges: Maximum number of previous exchanges to include

        Returns:
            Tuple of (enhanced_query, context_length)
        """
        if not self.exchanges:
            return current_query, 0

        # Get last N exchanges
        recent_exchanges = self.exchanges[-max_exchanges:]

        # Build context
        context_parts = []
        if self.summary:
            context_parts.append(f"Previous conversation summary: {self.summary}")

        for exchange in recent_exchanges:
            context_parts.append(f"User: {exchange['query']}")
            context_parts.append(f"Assistant: {exchange['response'][:200]}...")

        context = "\n".join(context_parts)

        # Enhanced query with context
        enhanced_query = f"{context}\n\nCurrent question: {current_query}"

        return enhanced_query, len(context)

    def _summarize(self) -> None:
        """Generate summary of conversation history using LLM"""
        if not self.llm or not self.exchanges:
            return

        try:
            # Build conversation text
            conv_text = []
            for ex in self.exchanges:
                conv_text.append(f"User: {ex['query']}")
                conv_text.append(f"Assistant: {ex['response']}")

            conversation = "\n".join(conv_text)

            # Generate summary
            prompt = f"""Summarize this conversation in 2-3 sentences, focusing on key topics and decisions:

{conversation}

Summary:"""

            self.summary = self.llm.invoke(prompt)
            logger.info("Conversation summarized")

        except Exception as e:
            logger.warning(f"Summarization failed: {e}")

    def clear(self) -> None:
        """Clear all conversation history"""
        self.exchanges.clear()
        self.summary = None
        logger.info("Conversation memory cleared")

    def get_history(self, last_n: int = 5) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            last_n: Number of recent exchanges to return

        Returns:
            List of exchange dictionaries
        """
        return self.exchanges[-last_n:] if self.exchanges else []

    def __len__(self) -> int:
        """Return number of exchanges in memory"""
        return len(self.exchanges)
