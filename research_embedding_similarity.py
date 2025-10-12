"""
Research: Embedding Similarity Analysis
Goal: Understand why 0.95 threshold matches unrelated queries
"""
import requests
import numpy as np
from typing import List, Tuple

OLLAMA_URL = "http://localhost:11434"

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

# Test queries
test_queries = {
    "base": "How does the Air Force define social functions and what are some examples of events that fall under this category?",
    "similar_1": "What are Air Force social functions?",
    "similar_2": "Define social functions in the Air Force",
    "different_topic_1": "Is it permissible for a service member to wear cold weather headbands on the OCP uniform?",
    "different_topic_2": "can i grow a beard",
    "different_topic_3": "am i allowed to grow a beard",
    "random_1": "test",
    "random_2": "hello world",
    "different_topic_4": "What are the uniform requirements?",
    "different_topic_5": "What is the dress code policy?",
}

print("=" * 80)
print("EMBEDDING SIMILARITY ANALYSIS")
print("=" * 80)
print("\nBase Query:")
print(f"  '{test_queries['base']}'")
print()

# Get base embedding
base_embedding = get_embedding(test_queries["base"])

# Calculate similarities
results = []
for key, query in test_queries.items():
    if key == "base":
        continue

    embedding = get_embedding(query)
    similarity = cosine_similarity(base_embedding, embedding)
    results.append((key, query, similarity))

# Sort by similarity
results.sort(key=lambda x: x[2], reverse=True)

# Display results
print(f"{'Category':<20} {'Similarity':<12} {'Query'}")
print("-" * 80)

for key, query, sim in results:
    category = "SIMILAR" if "similar" in key else "DIFFERENT" if "different" in key else "RANDOM"
    match_indicator = "[MATCH]" if sim >= 0.95 else "[NO MATCH]"
    print(f"{category:<20} {sim:.6f} {match_indicator:<12} {query[:50]}")

print()
print("=" * 80)
print("ANALYSIS")
print("=" * 80)

# Group by match status
matches_at_95 = [r for r in results if r[2] >= 0.95]
no_match = [r for r in results if r[2] < 0.95]

print(f"\n[+] WOULD MATCH at 0.95 threshold: {len(matches_at_95)}")
for key, query, sim in matches_at_95:
    print(f"  - {sim:.6f}: {query[:60]}")

print(f"\n[-] Would NOT match at 0.95 threshold: {len(no_match)}")
for key, query, sim in no_match[:5]:  # Show top 5
    print(f"  - {sim:.6f}: {query[:60]}")

# Statistical analysis
all_sims = [r[2] for r in results]
print(f"\n[STATS] Statistics:")
print(f"  Mean similarity: {np.mean(all_sims):.6f}")
print(f"  Std deviation: {np.std(all_sims):.6f}")
print(f"  Min similarity: {np.min(all_sims):.6f}")
print(f"  Max similarity: {np.max(all_sims):.6f}")
print(f"  Median similarity: {np.median(all_sims):.6f}")

# Recommend threshold
similar_sims = [r[2] for r in results if "similar" in r[0]]
different_sims = [r[2] for r in results if "different" in r[0] or "random" in r[0]]

if similar_sims and different_sims:
    min_similar = min(similar_sims)
    max_different = max(different_sims)

    print(f"\n[*] Threshold Analysis:")
    print(f"  Lowest SIMILAR query: {min_similar:.6f}")
    print(f"  Highest DIFFERENT query: {max_different:.6f}")
    print(f"  Gap: {min_similar - max_different:.6f}")

    if min_similar > max_different:
        recommended = (min_similar + max_different) / 2
        print(f"\n[!] Recommended threshold: {recommended:.6f}")
        print(f"   (Safely between similar and different queries)")
    else:
        print(f"\n[WARNING] OVERLAP DETECTED! Similar and different queries overlap in similarity.")
        print(f"   No safe threshold exists - semantic caching may be fundamentally flawed.")

print("\n" + "=" * 80)
