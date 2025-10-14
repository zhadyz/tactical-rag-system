"""
Quick Stability Test - Verify Backend with LLM Timeouts

Tests 10 queries to ensure:
1. No indefinite hangs (all complete within 90s)
2. No backend crashes
3. Improved error handling
"""

import requests
import time
import json
from datetime import datetime

API_URL = "http://localhost:8000/api/query"

# Simple test queries from the test suite
TEST_QUERIES = [
    "What about to the colors?",
    "What song is authorized for playing at Air Force ceremonies when colors are presented?",
    "When should the United States flag be flown at half-staff?",
    "What does Taps signify?",
    "What are reveille and retreat?",
    "What is the Air Force Departmental Flag?",
    "What are positional flags?",
    "What are guidons?",
    "What is a CMSAF?",
    "What does AFI stand for?",
]

def test_stability():
    print("=" * 80)
    print("STABILITY TEST - Backend with 60s LLM Timeouts")
    print("=" * 80)
    print(f"Testing {len(TEST_QUERIES)} queries in Simple mode")
    print(f"Expected: All queries complete within 90s (60s LLM + overhead)")
    print()

    results = []
    errors = 0
    timeouts = 0
    successes = 0

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] Testing: {query[:60]}...")

        start = time.time()
        try:
            response = requests.post(
                API_URL,
                json={"question": query, "mode": "simple"},
                timeout=90  # 90s total timeout (60s LLM + 30s overhead)
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                print(f"  [OK] SUCCESS in {elapsed:.1f}s")
                print(f"    Answer: {data['answer'][:100]}...")
                successes += 1
                results.append({
                    "query": query,
                    "status": "success",
                    "time": elapsed,
                    "answer_length": len(data['answer'])
                })
            else:
                print(f"  [ERR] HTTP {response.status_code} in {elapsed:.1f}s")
                errors += 1
                results.append({
                    "query": query,
                    "status": "http_error",
                    "code": response.status_code,
                    "time": elapsed
                })

        except requests.exceptions.Timeout:
            elapsed = time.time() - start
            print(f"  [TIMEOUT] after {elapsed:.1f}s")
            timeouts += 1
            results.append({
                "query": query,
                "status": "timeout",
                "time": elapsed
            })
        except Exception as e:
            elapsed = time.time() - start
            print(f"  [ERR] ERROR after {elapsed:.1f}s: {e}")
            errors += 1
            results.append({
                "query": query,
                "status": "error",
                "error": str(e),
                "time": elapsed
            })

    # Summary
    print("\n" + "=" * 80)
    print("STABILITY TEST RESULTS")
    print("=" * 80)
    print(f"Total Queries: {len(TEST_QUERIES)}")
    print(f"  [OK] Successes: {successes} ({successes/len(TEST_QUERIES)*100:.1f}%)")
    print(f"  [TIMEOUT] Timeouts: {timeouts} ({timeouts/len(TEST_QUERIES)*100:.1f}%)")
    print(f"  [ERR] Errors: {errors} ({errors/len(TEST_QUERIES)*100:.1f}%)")
    print()

    # Calculate stats for successful queries
    success_times = [r['time'] for r in results if r['status'] == 'success']
    if success_times:
        print(f"Response Time Stats (successful queries):")
        print(f"  Min: {min(success_times):.1f}s")
        print(f"  Max: {max(success_times):.1f}s")
        print(f"  Avg: {sum(success_times)/len(success_times):.1f}s")

    print()

    # Assessment
    if successes >= 8:  # 80% success rate
        print("[PASS] Backend is stable (>=80% success rate)")
    elif successes >= 5:  # 50% success rate
        print("[PARTIAL] Backend partially stable (50-80% success)")
    else:
        print("[FAIL] Backend still unstable (<50% success)")

    print()

    # Check for indefinite hangs (>90s)
    long_queries = [r for r in results if r['time'] > 90]
    if long_queries:
        print("[WARNING] Some queries exceeded 90s (may indicate timeout not working):")
        for r in long_queries:
            print(f"  - {r['query'][:50]}: {r['time']:.1f}s")
    else:
        print("[OK] No indefinite hangs detected (all queries < 90s)")

    # Save results
    output = {
        "test_timestamp": datetime.now().isoformat(),
        "total_queries": len(TEST_QUERIES),
        "successes": successes,
        "timeouts": timeouts,
        "errors": errors,
        "success_rate": successes / len(TEST_QUERIES),
        "results": results
    }

    with open('logs/stability_test_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n[SAVED] Results saved to: logs/stability_test_results.json")
    print("=" * 80)

    return successes >= 8

if __name__ == "__main__":
    try:
        success = test_stability()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted by user")
        exit(1)
