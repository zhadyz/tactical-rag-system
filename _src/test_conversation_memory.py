"""
Unit Tests for Conversation Memory System
Tests sliding window, summarization, and context retrieval
"""

import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from langchain.docstore.document import Document

from conversation_memory import (
    ConversationMemory,
    ConversationExchange
)


class MockLLM:
    """Mock LLM for testing without actual Ollama connection"""

    def invoke(self, prompt: str) -> str:
        """Return mock summary"""
        return "Mock summary: User asked about documents, assistant provided information about RAG system."


class TestConversationExchange(unittest.TestCase):
    """Test ConversationExchange dataclass"""

    def test_exchange_creation(self):
        """Test creating a conversation exchange"""
        docs = [Document(page_content="test content")]

        exchange = ConversationExchange(
            query="What is RAG?",
            response="RAG stands for Retrieval-Augmented Generation.",
            retrieved_docs=docs,
            query_type="simple",
            strategy_used="simple"
        )

        self.assertEqual(exchange.query, "What is RAG?")
        self.assertEqual(exchange.response, "RAG stands for Retrieval-Augmented Generation.")
        self.assertEqual(len(exchange.retrieved_docs), 1)
        self.assertEqual(exchange.query_type, "simple")
        self.assertEqual(exchange.strategy_used, "simple")
        self.assertIsInstance(exchange.timestamp, datetime)

    def test_exchange_to_text_summary(self):
        """Test converting exchange to text summary"""
        exchange = ConversationExchange(
            query="Hello",
            response="Hi there!",
            retrieved_docs=[]
        )

        summary = exchange.to_text_summary()
        self.assertIn("User: Hello", summary)
        self.assertIn("Assistant: Hi there!", summary)


