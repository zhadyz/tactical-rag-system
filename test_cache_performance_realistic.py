"""
Realistic Cache Performance Test
Simulate RAG system queries to measure cache performance with real patterns
"""

import redis
import requests
import time
from typing import List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_src'))

from cache_next_gen import MultiStageCache

REDIS_HOST = "localhost"
REDIS_PORT = 6379
OLLAMA_URL = "http://localhost:11434"

def get_embedding(text: str) -> List[float]:
    """Get embedding from Ollama"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text},
            timeout=30
        )
        return response.json()["embedding"]
    except Exception as e:
        print(f"[ERROR] Embedding failed: {e}")
        # Return zero vector as fallback
        return [0.0] * 768

# Test queries - diverse topics
test_queries = [
    {
        "question": "What are the grooming standards for male service members?",
        "docs": ["afi_36_2903_grooming", "afi_36_2903_hair", "afi_36_2903_male"],
        "answer": {"answer": "Male grooming standards include: hair must be neat and tapered...", "source": "AFI 36-2903"}
    },
    {
        "question": "Can I wear civilian clothes while on duty?",
        "docs": ["afi_36_2903_civilian", "afi_36_2903_duty", "afi_36_2903_attire"],
        "answer": {"answer": "Civilian clothes are generally not authorized while on duty unless...", "source": "AFI 36-2903"}
    },
    {
        "question": "What is the policy on tattoos in the Air Force?",
        "docs": ["afi_36_2903_tattoos", "afi_36_2903_body_art", "afi_36_2903_standards"],
        "answer": {"answer": "Tattoo policy: Tattoos are authorized but cannot be obscene, discriminatory...", "source": "AFI 36-2903"}
    },
    {
        "question": "Are beards allowed in the military?",
        "docs": ["afi_36_2903_beards", "afi_36_2903_facial_hair", "afi_36_2903_grooming"],
        "answer": {"answer": "Beards are not authorized except for medical or religious accommodation...", "source": "AFI 36-2903"}
    },
    {
        "question": "What are the rules for wearing the dress uniform?",
        "docs": ["afi_36_2903_dress", "afi_36_2903_uniform", "afi_36_2903_occasions"],
        "answer": {"answer": "Service dress uniform wear: Authorized for official functions, ceremonies...", "source": "AFI 36-2903"}
    },
    {
        "question": "Can I have colored hair in the Air Force?",
        "docs": ["afi_36_2903_hair_color", "afi_36_2903_appearance", "afi_36_2903_grooming"],
        "answer": {"answer": "Hair color must look natural. Extreme or faddish colors are prohibited...", "source": "AFI 36-2903"}
    },
    {
        "question": "What are the requirements for physical fitness?",
        "docs": ["afi_36_2905_fitness", "afi_36_2905_testing", "afi_36_2905_standards"],
        "answer": {"answer": "Physical fitness requirements include annual testing with components...", "source": "AFI 36-2905"}
    },
    {
        "question": "Is it permissible to wear earrings while in uniform?",
        "docs": ["afi_36_2903_earrings", "afi_36_2903_jewelry", "afi_36_2903_accessories"],
        "answer": {"answer": "Earrings are not authorized for males in uniform. Females may wear small...", "source": "AFI 36-2903"}
    },
    {
        "question": "What are the standards for military bearing?",
        "docs": ["afi_36_2903_bearing", "afi_36_2903_conduct", "afi_36_2903_professionalism"],
        "answer": {"answer": "Military bearing standards: Maintain professional appearance and conduct...", "source": "AFI 36-2903"}
    },
    {
        "question": "Can I wear a religious head covering with my uniform?",
        "docs": ["afi_36_2903_religious", "afi_36_2903_accommodation", "afi_36_2903_headgear"],
        "answer": {"answer": "Religious accommodations for head coverings may be requested through...", "source": "AFI 36-2903"}
    }
]

print("="*80)
print("REALISTIC CACHE PERFORMANCE TEST")
print("="*80)
print()

# Connect to Redis
print("Connecting to Redis...")
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=False)
try:
    r.ping()
    print("[OK] Redis connected")
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
    validation_threshold=0.80
)

cache.clear()
print("[OK] Cache cleared")
print()

# Test 1: First pass - populate cache (cold queries)
print("="*80)
print("TEST 1: COLD QUERIES (Populating Cache)")
print("="*80)
print()

cold_times = []
for i, query_data in enumerate(test_queries, 1):
    question = query_data["question"]
    docs = query_data["docs"]
    answer = query_data["answer"]

    print(f"[{i}/10] {question[:50]}...")

    # Simulate: Get embedding (part of RAG pipeline)
    embed_start = time.time()
    embedding = get_embedding(question)
    embed_time = time.time() - embed_start

    # Check cache (should be miss)
    cache_start = time.time()
    cached = cache.get(question, docs)
    cache_time = time.time() - cache_start

    # Simulate RAG processing if cache miss
    if cached is None:
        # Simulate: retrieval (50ms) + reranking (100ms) + LLM (2000ms)
        rag_time = 0.050 + 0.100 + 2.000
        time.sleep(rag_time)

        # Store in cache
        cache.put(question, answer, embedding, docs)

        total_time = embed_time + cache_time + rag_time
        print(f"     Time: {total_time:.3f}s (COLD - embed: {embed_time:.3f}s, cache: {cache_time:.3f}s, RAG: {rag_time:.3f}s)")
    else:
        total_time = embed_time + cache_time
        print(f"     Time: {total_time:.3f}s (HIT - unexpected!)")

    cold_times.append(total_time)
    print()

# Test 2: Second pass - test cache hits (warm queries)
print("="*80)
print("TEST 2: WARM QUERIES (Testing Cache Hits)")
print("="*80)
print()

warm_times = []
for i, query_data in enumerate(test_queries, 1):
    question = query_data["question"]
    docs = query_data["docs"]

    print(f"[{i}/10] {question[:50]}...")

    # Check cache (should be HIT via exact match)
    cache_start = time.time()
    cached = cache.get(question, docs)
    cache_time = time.time() - cache_start

    if cached is not None:
        print(f"     Time: {cache_time:.3f}s (CACHED)")
        warm_times.append(cache_time)
    else:
        print(f"     Time: {cache_time:.3f}s (MISS - unexpected!)")
        warm_times.append(cache_time)

    print()

# Test 3: Third pass - variations (testing normalization)
print("="*80)
print("TEST 3: QUERY VARIATIONS (Testing Normalization)")
print("="*80)
print()

variations_times = []
variations = [
    ("what are the grooming standards for male service members?", test_queries[0]["docs"]),  # Lowercase
    ("Can I wear civilian clothes while on duty", test_queries[1]["docs"]),  # No question mark
    ("  What is the policy on tattoos in the Air Force?  ", test_queries[2]["docs"]),  # Extra spaces
]

for i, (variant, docs) in enumerate(variations, 1):
    print(f"[{i}/3] {variant[:50]}...")

    cache_start = time.time()
    cached = cache.get(variant, docs)
    cache_time = time.time() - cache_start

    if cached is not None:
        print(f"     Time: {cache_time:.3f}s (CACHED via normalization)")
        variations_times.append(cache_time)
    else:
        print(f"     Time: {cache_time:.3f}s (MISS)")
        variations_times.append(cache_time)

    print()

# Test 4: Different queries (should be cache misses)
print("="*80)
print("TEST 4: DIFFERENT QUERIES (Should Miss Cache)")
print("="*80)
print()

different_queries = [
    ("What are the requirements for promotion?", ["afi_36_2502_promotion", "afi_36_2502_enlisted"]),
    ("Can I take leave during deployment?", ["afi_36_3003_leave", "afi_36_3003_deployment"]),
    ("What is the dress code for ceremonies?", ["afi_36_2903_ceremonies", "afi_36_2903_dress"]),
]

different_times = []
for i, (question, docs) in enumerate(different_queries, 1):
    print(f"[{i}/3] {question[:50]}...")

    cache_start = time.time()
    cached = cache.get(question, docs)
    cache_time = time.time() - cache_start

    if cached is None:
        print(f"     Time: {cache_time:.3f}s (MISS - correct)")
        different_times.append(cache_time)
    else:
        print(f"     Time: {cache_time:.3f}s (HIT - false match!)")
        different_times.append(cache_time)

    print()

# Summary
print("="*80)
print("PERFORMANCE SUMMARY")
print("="*80)
print()

print(f"Cold query avg: {sum(cold_times)/len(cold_times):.3f}s (range: {min(cold_times):.3f}s - {max(cold_times):.3f}s)")
print(f"Warm query avg: {sum(warm_times)/len(warm_times):.3f}s (range: {min(warm_times):.3f}s - {max(warm_times):.3f}s)")
print(f"Variations avg: {sum(variations_times)/len(variations_times):.3f}s (range: {min(variations_times):.3f}s - {max(variations_times):.3f}s)")
print(f"Different queries avg: {sum(different_times)/len(different_times):.3f}s (range: {min(different_times):.3f}s - {max(different_times):.3f}s)")
print()

speedup_warm = sum(cold_times) / sum(warm_times) if sum(warm_times) > 0 else 0
print(f"Cache speedup (cold → warm): {speedup_warm:.1f}x")
print()

# Cache statistics
print("="*80)
print("CACHE STATISTICS")
print("="*80)
stats = cache.get_stats()
print()
print(f"Exact hits: {stats['exact_hits']}")
print(f"Normalized hits: {stats['normalized_hits']}")
print(f"Semantic hits: {stats['semantic_hits']}")
print(f"Misses: {stats['misses']}")
print(f"Total requests: {stats['total_requests']}")
print(f"Hit rate: {stats['hit_rate']:.1%}")
print()

# Check for false matches
false_matches = sum(1 for _, cached in [(q, cache.get(q[0], q[1])) for q in different_queries] if cached is not None)
print(f"False matches detected: {false_matches}/3 different queries")
if false_matches == 0:
    print("[SUCCESS] No false matches - cache correctness verified!")
else:
    print("[WARNING] False matches detected - review required!")

print()
print("="*80)
