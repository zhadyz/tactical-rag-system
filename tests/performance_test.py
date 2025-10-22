"""
Comprehensive Performance Testing Suite for Tactical RAG
Tests cold/warm queries, accuracy, and timing across different query types
"""

import asyncio
import time
import json
from typing import Dict, List
import httpx
from datetime import datetime

# API Configuration
API_URL = "http://localhost:8000"
TIMEOUT = 180  # 3 minutes for complex queries

# Test queries covering different complexity levels
TEST_QUERIES = [
    {
        "id": "simple_1",
        "question": "Can I grow a beard?",
        "expected_keywords": ["beard", "grooming", "authorized", "military"],
        "complexity": "simple",
        "expected_time_cold": 15,
        "expected_time_warm": 10
    },
    {
        "id": "simple_2",
        "question": "What are the requirements for wearing jewelry?",
        "expected_keywords": ["jewelry", "ring", "necklace", "bracelet", "watch", "cuff", "stud", "ankle"],
        "complexity": "simple",
        "expected_time_cold": 15,
        "expected_time_warm": 10
    },
    {
        "id": "moderate_1",
        "question": "What are the hair length requirements for women in the Air Force?",
        "expected_keywords": ["hair", "women", "female", "length", "inches"],
        "complexity": "moderate",
        "expected_time_cold": 20,
        "expected_time_warm": 12
    },
    {
        "id": "moderate_2",
        "question": "What are the rules for wearing civilian clothes in uniform?",
        "expected_keywords": ["civilian", "clothes", "clothing", "uniform", "duty", "authorized", "authorize", "commander"],
        "complexity": "moderate",
        "expected_time_cold": 20,
        "expected_time_warm": 12
    },
    {
        "id": "complex_1",
        "question": "Compare the grooming standards for men versus women regarding hair length and styling",
        "expected_keywords": ["men", "women", "male", "female", "hair", "length", "standard"],
        "complexity": "complex",
        "expected_time_cold": 30,
        "expected_time_warm": 18
    }
]

class PerformanceMetrics:
    """Tracks performance metrics across test runs"""
    def __init__(self):
        self.results = []
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.total_time = 0

    def add_result(self, result: Dict):
        self.results.append(result)
        self.total_queries += 1
        if result["success"]:
            self.successful_queries += 1
            self.total_time += result["elapsed_time"]
        else:
            self.failed_queries += 1

    def get_summary(self) -> Dict:
        if self.successful_queries == 0:
            return {
                "total_queries": self.total_queries,
                "successful": 0,
                "failed": self.failed_queries,
                "success_rate": 0,
                "avg_time": 0,
                "min_time": 0,
                "max_time": 0
            }

        successful_times = [r["elapsed_time"] for r in self.results if r["success"]]

        return {
            "total_queries": self.total_queries,
            "successful": self.successful_queries,
            "failed": self.failed_queries,
            "success_rate": f"{(self.successful_queries / self.total_queries * 100):.1f}%",
            "avg_time": f"{sum(successful_times) / len(successful_times):.2f}s",
            "min_time": f"{min(successful_times):.2f}s",
            "max_time": f"{max(successful_times):.2f}s"
        }


async def clear_conversation():
    """Clear conversation memory before tests"""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(f"{API_URL}/api/conversation/clear")
            return response.status_code == 200
        except Exception as e:
            print(f"Warning: Could not clear conversation: {e}")
            return False


