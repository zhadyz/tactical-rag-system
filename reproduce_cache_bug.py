"""
Reproduction Test: Semantic Cache Bug
Goal: Reproduce user's bug under controlled conditions and capture all data

User's Report:
1. Query: "How does the Air Force define 'social functions'..." - Works correctly (3 min)
2. Query: "Is it permissible to wear cold weather headbands..." - WRONG ANSWER (social functions)
3. Query: "can i grow a beard" - WRONG ANSWER (social functions)
4. Query: "test" - WRONG ANSWER (social functions)

Hypothesis: Cache matching logic has a bug that causes false matches
"""
import requests
import redis
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any

# Configuration
OLLAMA_URL = "http://localhost:11434"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
APP_URL = "http://localhost:7860"

def get_embedding(text: str) -> List[float]:
    """Get embedding from Ollama"""
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text}
    )
    return response.json()["embedding"]

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity"""
    a = np.array(vec1)
    b = np.array(vec2)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def inspect_redis_cache(r: redis.Redis) -> List[Dict[str, Any]]:
    """Inspect all semantic cache entries"""
    keys = r.keys("semantic:*")
    entries = []

    for key in keys:
        data = r.get(key)
        if data:
            try:
                entry = json.loads(data)
                entries.append({
                    "key": key.decode(),
                    "query": entry.get("query"),
                    "embedding": entry.get("embedding"),
                    "answer_preview": entry.get("result", {}).get("answer", "")[:100] if isinstance(entry.get("result"), dict) else str(entry.get("result"))[:100]
                })
            except Exception as e:
                print(f"  ERROR reading key {key}: {e}")

    return entries

def query_app(question: str) -> Dict[str, Any]:
    """Query the RAG application via Gradio API"""
    try:
        # Gradio API endpoint for the chat function
        response = requests.post(
            f"{APP_URL}/api/predict",
            json={
                "data": [question, True]  # question, use_context
            }
        )
        return {
            "success": True,
            "answer": response.json()["data"][0],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

print("=" * 80)
print("SEMANTIC CACHE BUG REPRODUCTION TEST")
print("=" * 80)

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=False)

# Clear cache to start fresh
print("\n[1] Clearing Redis cache...")
cache_keys = r.keys("semantic:*")
if cache_keys:
    r.delete(*cache_keys)
    print(f"   Deleted {len(cache_keys)} cache entries")
else:
    print("   Cache already empty")

# Test queries (exact sequence user reported)
test_queries = [
    "How does the Air Force define 'social functions' and what are some examples of events that fall under this category?",
    "Is it permissible for a service member to wear cold weather headbands on the OCP uniform?",
    "can i grow a beard",
    "test"
]

print(f"\n[2] Running test queries...")
results = []

for i, query in enumerate(test_queries, 1):
    print(f"\n--- Query {i} ---")
    print(f"Question: {query[:60]}...")

    # Get embedding for this query BEFORE sending to app
    query_embedding = get_embedding(query)
    print(f"Embedding dimensions: {len(query_embedding)}")

    # Check cache state BEFORE query
    cache_before = inspect_redis_cache(r)
    print(f"Cache entries before: {len(cache_before)}")

    # Calculate similarity to all cached queries
    if cache_before:
        print(f"\nSimilarity to cached queries:")
        for cached in cache_before:
            cached_embedding = cached["embedding"]
            if cached_embedding:
                sim = cosine_similarity(query_embedding, cached_embedding)
                print(f"  vs '{cached['query'][:50]}...'")
                print(f"    Similarity: {sim:.6f} {'[WOULD MATCH at 0.95]' if sim >= 0.95 else '[NO MATCH]'}")

    # Send query to app
    print(f"\nSending query to app...")
    result = query_app(query)

    if result["success"]:
        answer = result["answer"]
        print(f"Answer received: {answer[:100]}...")

        # Check if answer is about social functions (the bug)
        is_social_functions = "social function" in answer.lower()
        is_expected_bug = i > 1 and is_social_functions

        if is_expected_bug:
            print(f"[BUG DETECTED] Query {i} returned social functions answer!")
    else:
        print(f"Query failed: {result['error']}")

    # Check cache state AFTER query
    cache_after = inspect_redis_cache(r)
    print(f"\nCache entries after: {len(cache_after)}")

    results.append({
        "query": query,
        "embedding": query_embedding,
        "result": result,
        "cache_before": len(cache_before),
        "cache_after": len(cache_after)
    })

    print("-" * 80)

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

# Analyze all query pairs
print("\n[3] Cross-query similarity matrix:")
for i in range(len(results)):
    for j in range(i+1, len(results)):
        q1 = results[i]["query"]
        q2 = results[j]["query"]
        emb1 = results[i]["embedding"]
        emb2 = results[j]["embedding"]

        sim = cosine_similarity(emb1, emb2)
        print(f"\nQuery {i+1} vs Query {j+1}:")
        print(f"  '{q1[:40]}...'")
        print(f"  '{q2[:40]}...'")
        print(f"  Similarity: {sim:.6f} {'[MATCH at 0.95]' if sim >= 0.95 else '[NO MATCH]'}")

# Final cache inspection
print("\n[4] Final cache state:")
final_cache = inspect_redis_cache(r)
print(f"\nTotal entries: {len(final_cache)}")
for i, entry in enumerate(final_cache, 1):
    print(f"\nEntry {i}:")
    print(f"  Query: {entry['query'][:60]}...")
    print(f"  Answer: {entry['answer_preview'][:80]}...")
    print(f"  Embedding: {len(entry['embedding'])} dimensions")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

# Check if bug was reproduced
bugs_found = sum(1 for i, r in enumerate(results[1:], 2) if r["result"].get("success") and "social function" in r["result"]["answer"].lower())

if bugs_found > 0:
    print(f"\n[!] BUG REPRODUCED: {bugs_found} queries returned wrong 'social functions' answer")
    print("    This confirms the semantic cache matching logic has a critical bug")
else:
    print(f"\n[?] BUG NOT REPRODUCED: All queries returned appropriate answers")
    print("    The bug may be intermittent or dependent on specific conditions")

print("\n" + "=" * 80)
