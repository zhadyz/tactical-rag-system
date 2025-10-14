"""
Test Environment Checker
Verifies that all required services and dependencies are available
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version: {version.major}.{version.minor}.{version.micro} (need 3.8+)")
        return False


def check_dependency(package: str, import_name: str = None) -> bool:
    """Check if Python package is installed"""
    if import_name is None:
        import_name = package

    try:
        __import__(import_name)
        print(f"✅ {package}")
        return True
    except ImportError:
        print(f"❌ {package} (install with: pip install {package})")
        return False


def check_service(name: str, host: str, port: int, check_func) -> bool:
    """Check if service is running"""
    try:
        check_func()
        print(f"✅ {name} ({host}:{port})")
        return True
    except Exception as e:
        print(f"❌ {name} ({host}:{port}) - {str(e)[:50]}")
        return False


def check_redis():
    """Check Redis connection"""
    import redis
    client = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
    client.ping()


def check_qdrant():
    """Check Qdrant connection"""
    from qdrant_client import QdrantClient
    client = QdrantClient(host="localhost", port=6333, timeout=2)
    client.get_collections()


def check_ollama():
    """Check Ollama connection"""
    import requests
    response = requests.get("http://localhost:11434/api/tags", timeout=2)
    response.raise_for_status()


def main():
    """Main environment check"""
    print("="*80)
    print("TEST ENVIRONMENT CHECKER")
    print("="*80)

    results = []

    # Python version
    print("\n[1/4] Checking Python version...")
    results.append(check_python_version())

    # Core dependencies
    print("\n[2/4] Checking Python dependencies...")
    core_deps = [
        ("pytest", "pytest"),
        ("pytest-asyncio", "pytest_asyncio"),
        ("pytest-cov", "pytest_cov"),
        ("numpy", "numpy"),
        ("requests", "requests"),
    ]

    for package, import_name in core_deps:
        results.append(check_dependency(package, import_name))

    # Optional dependencies
    print("\n[3/4] Checking optional dependencies...")
    optional_deps = [
        ("redis", "redis"),
        ("qdrant-client", "qdrant_client"),
        ("chromadb", "chromadb"),
        ("langchain", "langchain"),
        ("sentence-transformers", "sentence_transformers"),
    ]

    for package, import_name in optional_deps:
        check_dependency(package, import_name)  # Don't affect results

    # Services
    print("\n[4/4] Checking services...")
    services_ok = []

    services_ok.append(check_service(
        "Redis",
        "localhost",
        6379,
        check_redis
    ))

    services_ok.append(check_service(
        "Qdrant",
        "localhost",
        6333,
        check_qdrant
    ))

    services_ok.append(check_service(
        "Ollama",
        "localhost",
        11434,
        check_ollama
    ))

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if all(results):
        print("\n✅ Core dependencies: ALL INSTALLED")
    else:
        print("\n❌ Core dependencies: MISSING")
        print("   Install with: pip install -r tests/requirements-test.txt")

    service_status = sum(services_ok)
    print(f"\n📡 Services: {service_status}/3 available")

    if service_status == 0:
        print("   ⚠️  No services available - unit tests will be limited")
        print("   Start services:")
        print("     Redis:  docker run -d -p 6379:6379 redis:alpine")
        print("     Qdrant: docker run -d -p 6333:6333 qdrant/qdrant")
        print("     Ollama: ollama serve")
    elif service_status < 3:
        print("   ⚠️  Some services unavailable - some tests will be skipped")
    else:
        print("   ✅ All services available")

    print("\n" + "="*80)
    print("TEST CAPABILITIES")
    print("="*80)

    print("\n✅ Can run:")
    print("   - Basic unit tests (no external dependencies)")
    print("   - Fixture tests")
    print("   - Mock-based tests")

    if service_status >= 1:
        print(f"\n✅ Can run with {service_status} service(s):")
        if services_ok[0]:  # Redis
            print("   - Embedding cache tests")
        if services_ok[1]:  # Qdrant
            print("   - Qdrant store tests")
            print("   - Vector DB benchmarks")
        if services_ok[2]:  # Ollama
            print("   - Integration tests")
            print("   - End-to-end tests")

    if service_status == 3:
        print("\n✅ Full test suite available!")
        print("   Run with: python tests/run_tests.py all")

    print("\n" + "="*80)

    # Exit code
    if all(results):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
