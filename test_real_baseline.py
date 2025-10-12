"""
Real Baseline Test
Tests actual performance with conversation clearing
Tests Redis caching by running queries twice
"""
import time
import requests
import json
from statistics import mean, median

API_URL = "http://localhost:7860/gradio_api/call/respond"
CLEAR_URL = "http://localhost:7860/gradio_api/call/clear_chat"

# Smaller set of test queries for initial baseline
TEST_QUERIES = [
    "What is the dress code policy?",
    "Who can approve leave requests?",
    "What are the uniform requirements?",
]

def clear_conversation():
    """Clear conversation memory"""
    try:
        response = requests.post(CLEAR_URL, json={"data": []}, timeout=10)
        if response.status_code == 200:
            event_id = response.json().get("event_id")
            if event_id:
                result_url = f"{CLEAR_URL}/{event_id}"
                requests.get(result_url, timeout=10)
        time.sleep(0.5)  # Give it a moment
        return True
    except Exception as e:
        print(f"Clear failed: {e}")
        return False

def query_rag(question, timeout=300):
    """Query RAG system with timeout"""
    start_time = time.time()

    try:
        response = requests.post(API_URL, json={"data": [question, []]}, timeout=10)

        if response.status_code != 200:
            return None, None

        event_id = response.json()["event_id"]
        result_url = f"{API_URL}/{event_id}"

        # Poll for result
        while time.time() - start_time < timeout:
            try:
                result_response = requests.get(result_url, timeout=5)

                if result_response.status_code == 200:
                    lines = result_response.text.strip().split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            data = json.loads(line[6:])
                            if isinstance(data, list) and len(data) > 0:
                                history = data[0]
                                if isinstance(history, list) and len(history) > 0:
                                    last_msg = history[-1]
                                    if isinstance(last_msg, dict) and last_msg.get('role') == 'assistant':
                                        elapsed = time.time() - start_time
                                        return last_msg.get('content', ''), elapsed
            except:
                pass

            time.sleep(0.5)

        return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def main():
    print("="*80)
    print("REAL BASELINE TEST")
    print("="*80)
    print("Phase 1: Cold cache (first run)")
    print("Phase 2: Warm cache (second run)")
    print("="*80)
    print()

    cold_results = []
    warm_results = []

    # Phase 1: Cold cache
    print("PHASE 1: COLD CACHE")
    print("-" * 80)
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] {query[:60]}...")
        clear_conversation()

        response, elapsed = query_rag(query)

        if response and elapsed:
            print(f"  Time: {elapsed:.2f}s")
            safe = response.encode('ascii', 'ignore').decode('ascii')[:80]
            print(f"  Answer: {safe}...")
            cold_results.append({'query': query, 'time': elapsed, 'response': response})
        else:
            print(f"  FAILED or TIMEOUT")
            cold_results.append({'query': query, 'time': None, 'response': None})
        print()

    # Phase 2: Warm cache (same queries again)
    print("\nPHASE 2: WARM CACHE (testing Redis)")
    print("-" * 80)
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] {query[:60]}...")
        clear_conversation()

        response, elapsed = query_rag(query)

        if response and elapsed:
            print(f"  Time: {elapsed:.2f}s")
            safe = response.encode('ascii', 'ignore').decode('ascii')[:80]
            print(f"  Answer: {safe}...")
            warm_results.append({'query': query, 'time': elapsed, 'response': response})
        else:
            print(f"  FAILED or TIMEOUT")
            warm_results.append({'query': query, 'time': None, 'response': None})
        print()

    # Analysis
    print("="*80)
    print("RESULTS")
    print("="*80)

    cold_times = [r['time'] for r in cold_results if r['time'] is not None]
    warm_times = [r['time'] for r in warm_results if r['time'] is not None]

    print(f"Cold Cache ({len(cold_times)}/{len(TEST_QUERIES)} successful):")
    if cold_times:
        print(f"  Mean: {mean(cold_times):.2f}s")
        print(f"  Median: {median(cold_times):.2f}s")
        print(f"  Min: {min(cold_times):.2f}s")
        print(f"  Max: {max(cold_times):.2f}s")

    print(f"\nWarm Cache ({len(warm_times)}/{len(TEST_QUERIES)} successful):")
    if warm_times:
        print(f"  Mean: {mean(warm_times):.2f}s")
        print(f"  Median: {median(warm_times):.2f}s")
        print(f"  Min: {min(warm_times):.2f}s")
        print(f"  Max: {max(warm_times):.2f}s")

    if cold_times and warm_times:
        improvement = ((mean(cold_times) - mean(warm_times)) / mean(cold_times)) * 100
        speedup = mean(cold_times) / mean(warm_times)
        print(f"\nCache Performance:")
        print(f"  Improvement: {improvement:.1f}%")
        print(f"  Speedup: {speedup:.2f}x")

    print("="*80)

    # Save results
    with open('logs/real_baseline_test.json', 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_type': 'cold_vs_warm_cache',
            'queries': TEST_QUERIES,
            'cold_cache_results': cold_results,
            'warm_cache_results': warm_results,
            'statistics': {
                'cold_mean': mean(cold_times) if cold_times else None,
                'warm_mean': mean(warm_times) if warm_times else None,
                'improvement_percent': improvement if cold_times and warm_times else None,
                'speedup': speedup if cold_times and warm_times else None
            }
        }, f, indent=2)

    print("Results saved to logs/real_baseline_test.json")

if __name__ == "__main__":
    main()