class TestConversationMemory(unittest.TestCase):
    """Test ConversationMemory class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_llm = MockLLM()
        self.memory = ConversationMemory(
            llm=self.mock_llm,
            max_exchanges=10,
            summarization_threshold=5,
            enable_summarization=True
        )

    def test_initialization(self):
        """Test memory initialization"""
        self.assertEqual(self.memory.max_exchanges, 10)
        self.assertEqual(self.memory.summarization_threshold, 5)
        self.assertTrue(self.memory.enable_summarization)
        self.assertEqual(len(self.memory.exchanges), 0)
        self.assertIsNone(self.memory.conversation_summary)
        self.assertEqual(self.memory.total_exchanges, 0)

    def test_add_single_exchange(self):
        """Test adding a single exchange"""
        docs = [Document(page_content="Test content")]

        self.memory.add(
            query="What is RAG?",
            response="RAG is Retrieval-Augmented Generation.",
            retrieved_docs=docs,
            query_type="simple",
            strategy_used="simple"
        )

        self.assertEqual(len(self.memory.exchanges), 1)
        self.assertEqual(self.memory.total_exchanges, 1)

        exchange = self.memory.exchanges[0]
        self.assertEqual(exchange.query, "What is RAG?")
        self.assertEqual(exchange.query_type, "simple")

    def test_sliding_window(self):
        """Test sliding window behavior (FIFO)"""
        # Add 12 exchanges (max is 10)
        for i in range(12):
            self.memory.add(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_docs=[]
            )

        # Should only have 10 exchanges (window size)
        self.assertEqual(len(self.memory.exchanges), 10)
        self.assertEqual(self.memory.total_exchanges, 12)

        # First two should be evicted (FIFO)
        first_query = self.memory.exchanges[0].query
        self.assertEqual(first_query, "Query 2")  # Query 0 and 1 evicted

    def test_get_context_empty(self):
        """Test getting context when no exchanges exist"""
        context = self.memory.get_context("Current query")
        self.assertEqual(context, "")

    def test_get_context_with_exchanges(self):
        """Test getting context with exchanges"""
        # Add 3 exchanges
        for i in range(3):
            self.memory.add(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_docs=[]
            )

        context = self.memory.get_context("Current query", max_recent_exchanges=2)

        # Should include recent conversation header
        self.assertIn("Recent Conversation", context)
        # Should include last 2 exchanges
        self.assertIn("Query 1", context)
        self.assertIn("Query 2", context)
        # Should NOT include Query 0 (only last 2 requested)
        self.assertNotIn("Query 0", context)

    def test_summarization_trigger(self):
        """Test automatic summarization after threshold"""
        # Disable actual summarization for initial test
        self.memory.enable_summarization = True

        # Add exactly 5 exchanges (threshold)
        for i in range(5):
            self.memory.add(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_docs=[]
            )

        # Summarization should have been triggered
        self.assertEqual(self.memory.summarizations_performed, 1)
        self.assertIsNotNone(self.memory.conversation_summary)
        self.assertIn("Mock summary", self.memory.conversation_summary)

    def test_manual_summarize(self):
        """Test manual summarization"""
        # Add 3 exchanges
        for i in range(3):
            self.memory.add(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_docs=[]
            )

        # Manually trigger summarization
        summary = self.memory.summarize()

        self.assertIsNotNone(summary)
        self.assertIn("Mock summary", summary)

    def test_clear_memory(self):
        """Test clearing conversation memory"""
        # Add exchanges
        for i in range(3):
            self.memory.add(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_docs=[]
            )

        # Trigger summarization
        self.memory.summarize()

        # Clear memory
        self.memory.clear()

        # Verify everything is reset
        self.assertEqual(len(self.memory.exchanges), 0)
        self.assertIsNone(self.memory.conversation_summary)
        self.assertEqual(self.memory.total_exchanges, 0)
        self.assertEqual(self.memory.summarizations_performed, 0)

    def test_get_stats(self):
        """Test getting memory statistics"""
        # Add exchanges
        for i in range(3):
            self.memory.add(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_docs=[]
            )

        stats = self.memory.get_stats()

        self.assertEqual(stats['total_exchanges'], 3)
        self.assertEqual(stats['current_window_size'], 3)
        self.assertEqual(stats['max_exchanges'], 10)
        self.assertFalse(stats['has_summary'])
        self.assertEqual(stats['summary_length'], 0)

    def test_is_follow_up_question(self):
        """Test follow-up question detection"""
        # No exchanges yet - not a follow-up
        self.assertFalse(self.memory.is_follow_up_question("What is RAG?"))

        # Add an exchange
        self.memory.add(
            query="What is RAG?",
            response="RAG is Retrieval-Augmented Generation.",
            retrieved_docs=[]
        )

        # Questions with follow-up indicators
        self.assertTrue(self.memory.is_follow_up_question("Tell me more about that"))
        self.assertTrue(self.memory.is_follow_up_question("What about those documents?"))
        self.assertTrue(self.memory.is_follow_up_question("How does this work?"))
        self.assertTrue(self.memory.is_follow_up_question("Can you explain it?"))

        # Questions without follow-up indicators
        self.assertFalse(self.memory.is_follow_up_question("What is semantic search?"))

    def test_get_last_exchange(self):
        """Test retrieving last exchange"""
        # No exchanges
        self.assertIsNone(self.memory.get_last_exchange())

        # Add exchanges
        for i in range(3):
            self.memory.add(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_docs=[]
            )

        last = self.memory.get_last_exchange()
        self.assertIsNotNone(last)
        self.assertEqual(last.query, "Query 2")

    def test_get_relevant_context_for_query(self):
        """Test getting relevant context for query enhancement"""
        # Add exchanges
        docs = [Document(page_content="Test doc")]
        for i in range(3):
            self.memory.add(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_docs=docs
            )

        # Test with follow-up question
        enhanced_query, relevant_docs = self.memory.get_relevant_context_for_query(
            "Tell me more about that"
        )

        # Should enhance the query
        self.assertIn("Current question: Tell me more about that", enhanced_query)
        self.assertIn("Recent Conversation", enhanced_query)

        # Should return relevant documents
        self.assertGreater(len(relevant_docs), 0)

    def test_get_relevant_context_for_non_followup(self):
        """Test context retrieval for non-follow-up questions"""
        # Add exchange
        self.memory.add(
            query="What is RAG?",
            response="RAG is Retrieval-Augmented Generation.",
            retrieved_docs=[]
        )

        # Test with non-follow-up question
        enhanced_query, relevant_docs = self.memory.get_relevant_context_for_query(
            "What is semantic search?"
        )

        # Should NOT enhance the query (return as-is)
        self.assertEqual(enhanced_query, "What is semantic search?")
        self.assertEqual(len(relevant_docs), 0)

    def test_thread_safety(self):
        """Test thread-safe operations"""
        import threading

        def add_exchanges():
            for i in range(10):
                self.memory.add(
                    query=f"Query {i}",
                    response=f"Response {i}",
                    retrieved_docs=[]
                )

        # Run multiple threads
        threads = [threading.Thread(target=add_exchanges) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify total exchanges (3 threads × 10 exchanges)
        self.assertEqual(self.memory.total_exchanges, 30)

    def test_summarization_disabled(self):
        """Test behavior when summarization is disabled"""
        memory_no_summary = ConversationMemory(
            llm=self.mock_llm,
            max_exchanges=10,
            summarization_threshold=5,
            enable_summarization=False
        )

        # Add 5 exchanges
        for i in range(5):
            memory_no_summary.add(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_docs=[]
            )

        # Should NOT have created summary
        self.assertEqual(memory_no_summary.summarizations_performed, 0)
        self.assertIsNone(memory_no_summary.conversation_summary)


if __name__ == '__main__':
    unittest.main()
