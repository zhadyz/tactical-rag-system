"""
Pytest Configuration for Tactical RAG Test Suite
Shared fixtures and configuration for all tests
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Generator

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "_src"))


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest settings"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require services)"
    )
    config.addinivalue_line(
        "markers", "performance: Performance benchmarks (slow)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        {
            "text": "Air Force uniform regulations specify proper attire for duty.",
            "metadata": {
                "document_id": "AFI-36-2903",
                "file_name": "dafi36-2903.pdf",
                "page": 1,
                "chunk_index": 0,
                "category": "uniform_regulations"
            }
        },
        {
            "text": "Leave policies allow 30 days of annual leave per fiscal year.",
            "metadata": {
                "document_id": "AFI-36-3003",
                "file_name": "dafi36-3003.pdf",
                "page": 5,
                "chunk_index": 1,
                "category": "leave_policy"
            }
        },
        {
            "text": "Physical fitness standards require passing scores in all components.",
            "metadata": {
                "document_id": "AFI-36-2905",
                "file_name": "dafi36-2905.pdf",
                "page": 10,
                "chunk_index": 2,
                "category": "fitness"
            }
        }
    ]


@pytest.fixture
def sample_queries():
    """Sample queries for testing"""
    return [
        {
            "query": "What are the uniform regulations?",
            "expected_type": "simple",
            "expected_doc_id": "AFI-36-2903"
        },
        {
            "query": "How many days of leave do I get per year?",
            "expected_type": "simple",
            "expected_doc_id": "AFI-36-3003"
        },
        {
            "query": "Compare the fitness standards to the uniform requirements",
            "expected_type": "complex",
            "expected_doc_id": None  # Multiple docs
        }
    ]


@pytest.fixture
def mock_embeddings():
    """Mock embeddings for testing without real model"""
    import numpy as np

    class MockEmbeddings:
        def embed_query(self, text: str):
            # Deterministic embeddings based on text hash
            np.random.seed(hash(text) % 2**32)
            return np.random.randn(768).astype(np.float32)

        def embed_documents(self, texts: list):
            return [self.embed_query(text) for text in texts]

    return MockEmbeddings()


@pytest.fixture
async def redis_test_client():
    """Test Redis client (will skip if Redis unavailable)"""
    try:
        import redis.asyncio as redis
        client = await redis.from_url(
            "redis://localhost:6379",
            decode_responses=False
        )
        await client.ping()
        yield client
        await client.flushdb()  # Clean up after tests
        await client.close()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.fixture
def temp_chroma_db(tmp_path):
    """Temporary ChromaDB for testing"""
    return tmp_path / "test_chroma_db"


@pytest.fixture
def test_config():
    """Test configuration"""
    from config import SystemConfig

    config = SystemConfig()
    config.cache.use_redis = False  # Use local cache for tests
    config.retrieval.initial_k = 10
    config.retrieval.rerank_k = 5
    config.retrieval.final_k = 3

    return config