async def run_query(query_data: Dict, mode: str = "simple") -> Dict:
    """
    Run a single query and measure performance

    Returns:
        Dict with keys: success, elapsed_time, answer, sources, error
    """
    start_time = time.time()

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.post(
                f"{API_URL}/api/query",
                json={
                    "question": query_data["question"],
                    "mode": mode,
                    "use_context": False
                }
            )

            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                # Check for expected keywords in answer
                answer_lower = data["answer"].lower()
                keywords_found = sum(1 for kw in query_data["expected_keywords"]
                                    if kw.lower() in answer_lower)
                keyword_match_rate = (keywords_found / len(query_data["expected_keywords"])) * 100

                return {
                    "success": True,
                    "elapsed_time": elapsed_time,
                    "answer": data["answer"],
                    "sources": len(data.get("sources", [])),
                    "confidence": data.get("metadata", {}).get("confidence", 0),
                    "keyword_match_rate": keyword_match_rate,
                    "keywords_found": keywords_found,
                    "keywords_total": len(query_data["expected_keywords"]),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "elapsed_time": elapsed_time,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            elapsed_time = time.time() - start_time
            return {
                "success": False,
                "elapsed_time": elapsed_time,
                "error": str(e)
            }


async def test_cold_queries():
    """Test performance with cold cache (first queries)"""
    print("\n" + "="*70)
    print("COLD QUERY PERFORMANCE TEST (First-Time Queries)")
    print("="*70)

    metrics = PerformanceMetrics()

    for query_data in TEST_QUERIES:
        print(f"\n[{query_data['complexity'].upper()}] {query_data['question']}")
        print("-" * 70)

        # Clear conversation before each query to isolate performance
        await clear_conversation()

        result = await run_query(query_data, mode="simple")
        result["query_id"] = query_data["id"]
        result["complexity"] = query_data["complexity"]

        metrics.add_result(result)

        if result["success"]:
            print(f"[OK] Success in {result['elapsed_time']:.2f}s")
            print(f"  Sources: {result['sources']}")
            print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Keyword Match: {result['keyword_match_rate']:.1f}% ({result['keywords_found']}/{result['keywords_total']})")
            print(f"  Answer: {result['answer'][:100]}...")
        else:
            print(f"[FAIL] Failed: {result['error']}")

    print("\n" + "="*70)
    print("COLD QUERY SUMMARY")
    print("="*70)
    summary = metrics.get_summary()
    for key, value in summary.items():
        print(f"{key:20s}: {value}")

    return metrics.results


async def test_warm_queries():
    """Test performance with warm cache (repeated queries)"""
    print("\n" + "="*70)
    print("WARM QUERY PERFORMANCE TEST (Cache Hit)")
    print("="*70)

    metrics = PerformanceMetrics()

    # Run the same query twice to test cache performance
    test_query = TEST_QUERIES[0]

    print(f"\n[WARM-UP] Running query first time to populate cache...")
    await run_query(test_query, mode="simple")

    print(f"\n[WARM TEST] Running same query to test cache hit...")
    result = await run_query(test_query, mode="simple")
    result["query_id"] = test_query["id"] + "_warm"
    result["complexity"] = "cache_hit"

    metrics.add_result(result)

    if result["success"]:
        print(f"[OK] Cache hit in {result['elapsed_time']:.2f}s")
        print(f"  Sources: {result['sources']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Answer: {result['answer'][:100]}...")
    else:
        print(f"[FAIL] Failed: {result['error']}")

    return metrics.results


async def test_accuracy_validation():
    """Run focused accuracy tests"""
    print("\n" + "="*70)
    print("ACCURACY VALIDATION TEST")
    print("="*70)

    total_queries = len(TEST_QUERIES)
    passed = 0

    for query_data in TEST_QUERIES:
        result = await run_query(query_data, mode="simple")

        if result["success"] and result["keyword_match_rate"] >= 50:  # 50% keyword threshold
            passed += 1
            status = "[OK] PASS"
        else:
            status = "[FAIL] FAIL"

        print(f"{status} | {query_data['id']:15s} | Match: {result.get('keyword_match_rate', 0):.1f}%")

    accuracy = (passed / total_queries) * 100
    print(f"\nAccuracy: {accuracy:.1f}% ({passed}/{total_queries} passed)")

    return accuracy


async def main():
    """Run all performance tests"""
    print("\n" + "="*70)
    print("TACTICAL RAG PERFORMANCE TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # Check backend health
    print("\n[1/4] Checking backend health...")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(f"{API_URL}/api/health")
            if response.status_code == 200:
                health = response.json()
                print(f"[OK] Backend healthy: {health['status']}")
            else:
                print(f"[FAIL] Backend unhealthy: HTTP {response.status_code}")
                return
        except Exception as e:
            print(f"[FAIL] Cannot reach backend: {e}")
            return

    # Run test suites
    print("\n[2/4] Running cold query tests...")
    cold_results = await test_cold_queries()

    print("\n[3/4] Running warm query tests...")
    warm_results = await test_warm_queries()

    print("\n[4/4] Running accuracy validation...")
    accuracy = await test_accuracy_validation()

    # Save results to file
    results = {
        "timestamp": datetime.now().isoformat(),
        "cold_queries": cold_results,
        "warm_queries": warm_results,
        "accuracy": accuracy
    }

    with open("performance_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print(f"Results saved to: performance_test_results.json")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
