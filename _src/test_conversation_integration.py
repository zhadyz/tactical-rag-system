"""
Integration Tests for Conversation Memory in RAG System
Tests multi-turn conversation workflows and context retention
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from conversation_memory import ConversationMemory, ConversationExchange
from langchain.docstore.document import Document


class MockLLMForIntegration:
    """Mock LLM that simulates realistic summarization"""

    def invoke(self, prompt: str) -> str:
        """Generate contextual summary based on prompt content"""
        if "summarize" in prompt.lower() or "summary" in prompt.lower():
            return "Summary: User asked about RAG system features including conversation memory, adaptive retrieval, and GPU acceleration. Assistant provided detailed explanations of multi-turn context tracking and system capabilities."
        return "Mock response"


@pytest.fixture
def mock_llm():
    """Provide mock LLM for testing"""
    return MockLLMForIntegration()


@pytest.fixture
def conversation_memory(mock_llm):
    """Provide conversation memory instance"""
    return ConversationMemory(
        llm=mock_llm,
        max_exchanges=10,
        summarization_threshold=5,
        enable_summarization=True
    )


@pytest.mark.asyncio
class TestConversationIntegration:
    """Integration tests for conversation memory workflows"""

    def test_single_turn_conversation(self, conversation_memory):
        """Test basic single-turn conversation"""
        docs = [Document(page_content="RAG stands for Retrieval-Augmented Generation.")]

        conversation_memory.add(
            query="What is RAG?",
            response="RAG (Retrieval-Augmented Generation) is an AI technique that combines retrieval with generation.",
            retrieved_docs=docs,
            query_type="simple",
            strategy_used="simple"
        )

        stats = conversation_memory.get_stats()
        assert stats['total_exchanges'] == 1
        assert stats['current_window_size'] == 1
        assert not stats['has_summary']

    def test_multi_turn_conversation_basic(self, conversation_memory):
        """Test 3-turn conversation with context"""
        docs = [Document(page_content="Test content")]

        # Turn 1
        conversation_memory.add(
            query="What is RAG?",
            response="RAG is Retrieval-Augmented Generation.",
            retrieved_docs=docs,
            query_type="simple",
            strategy_used="simple"
        )

        # Turn 2 - Follow-up
        conversation_memory.add(
            query="How does it work?",
            response="RAG retrieves relevant documents and uses them to generate answers.",
            retrieved_docs=docs,
            query_type="moderate",
            strategy_used="hybrid"
        )

        # Turn 3 - Another follow-up
        conversation_memory.add(
            query="What are the benefits?",
            response="Benefits include factual grounding, reduced hallucination, and domain adaptation.",
            retrieved_docs=docs,
            query_type="moderate",
            strategy_used="hybrid"
        )

        stats = conversation_memory.get_stats()
        assert stats['total_exchanges'] == 3
        assert stats['current_window_size'] == 3

        # Get context
        context = conversation_memory.get_context("Current question", max_recent_exchanges=3)
        assert "Recent Conversation" in context
        assert "What is RAG?" in context
        assert "How does it work?" in context

    def test_follow_up_detection(self, conversation_memory):
        """Test follow-up question detection"""
        docs = [Document(page_content="Test")]

        # First question - not a follow-up
        assert not conversation_memory.is_follow_up_question("What is machine learning?")

        # Add initial exchange
        conversation_memory.add(
            query="What is RAG?",
            response="RAG is Retrieval-Augmented Generation.",
            retrieved_docs=docs
        )

        # Follow-up questions
        assert conversation_memory.is_follow_up_question("Tell me more about that")
        assert conversation_memory.is_follow_up_question("What about those benefits?")
        assert conversation_memory.is_follow_up_question("How does this work?")
        assert conversation_memory.is_follow_up_question("Can you explain it?")

        # Not follow-ups
        assert not conversation_memory.is_follow_up_question("What is semantic search and how does it differ from traditional search?")

    def test_context_enhancement_for_followups(self, conversation_memory):
        """Test query enhancement for follow-up questions"""
        docs = [Document(page_content="GPU acceleration improves performance.")]

        # Initial conversation
        conversation_memory.add(
            query="Does the system use GPU?",
            response="Yes, the system uses GPU acceleration for embeddings and reranking.",
            retrieved_docs=docs,
            query_type="simple",
            strategy_used="simple"
        )

        # Follow-up question
        enhanced_query, relevant_docs = conversation_memory.get_relevant_context_for_query(
            "What about the performance benefits?"
        )

        # Should enhance the query
        assert "Current question: What about the performance benefits?" in enhanced_query
        assert "Recent Conversation" in enhanced_query
        assert "Does the system use GPU?" in enhanced_query
        assert len(relevant_docs) > 0

    def test_non_followup_passthrough(self, conversation_memory):
        """Test that non-follow-up questions are not enhanced"""
        docs = [Document(page_content="Test")]

        conversation_memory.add(
            query="What is RAG?",
            response="RAG is Retrieval-Augmented Generation.",
            retrieved_docs=docs
        )

        # New topic - not a follow-up
        enhanced_query, relevant_docs = conversation_memory.get_relevant_context_for_query(
            "What is the capital of France?"
        )

        # Should NOT enhance (return as-is)
        assert enhanced_query == "What is the capital of France?"
        assert len(relevant_docs) == 0

    def test_five_turn_conversation_with_summarization(self, conversation_memory):
        """Test 5+ turn conversation triggering automatic summarization"""
        docs = [Document(page_content="Test content")]

        questions = [
            "What is RAG?",
            "How does it work?",
            "What models does it use?",
            "Is GPU acceleration supported?",
            "What are the performance metrics?"
        ]

        responses = [
            "RAG is Retrieval-Augmented Generation.",
            "It retrieves documents and generates answers.",
            "It uses llama3.1:8b and nomic-embed-text.",
            "Yes, GPU acceleration is supported.",
            "Performance varies from 1-6 seconds per query."
        ]

        # Add 5 exchanges
        for i, (q, r) in enumerate(zip(questions, responses), 1):
            conversation_memory.add(
                query=q,
                response=r,
                retrieved_docs=docs,
                query_type="simple",
                strategy_used="simple"
            )

        stats = conversation_memory.get_stats()
        assert stats['total_exchanges'] == 5
        assert stats['summarizations_performed'] == 1
        assert stats['has_summary']
        assert stats['summary_length'] > 0

        # Verify summary exists
        assert conversation_memory.conversation_summary is not None
        assert "RAG system" in conversation_memory.conversation_summary or "Summary" in conversation_memory.conversation_summary

    def test_sliding_window_eviction(self, conversation_memory):
        """Test that window correctly evicts old exchanges (FIFO)"""
        docs = [Document(page_content="Test")]

        # Add 12 exchanges (max is 10)
        for i in range(12):
            conversation_memory.add(
                query=f"Question {i}",
                response=f"Answer {i}",
                retrieved_docs=docs
            )

        stats = conversation_memory.get_stats()
        assert stats['total_exchanges'] == 12
        assert stats['current_window_size'] == 10  # Max window size

        # First two should be evicted
        first_exchange = conversation_memory.exchanges[0]
        assert first_exchange.query == "Question 2"  # 0 and 1 evicted

        last_exchange = conversation_memory.get_last_exchange()
        assert last_exchange.query == "Question 11"

    def test_conversation_clear(self, conversation_memory):
        """Test clearing conversation memory"""
        docs = [Document(page_content="Test")]

        # Add exchanges and trigger summarization
        for i in range(5):
            conversation_memory.add(
                query=f"Question {i}",
                response=f"Answer {i}",
                retrieved_docs=docs
            )

        # Verify state before clear
        assert conversation_memory.get_stats()['total_exchanges'] == 5

        # Clear
        conversation_memory.clear()

        # Verify reset
        stats = conversation_memory.get_stats()
        assert stats['total_exchanges'] == 0
        assert stats['current_window_size'] == 0
        assert not stats['has_summary']
        assert stats['summarizations_performed'] == 0

    def test_continuous_summarization(self, conversation_memory):
        """Test multiple summarization triggers"""
        docs = [Document(page_content="Test")]

        # Add 10 exchanges (should trigger 2 summarizations at 5 and 10)
        for i in range(10):
            conversation_memory.add(
                query=f"Question {i}",
                response=f"Answer {i}",
                retrieved_docs=docs
            )

        stats = conversation_memory.get_stats()
        assert stats['total_exchanges'] == 10
        assert stats['summarizations_performed'] == 2  # At 5 and 10
        assert stats['has_summary']

    def test_context_with_summary_and_recent(self, conversation_memory):
        """Test context includes both summary and recent exchanges"""
        docs = [Document(page_content="Test")]

        # Add 7 exchanges (trigger summarization at 5)
        for i in range(7):
            conversation_memory.add(
                query=f"Question {i}",
                response=f"Answer {i}",
                retrieved_docs=docs
            )

        # Get context
        context = conversation_memory.get_context("Current question", max_recent_exchanges=2)

        # Should have both summary and recent
        assert "Earlier Conversation Summary" in context
        assert "Recent Conversation" in context
        assert "Question 5" in context  # Recent
        assert "Question 6" in context  # Recent

    def test_last_exchange_retrieval(self, conversation_memory):
        """Test retrieving the last exchange"""
        docs = [Document(page_content="Test")]

        # No exchanges yet
        assert conversation_memory.get_last_exchange() is None

        # Add exchanges
        conversation_memory.add(
            query="First question",
            response="First answer",
            retrieved_docs=docs
        )

        conversation_memory.add(
            query="Second question",
            response="Second answer",
            retrieved_docs=docs
        )

        # Get last
        last = conversation_memory.get_last_exchange()
        assert last is not None
        assert last.query == "Second question"
        assert last.response == "Second answer"


@pytest.mark.asyncio
class TestConversationMemoryPerformance:
    """Performance and scalability tests"""

    def test_memory_stats_accuracy(self, conversation_memory):
        """Test that statistics are accurately tracked"""
        docs = [Document(page_content="Test")]

        # Add 3 exchanges
        for i in range(3):
            conversation_memory.add(
                query=f"Q{i}",
                response=f"A{i}",
                retrieved_docs=docs
            )

        stats = conversation_memory.get_stats()
        assert stats['total_exchanges'] == 3
        assert stats['current_window_size'] == 3
        assert stats['max_exchanges'] == 10
        assert stats['summarizations_performed'] == 0

    def test_large_conversation_handling(self, conversation_memory):
        """Test handling of very long conversations"""
        docs = [Document(page_content="Test")]

        # Simulate 25-turn conversation
        for i in range(25):
            conversation_memory.add(
                query=f"Question {i}",
                response=f"Answer {i}",
                retrieved_docs=docs
            )

        stats = conversation_memory.get_stats()
        assert stats['total_exchanges'] == 25
        assert stats['current_window_size'] == 10  # Window size limit
        assert stats['summarizations_performed'] == 5  # Every 5 exchanges


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
