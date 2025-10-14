"""
Manual Validation Test Suite
Tests core functionality without requiring external services (Redis, Qdrant, vLLM)
"""

import sys
from pathlib import Path

# Add _src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "_src"))

import asyncio
from typing import Dict, List


class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []

    def add_pass(self, name: str):
        self.passed.append(name)
        print(f"  PASS: {name}")

    def add_fail(self, name: str, error: str):
        self.failed.append((name, error))
        print(f"  FAIL: {name} - {error}")

    def add_skip(self, name: str, reason: str):
        self.skipped.append((name, reason))
        print(f"  SKIP: {name} - {reason}")

    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total:   {total}")
        print(f"Passed:  {len(self.passed)} ({len(self.passed)/total*100 if total > 0 else 0:.1f}%)")
        print(f"Failed:  {len(self.failed)}")
        print(f"Skipped: {len(self.skipped)}")

        if self.failed:
            print("\nFailed Tests:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")

        return len(self.failed) == 0


def test_imports(results: TestResults):
    """Test 1: Core Module Imports"""
    print("\n[Test 1] Core Module Imports")

    try:
        from config import load_config, SystemConfig
        results.add_pass("config module import")
    except Exception as e:
        results.add_fail("config module import", str(e))

    try:
        from qdrant_store import QdrantVectorStore, SearchResult
        results.add_pass("qdrant_store module import")
    except Exception as e:
        results.add_fail("qdrant_store module import", str(e))

    try:
        from vllm_client import VLLMClient
        results.add_pass("vllm_client module import")
    except Exception as e:
        results.add_fail("vllm_client module import", str(e))

    try:
        from llm_factory import create_llm, get_llm_type
        results.add_pass("llm_factory module import")
    except Exception as e:
        results.add_fail("llm_factory module import", str(e))

    try:
        from embedding_cache import EmbeddingCache, CachedEmbeddings
        results.add_pass("embedding_cache module import")
    except Exception as e:
        results.add_fail("embedding_cache module import", str(e))


def test_config_system(results: TestResults):
    """Test 2: Configuration System"""
    print("\n[Test 2] Configuration System")

    try:
        from config import load_config
        config = load_config()

        # Check default values
        assert hasattr(config, 'use_qdrant'), "use_qdrant flag missing"
        assert hasattr(config, 'use_vllm'), "use_vllm flag missing"
        assert config.use_qdrant == False, "use_qdrant should default to False"
        assert config.use_vllm == False, "use_vllm should default to False"

        results.add_pass("config loading and defaults")
    except Exception as e:
        results.add_fail("config loading and defaults", str(e))

    try:
        from config import load_config
        config = load_config()

        # Check Qdrant config exists
        assert hasattr(config, 'qdrant'), "Qdrant config missing"
        assert config.qdrant.host == "localhost", "Qdrant host incorrect"
        assert config.qdrant.port == 6333, "Qdrant port incorrect"

        results.add_pass("Qdrant configuration")
    except Exception as e:
        results.add_fail("Qdrant configuration", str(e))

    try:
        from config import load_config
        config = load_config()

        # Check vLLM config exists
        assert hasattr(config, 'vllm'), "vLLM config missing"
        assert config.vllm.host, "vLLM host missing"
        assert config.vllm.max_tokens > 0, "vLLM max_tokens invalid"

        results.add_pass("vLLM configuration")
    except Exception as e:
        results.add_fail("vLLM configuration", str(e))


def test_llm_factory(results: TestResults):
    """Test 3: LLM Factory Pattern"""
    print("\n[Test 3] LLM Factory Pattern")

    try:
        from llm_factory import create_llm, get_llm_type
        from config import load_config

        # Test with Ollama (default)
        config = load_config()
        config.use_vllm = False

        llm = create_llm(config, test_connection=False)
        llm_type = get_llm_type(llm)

        assert llm_type == "ollama", f"Expected 'ollama', got '{llm_type}'"

        results.add_pass("LLM factory with Ollama")
    except Exception as e:
        results.add_fail("LLM factory with Ollama", str(e))

    try:
        from vllm_client import VLLMClient

        # Test VLLMClient instantiation
        client = VLLMClient(
            host="http://localhost:8000",
            model_name="test-model",
            temperature=0.0
        )

        assert client.host == "http://localhost:8000"
        assert client.model_name == "test-model"
        assert client.temperature == 0.0

        results.add_pass("VLLMClient instantiation")
    except Exception as e:
        results.add_fail("VLLMClient instantiation", str(e))


