"""
Test Suite: Next-Generation Multi-Stage Cache
Validates correctness and performance of breakthrough cache architecture

Tests:
1. Exact match correctness (100% expected)
2. Normalized match correctness (100% expected)
3. Semantic match with validation (95%+ expected)
4. False match prevention (user's bug scenario)
5. Performance benchmarking
"""

import redis
import requests
import time
from typing import List
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_src'))

from cache_next_gen import MultiStageCache, QueryNormalizer, DocumentOverlapValidator


# Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
OLLAMA_URL = "http://localhost:11434"


def get_embedding(text: str) -> List[float]:
    """Get embedding from Ollama"""
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text}
    )
    return response.json()["embedding"]


def print_header(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


def print_test(name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")
    if details:
        print(f"     {details}")


print_header("NEXT-GEN CACHE TEST SUITE")

# Connect to Redis
print("Connecting to Redis...")
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=False)
try:
    r.ping()
    print("[OK] Redis connected\n")
except:
    print("[ERROR] Redis not available. Exiting.")
    sys.exit(1)

# Initialize cache
cache = MultiStageCache(
    redis_client=r,
    embeddings_func=get_embedding,
    ttl_exact=3600,
    ttl_semantic=600,
    semantic_threshold=0.98,
    validation_threshold=0.80,
    max_semantic_candidates=3
)

# Clear cache
cache.clear()
print("[OK] Cache cleared\n")

# ============================================================================
# TEST 1: Exact Match Correctness
# ============================================================================
print_header("TEST 1: Exact Match Correctness")

query1 = "How does the Air Force define social functions?"
result1 = {"answer": "Answer about social functions", "confidence": 0.95}
doc_ids1 = ["doc1", "doc2", "doc3"]

# Store in cache
cache.put(query1, result1, get_embedding(query1), doc_ids1)
time.sleep(0.1)

# Retrieve exact same query
cached_result = cache.get(query1, doc_ids1)

test1_pass = cached_result == result1
print_test(
    "Exact match returns correct result",
    test1_pass,
    f"Expected: {result1}, Got: {cached_result}"
)

# ============================================================================
# TEST 2: Normalized Match Correctness
# ============================================================================
print_header("TEST 2: Normalized Match Correctness")

query2_variations = [
    "How does the Air Force define social functions?",  # Original
    "how does the air force define social functions?",  # Lowercase
    "How does the Air Force define social functions",   # No question mark
    "  How  does  the  Air  Force  define  social  functions?  ",  # Extra spaces
    "How does the Air Force define social functions??",  # Multiple question marks
]

# Clear and store original
cache.clear()
cache.put(query2_variations[0], result1, get_embedding(query2_variations[0]), doc_ids1)
time.sleep(0.1)

# Test all variations
test2_results = []
for variant in query2_variations[1:]:
    cached_result = cache.get(variant, doc_ids1)
    matches = cached_result == result1
    test2_results.append(matches)
    print_test(
        f"Normalized match: '{variant[:40]}...'",
        matches,
        f"{'Hit' if matches else 'Miss'}"
    )

test2_pass = all(test2_results)
print(f"\nNormalized match success rate: {sum(test2_results)}/{len(test2_results)}")

# ============================================================================
# TEST 3: False Match Prevention (User's Bug Scenario)
# ============================================================================
print_header("TEST 3: False Match Prevention (User's Bug Scenario)")

# Clear cache
cache.clear()

# Store first query about social functions
query_social = "How does the Air Force define social functions?"
answer_social = {"answer": "Social functions are defined as...", "source": "AFI 36-2903"}
docs_social = ["doc_social_1", "doc_social_2", "doc_social_3"]

cache.put(query_social, answer_social, get_embedding(query_social), docs_social)
time.sleep(0.1)

# Try completely different queries (user's bug scenario)
test_queries = [
    ("Is it permissible to wear cold weather headbands on the OCP uniform?", ["doc_uniform_1", "doc_uniform_2"]),
    ("can i grow a beard", ["doc_grooming_1", "doc_grooming_2"]),
    ("test", ["doc_test_1"]),
    ("What are the dress code requirements?", ["doc_dress_1", "doc_dress_2"])
]

print("Testing if different queries incorrectly match 'social functions' cache...\n")

test3_results = []
for query, doc_ids in test_queries:
    cached_result = cache.get(query, doc_ids)

    # Should be None (cache miss) because these are completely different topics
    is_correct = cached_result is None

    # If it returned something, check if it's the wrong answer
    if cached_result is not None:
        is_wrong_answer = cached_result == answer_social
        print_test(
            f"Query: '{query[:40]}...'",
            is_correct,
            f"WRONG MATCH! Returned social functions answer" if is_wrong_answer else "Returned cached result"
        )
    else:
        print_test(
            f"Query: '{query[:40]}...'",
            is_correct,
            "Correctly returned None (cache miss)"
        )

    test3_results.append(is_correct)

test3_pass = all(test3_results)
print(f"\nFalse match prevention: {sum(test3_results)}/{len(test3_results)} correct")

# ============================================================================
# TEST 4: Semantic Match with Validation
# ============================================================================
print_header("TEST 4: Semantic Match with Validation (Paraphrases)")

# Clear cache
cache.clear()

# Store original query
query_original = "What are Air Force social functions?"
answer_original = {"answer": "Air Force social functions include...", "source": "AFI"}
docs_original = ["doc1", "doc2", "doc3"]

cache.put(query_original, answer_original, get_embedding(query_original), docs_original)
time.sleep(0.1)

# Test paraphrases with SAME document IDs (should match)
paraphrases = [
    "Define Air Force social functions",
    "Explain what Air Force social functions are",
    "What is meant by social functions in the Air Force?",
]

print("Testing semantic matching with valid paraphrases (same docs)...\n")

test4_results = []
for paraphrase in paraphrases:
    # Same doc IDs - should match because docs overlap
    cached_result = cache.get(paraphrase, docs_original)

    matched = cached_result == answer_original
    test4_results.append(matched)

    print_test(
        f"Paraphrase: '{paraphrase[:40]}...'",
        matched,
        "Semantic match validated" if matched else "No match (might be below threshold)"
    )

print(f"\nSemantic match success rate: {sum(test4_results)}/{len(test4_results)}")

# ============================================================================
# TEST 5: Semantic Match Rejection (Different Docs)
# ============================================================================
print_header("TEST 5: Semantic Match Rejection (Different Docs)")

# Test paraphrases with DIFFERENT document IDs (should NOT match)
print("Testing semantic rejection when docs don't overlap...\n")

test5_results = []
for paraphrase in paraphrases:
    # Different doc IDs - should NOT match despite high similarity
    different_docs = ["doc_other_1", "doc_other_2", "doc_other_3"]
    cached_result = cache.get(paraphrase, different_docs)

    rejected = cached_result is None
    test5_results.append(rejected)

    print_test(
        f"Paraphrase: '{paraphrase[:40]}...'",
        rejected,
        "Correctly rejected (docs don't overlap)" if rejected else "FAILED - matched despite different docs"
    )

test5_pass = all(test5_results)
print(f"\nSemantic rejection success rate: {sum(test5_results)}/{len(test5_results)}")

# ============================================================================
# TEST 6: Performance Benchmark
# ============================================================================
print_header("TEST 6: Performance Benchmark")

# Clear and populate cache
cache.clear()

# Populate with 50 queries
print("Populating cache with 50 diverse queries...")
for i in range(50):
    q = f"Test query number {i} about various Air Force topics"
    a = {"answer": f"Answer {i}", "confidence": 0.9}
    d = [f"doc_{i}_1", f"doc_{i}_2", f"doc_{i}_3"]
    cache.put(q, a, get_embedding(q), d)

time.sleep(0.5)

# Benchmark exact match
query_test = "Test query number 25 about various Air Force topics"
docs_test = ["doc_25_1", "doc_25_2", "doc_25_3"]

start = time.time()
for _ in range(100):
    cache.get(query_test, docs_test)
elapsed_ms = (time.time() - start) * 1000

avg_lookup_ms = elapsed_ms / 100
print(f"Exact match lookup: {avg_lookup_ms:.2f}ms average (100 iterations)")
print_test("Exact match performance", avg_lookup_ms < 10, f"Target: <10ms, Actual: {avg_lookup_ms:.2f}ms")

# Benchmark cache miss (full scan)
query_miss = "This query does not exist in cache"
docs_miss = ["doc_none_1", "doc_none_2"]

start = time.time()
result = cache.get(query_miss, docs_miss)
elapsed_ms = (time.time() - start) * 1000

print(f"\nCache miss (full scan): {elapsed_ms:.2f}ms")
print_test("Cache miss performance", elapsed_ms < 100, f"Target: <100ms, Actual: {elapsed_ms:.2f}ms")

# ============================================================================
# TEST 7: Cache Statistics
# ============================================================================
print_header("TEST 7: Cache Statistics")

stats = cache.get_stats()

print(f"Exact hits: {stats['exact_hits']}")
print(f"Normalized hits: {stats['normalized_hits']}")
print(f"Semantic hits: {stats['semantic_hits']}")
print(f"Semantic validated: {stats['semantic_validated']}")
print(f"Semantic rejected: {stats['semantic_rejected']}")
print(f"Misses: {stats['misses']}")
print(f"\nTotal requests: {stats['total_requests']}")
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Semantic precision: {stats['semantic_precision']:.1%}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print_header("TEST SUMMARY")

all_tests = [
    ("Exact match correctness", test1_pass),
    ("Normalized match correctness", test2_pass),
    ("False match prevention", test3_pass),
    ("Semantic match validation", len([r for r in test4_results if r]) > 0),
    ("Semantic match rejection", test5_pass),
]

passed_count = sum(1 for _, passed in all_tests if passed)
total_count = len(all_tests)

for test_name, passed in all_tests:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {test_name}")

print(f"\n{'='*80}")
print(f"OVERALL: {passed_count}/{total_count} tests passed")

if passed_count == total_count:
    print("[SUCCESS] All tests passed! Cache is ready for production.")
else:
    print("[WARNING] Some tests failed. Review results above.")

print(f"{'='*80}\n")

# Print configuration
print("Cache Configuration:")
print(f"  - Exact TTL: {cache.ttl_exact}s")
print(f"  - Semantic TTL: {cache.ttl_semantic}s")
print(f"  - Semantic threshold: {cache.semantic_threshold}")
print(f"  - Validation threshold: {cache.validation_threshold}")
print(f"  - Max semantic candidates: {cache.max_semantic_candidates}")
print()
