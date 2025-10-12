"""
Investigation: What's actually stored in Redis cache?
Goal: Understand why cache returned wrong answers
"""
import redis
import json
import numpy as np

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)

print("=" * 80)
print("REDIS CACHE INVESTIGATION")
print("=" * 80)

# Get all semantic cache keys
keys = r.keys("semantic:*")
print(f"\nTotal semantic cache entries: {len(keys)}")

# Analyze each entry
for i, key in enumerate(keys[:10]):  # Limit to first 10
    print(f"\n[Entry {i+1}] Key: {key.decode()}")

    # Get the data
    data = r.get(key)

    if data:
        try:
            cache_entry = json.loads(data)

            # Extract info
            query = cache_entry.get("query", "N/A")
            timestamp = cache_entry.get("timestamp", "N/A")
            embedding = cache_entry.get("embedding")
            result = cache_entry.get("result")

            print(f"  Query: {query[:80]}...")
            print(f"  Timestamp: {timestamp}")
            print(f"  Embedding: {len(embedding)} dimensions" if embedding else "  Embedding: None")

            # Check result structure
            if result:
                if isinstance(result, dict):
                    answer = result.get("answer", "")
                    print(f"  Answer preview: {answer[:100]}...")
                else:
                    print(f"  Result type: {type(result)}")

        except json.JSONDecodeError as e:
            print(f"  ERROR: Could not decode JSON - {e}")
        except Exception as e:
            print(f"  ERROR: {e}")

print("\n" + "=" * 80)
print("HYPOTHESIS TESTING")
print("=" * 80)

# Test if there are duplicate/similar queries with high similarity
if len(keys) >= 2:
    print("\nComparing cached query embeddings...")

    entries = []
    for key in keys[:5]:  # Compare first 5
        data = r.get(key)
        if data:
            try:
                entry = json.loads(data)
                entries.append({
                    "query": entry.get("query"),
                    "embedding": entry.get("embedding")
                })
            except:
                pass

    # Calculate similarity between all pairs
    print(f"\nSimilarity matrix between {len(entries)} cached queries:")
    print("-" * 80)

    def cosine_similarity(vec1, vec2):
        a = np.array(vec1)
        b = np.array(vec2)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    for i in range(len(entries)):
        for j in range(i+1, len(entries)):
            q1 = entries[i]["query"]
            q2 = entries[j]["query"]
            emb1 = entries[i]["embedding"]
            emb2 = entries[j]["embedding"]

            if emb1 and emb2:
                sim = cosine_similarity(emb1, emb2)
                print(f"\nQuery 1: {q1[:50]}...")
                print(f"Query 2: {q2[:50]}...")
                print(f"Similarity: {sim:.6f} {'[WOULD MATCH AT 0.95]' if sim >= 0.95 else ''}")

print("\n" + "=" * 80)
