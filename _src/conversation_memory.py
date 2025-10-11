"""
Conversation Memory System for Multi-Turn Context Tracking
Implements sliding window with automatic LLM-based compression
"""

import logging
from collections import deque
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading
from langchain_community.llms import Ollama as OllamaLLM
from langchain.docstore.document import Document

logger = logging.getLogger(__name__)


@dataclass
class ConversationExchange:
    """Single conversation exchange with metadata"""
    query: str
    response: str
    retrieved_docs: List[Document]
    timestamp: datetime = field(default_factory=datetime.now)
    query_type: str = "unknown"
    strategy_used: str = "unknown"

    def to_text_summary(self) -> str:
        """Convert exchange to text for summarization"""
        return f"User: {self.query}\nAssistant: {self.response}"


class ConversationMemory:
    """
    Multi-turn conversation memory with sliding window and automatic summarization.

    Features:
    - Sliding window: Stores last N exchanges (default: 10)
    - Automatic summarization: After M exchanges (default: 5), compresses history
    - LLM-based compression: Uses existing LLM to create concise summaries
    - Thread-safe: Uses locks for concurrent access
    - Context-aware: Provides rich context for follow-up questions

    Architecture:
    - Recent exchanges: Stored in full detail in deque (FIFO)
    - Older exchanges: Compressed into summary text
    - Summary generation: Triggered automatically when window fills
    """

    def __init__(
        self,
        llm: OllamaLLM,
        max_exchanges: int = 10,
        summarization_threshold: int = 5,
        enable_summarization: bool = True
    ):
        """
        Initialize conversation memory system.

        Args:
            llm: LangChain LLM instance for summarization
            max_exchanges: Maximum number of exchanges to store in window
            summarization_threshold: Number of exchanges before triggering summarization
            enable_summarization: Whether to enable automatic summarization
        """
        self.llm = llm
        self.max_exchanges = max_exchanges
        self.summarization_threshold = summarization_threshold
        self.enable_summarization = enable_summarization

        # Sliding window of recent exchanges (FIFO queue)
        self.exchanges: deque = deque(maxlen=max_exchanges)

        # Compressed summary of older conversations
        self.conversation_summary: Optional[str] = None

        # Thread safety
        self.lock = threading.RLock()

        # Statistics
        self.total_exchanges = 0
        self.summarizations_performed = 0

        logger.info(
            f"ConversationMemory initialized: "
            f"max_exchanges={max_exchanges}, "
            f"summarization_threshold={summarization_threshold}, "
            f"summarization={'enabled' if enable_summarization else 'disabled'}"
        )

    def add(
        self,
        query: str,
        response: str,
        retrieved_docs: List[Document],
        query_type: str = "unknown",
        strategy_used: str = "unknown"
    ) -> None:
        """
        Add a new exchange to conversation memory.

        Args:
            query: User's query
            response: Assistant's response
            retrieved_docs: Documents retrieved for this query
            query_type: Type of query (simple/moderate/complex)
            strategy_used: Retrieval strategy used
        """
        with self.lock:
            exchange = ConversationExchange(
                query=query,
                response=response,
                retrieved_docs=retrieved_docs,
                timestamp=datetime.now(),
                query_type=query_type,
                strategy_used=strategy_used
            )

            self.exchanges.append(exchange)
            self.total_exchanges += 1

            logger.debug(
                f"Added exchange {self.total_exchanges}: "
                f"query_type={query_type}, strategy={strategy_used}"
            )

            # Check if summarization is needed
            if (
                self.enable_summarization
                and len(self.exchanges) >= self.summarization_threshold
                and self.total_exchanges % self.summarization_threshold == 0
            ):
                self._trigger_summarization()

    def get_context(
        self,
        current_query: str,
        include_documents: bool = False,
        max_recent_exchanges: int = 3
    ) -> str:
        """
        Get conversation context for current query.

        Args:
            current_query: Current user query to provide context for
            include_documents: Whether to include retrieved documents in context
            max_recent_exchanges: Maximum number of recent exchanges to include

        Returns:
            Formatted conversation context string
        """
        with self.lock:
            if not self.exchanges and not self.conversation_summary:
                return ""

            context_parts = []

            # Add conversation summary if exists
            if self.conversation_summary:
                context_parts.append("=== Earlier Conversation Summary ===")
                context_parts.append(self.conversation_summary)
                context_parts.append("")

            # Add recent exchanges (most recent first priority)
            if self.exchanges:
                recent = list(self.exchanges)[-max_recent_exchanges:]
                context_parts.append("=== Recent Conversation ===")

                for i, exchange in enumerate(recent, 1):
                    context_parts.append(f"\nExchange {i}:")
                    context_parts.append(f"User: {exchange.query}")
                    context_parts.append(f"Assistant: {exchange.response[:200]}...")

                    if include_documents and exchange.retrieved_docs:
                        doc_previews = [
                            doc.page_content[:100]
                            for doc in exchange.retrieved_docs[:2]
                        ]
                        context_parts.append(
                            f"Context: {'; '.join(doc_previews)}..."
                        )

            context = "\n".join(context_parts)

            logger.debug(
                f"Generated context: {len(context)} chars, "
                f"{len(recent) if self.exchanges else 0} recent exchanges, "
                f"summary={'yes' if self.conversation_summary else 'no'}"
            )

            return context

    def _trigger_summarization(self) -> None:
        """
        Trigger LLM-based summarization of conversation history.

        This compresses older exchanges into a concise summary to save context space
        while preserving important information for follow-up questions.
        """
        try:
            logger.info("Triggering conversation summarization...")

            # Get all exchanges to summarize
            exchanges_text = "\n\n".join([
                exchange.to_text_summary()
                for exchange in self.exchanges
            ])

            # Create summarization prompt
            prompt = f"""You are an AI assistant helping to summarize a conversation between a user and an AI document assistant.

Please create a concise summary of the following conversation, preserving:
1. Main topics discussed
2. Key questions asked
3. Important information provided
4. Any unresolved issues or follow-up topics

Keep the summary under 200 words but ensure no critical context is lost.

Conversation:
{exchanges_text}

Summary:"""

            # Generate summary using LLM
            summary = self.llm.invoke(prompt)

            # Update conversation summary
            if self.conversation_summary:
                # Append to existing summary
                self.conversation_summary = (
                    f"{self.conversation_summary}\n\n"
                    f"[Continued] {summary}"
                )
            else:
                self.conversation_summary = summary

            self.summarizations_performed += 1

            logger.info(
                f"Summarization complete: "
                f"{len(exchanges_text)} chars → {len(summary)} chars "
                f"(compression: {len(summary)/len(exchanges_text)*100:.1f}%)"
            )

        except Exception as e:
            logger.error(f"Summarization failed: {e}", exc_info=True)
            # Graceful degradation - continue without summary

    def summarize(self) -> Optional[str]:
        """
        Manually trigger summarization and return current summary.

        Returns:
            Current conversation summary or None if no exchanges exist
        """
        with self.lock:
            if not self.exchanges:
                return None

            self._trigger_summarization()
            return self.conversation_summary

    def clear(self) -> None:
        """Clear all conversation history and reset state."""
        with self.lock:
            self.exchanges.clear()
            self.conversation_summary = None
            self.total_exchanges = 0
            self.summarizations_performed = 0
            logger.info("Conversation memory cleared")

    def get_stats(self) -> Dict:
        """
        Get conversation memory statistics.

        Returns:
            Dictionary with memory statistics
        """
        with self.lock:
            return {
                "total_exchanges": self.total_exchanges,
                "current_window_size": len(self.exchanges),
                "max_exchanges": self.max_exchanges,
                "has_summary": self.conversation_summary is not None,
                "summary_length": (
                    len(self.conversation_summary)
                    if self.conversation_summary else 0
                ),
                "summarizations_performed": self.summarizations_performed
            }

    def is_follow_up_question(self, query: str) -> bool:
        """
        Detect if current query is likely a follow-up question.

        Args:
            query: Current user query

        Returns:
            True if query appears to be a follow-up
        """
        if not self.exchanges:
            return False

        # Follow-up indicators
        follow_up_patterns = [
            "those", "these", "that", "this", "it", "them",
            "what about", "how about", "tell me more",
            "can you explain", "why is", "also",
            "additionally", "furthermore", "moreover",
            "the previous", "you mentioned", "earlier you said"
        ]

        query_lower = query.lower()

        # Check for pronouns/references without full context
        has_reference = any(
            pattern in query_lower
            for pattern in follow_up_patterns
        )

        # Short queries are more likely to be follow-ups if they have references
        is_short = len(query.split()) < 10

        return has_reference or (is_short and len(self.exchanges) > 0)

    def get_last_exchange(self) -> Optional[ConversationExchange]:
        """
        Get the most recent conversation exchange.

        Returns:
            Last exchange or None if no exchanges exist
        """
        with self.lock:
            return self.exchanges[-1] if self.exchanges else None

    def get_relevant_context_for_query(
        self,
        query: str,
        max_exchanges: int = 5
    ) -> Tuple[str, List[Document]]:
        """
        Get conversation context and documents relevant to current query.

        This is the primary method for query enhancement with conversation context.

        Args:
            query: Current user query
            max_exchanges: Maximum recent exchanges to consider

        Returns:
            Tuple of (enhanced_query, relevant_documents)
        """
        with self.lock:
            if not self.exchanges:
                return query, []

            # Check if this is a follow-up
            is_follow_up = self.is_follow_up_question(query)

            if not is_follow_up:
                return query, []

            # Get conversation context
            context = self.get_context(
                current_query=query,
                include_documents=False,
                max_recent_exchanges=min(max_exchanges, len(self.exchanges))
            )

            # Enhance query with context
            enhanced_query = f"""{context}

Current question: {query}

Please answer the current question using the conversation context above."""

            # Collect relevant documents from recent exchanges
            relevant_docs = []
            for exchange in list(self.exchanges)[-max_exchanges:]:
                relevant_docs.extend(exchange.retrieved_docs[:2])

            logger.debug(
                f"Enhanced query: is_follow_up={is_follow_up}, "
                f"context_length={len(context)}, "
                f"relevant_docs={len(relevant_docs)}"
            )

            return enhanced_query, relevant_docs
