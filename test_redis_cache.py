"""Test Redis caching performance with proper conversation clearing"""
import time
import requests
import json

base_url = "http://localhost:7860"

def clear_conversation():
    """Clear conversation memory"""
    clear_url = f"{base_url}/gradio_api/call/clear_chat"
    response = requests.post(clear_url, json={"data": []})
    print(f"  Conversation cleared: {response.status_code}")
    return response.status_code == 200

def test_query(query_text, test_name):
    """Test a single query and measure response time"""
    print(f"\n{test_name}")
    print(f"  Query: {query_text}")

    # Start timing
    start = time.time()

    # Submit query
    submit_url = f"{base_url}/gradio_api/call/respond"
    response = requests.post(
        submit_url,
        json={"data": [query_text, []]},
        timeout=60
    )

    if response.status_code != 200:
        print(f"  ERROR: Submit failed with {response.status_code}")
        return None

    event_id = response.json().get("event_id")

    # Get result
    result_url = f"{base_url}/gradio_api/call/respond/{event_id}"

    # Poll for result
    found = False
    while time.time() - start < 60:
        result_response = requests.get(result_url)

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
                                elapsed = time.time() - start
                                print(f"  Response time: {elapsed:.3f}s")
                                found = True
                                return elapsed
            if found:
                break

        time.sleep(0.5)

    print(f"  ERROR: Timeout after {time.time() - start:.3f}s")
    return None

# Test plan
print("=" * 60)
print("REDIS CACHE PERFORMANCE TEST")
print("=" * 60)

test_query_text = "What is the dress code policy?"

# Test 1: Cold query (no cache)
clear_conversation()
time.sleep(1)
cold_time = test_query(test_query_text, "Test 1: Cold Query (no cache)")

# Test 2: Same query immediately after (should be cache hit)
# Don't clear conversation to test exact same enhanced_query
time.sleep(2)
warm_time_1 = test_query(test_query_text, "Test 2: Warm Cache (same conversation)")

# Test 3: Clear conversation and query again (semantic cache should still hit)
clear_conversation()
time.sleep(1)
semantic_cache_time = test_query(test_query_text, "Test 3: Semantic Cache (cleared conversation)")

# Test 4: Different query to populate cache
clear_conversation()
time.sleep(1)
different_time = test_query("What are the uniform requirements?", "Test 4: Different Query")

# Test 5: Repeat the different query (cache hit)
time.sleep(2)
warm_time_2 = test_query("What are the uniform requirements?", "Test 5: Warm Cache (different query)")

# Summary
print("\n" + "=" * 60)
print("PERFORMANCE SUMMARY")
print("=" * 60)
if cold_time:
    print(f"Cold query (no cache):     {cold_time:.3f}s")
if warm_time_1:
    print(f"Warm cache (same context): {warm_time_1:.3f}s")
    if cold_time:
        speedup = cold_time / warm_time_1
        print(f"  Speedup: {speedup:.1f}x")
if semantic_cache_time:
    print(f"Semantic cache (cleared):  {semantic_cache_time:.3f}s")
    if cold_time:
        speedup = cold_time / semantic_cache_time
        print(f"  Speedup: {speedup:.1f}x")
if different_time and warm_time_2:
    speedup = different_time / warm_time_2
    print(f"\nDifferent query speedup:   {speedup:.1f}x")

print("=" * 60)