def test_qdrant_store_class(results: TestResults):
    """Test 4: Qdrant Store Class Structure"""
    print("\n[Test 4] Qdrant Store Class Structure")

    try:
        from qdrant_store import QdrantVectorStore, SearchResult

        # Test class instantiation (without connection)
        store = QdrantVectorStore(
            host="localhost",
            port=6333,
            collection_name="test_collection",
            vector_size=768
        )

        assert store.collection_name == "test_collection"
        assert store.vector_size == 768

        results.add_pass("QdrantVectorStore instantiation")
    except Exception as e:
        results.add_fail("QdrantVectorStore instantiation", str(e))

    try:
        from qdrant_store import SearchResult

        # Test SearchResult dataclass
        result = SearchResult(
            id=1,
            score=0.95,
            text="test content",
            metadata={"key": "value"}
        )

        assert result.id == 1
        assert result.score == 0.95
        assert result.text == "test content"
        assert result.metadata["key"] == "value"

        results.add_pass("SearchResult dataclass")
    except Exception as e:
        results.add_fail("SearchResult dataclass", str(e))


def test_embedding_cache_class(results: TestResults):
    """Test 5: Embedding Cache Class Structure"""
    print("\n[Test 5] Embedding Cache Class Structure")

    try:
        from embedding_cache import EmbeddingCache

        # Test class instantiation (without Redis)
        cache = EmbeddingCache(
            redis_url="redis://localhost:6379",
            ttl=3600,
            key_prefix="test:",
            max_cache_size=1000
        )

        assert cache.ttl == 3600
        assert cache.key_prefix == "test:"
        assert cache.max_cache_size == 1000

        results.add_pass("EmbeddingCache instantiation")
    except Exception as e:
        results.add_fail("EmbeddingCache instantiation", str(e))

    try:
        from embedding_cache import EmbeddingCache

        cache = EmbeddingCache()

        # Test key generation (doesn't require Redis)
        key1 = cache._key("test text")
        key2 = cache._key("test text")
        key3 = cache._key("different text")

        assert key1 == key2, "Same text should produce same key"
        assert key1 != key3, "Different text should produce different key"
        assert key1.startswith("emb:v1:"), "Key should have correct prefix"

        results.add_pass("Cache key generation")
    except Exception as e:
        results.add_fail("Cache key generation", str(e))


def test_app_integration(results: TestResults):
    """Test 6: App Integration Points (DEPRECATED - Gradio app removed)"""
    print("\n[Test 6] App Integration Points (SKIPPED - Legacy Gradio)")

    results.add_skip(
        "VectorStoreAdapter class",
        "Legacy Gradio app (_src/app.py) - Use FastAPI backend instead"
    )
    results.add_skip(
        "EnterpriseRAGSystem instantiation",
        "Legacy Gradio app (_src/app.py) - Use FastAPI backend instead"
    )

    # Note: The production FastAPI backend doesn't import Gradio
    # It uses backend/app/core/rag_engine.py which is Gradio-free


def test_migration_script(results: TestResults):
    """Test 7: Migration Script Structure"""
    print("\n[Test 7] Migration Script Structure")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "migrate_chromadb_to_qdrant",
            "scripts/migrate_chromadb_to_qdrant.py"
        )
        module = importlib.util.module_from_spec(spec)

        # Just check if it can be loaded
        assert spec is not None
        assert module is not None

        results.add_pass("Migration script loadable")
    except Exception as e:
        results.add_fail("Migration script loadable", str(e))


def main():
    print("=" * 70)
    print("MANUAL VALIDATION TEST SUITE")
    print("=" * 70)
    print("\nTesting production infrastructure without external services...")

    results = TestResults()

    test_imports(results)
    test_config_system(results)
    test_llm_factory(results)
    test_qdrant_store_class(results)
    test_embedding_cache_class(results)
    test_app_integration(results)
    test_migration_script(results)

    success = results.summary()

    if success:
        print("\nAll validation tests passed!")
        print("\nNext steps:")
        print("1. Start external services (Redis, Qdrant) for integration tests")
        print("2. Run: python tests/run_tests.py integration")
        print("3. Run: python tests/performance/benchmark_vectordb.py")
        return 0
    else:
        print("\nSome tests failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
