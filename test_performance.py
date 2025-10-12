"""
Real Performance Testing Script
Queries the actual RAG system via Gradio API and measures response times
"""

import time
import requests
import json
from statistics import mean, median

# Gradio API endpoint - using the /respond endpoint
API_URL = "http://localhost:7860/gradio_api/call/respond"

TEST_QUERIES = [
    "What is the dress code policy?",
    "Who can approve leave requests?",
    "What are the uniform requirements?",
    "When can I wear civilian clothes?",
    "What is the purpose of Protocol?",
]

def clear_conversation():
    """Clear conversation to prevent memory accumulation"""
    try:
        # Call the clear endpoint
        clear_url = "http://localhost:7860/gradio_api/call/clear_chat"
        response = requests.post(clear_url, json={"data": []})
        if response.status_code == 200:
            event_id = response.json().get("event_id")
            if event_id:
                result_url = f"http://localhost:7860/gradio_api/call/clear_chat/{event_id}"
                requests.get(result_url)
        return True
    except Exception as e:
        print(f"Warning: Could not clear conversation: {e}")
        return False

def query_rag(question):
    """Send query to RAG system and measure response time"""

    start_time = time.time()

    # Step 1: Initiate the call
    response = requests.post(
        API_URL,
        json={
            "data": [question, []]  # question, history
        }
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
        return None, None

    event_id = response.json()["event_id"]

    # Step 2: Poll for result
    result_url = f"http://localhost:7860/gradio_api/call/respond/{event_id}"

    while True:
        result_response = requests.get(result_url)

        if result_response.status_code == 200:
            lines = result_response.text.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    # data is [history, ""]
                    # history is a list of messages with role and content
                    if isinstance(data, list) and len(data) > 0:
                        history = data[0]
                        if isinstance(history, list) and len(history) > 0:
                            # Get the last message (assistant's response)
                            last_msg = history[-1]
                            if isinstance(last_msg, dict) and last_msg.get('role') == 'assistant':
                                elapsed = time.time() - start_time
                                return last_msg.get('content', ''), elapsed

        time.sleep(0.1)

        # Timeout after 60 seconds
        if time.time() - start_time > 60:
            return None, None

def main():
    print("="*80)
    print("REAL PERFORMANCE TEST - Tactical RAG System")
    print("="*80)
    print(f"Testing {len(TEST_QUERIES)} queries...")
    print()

    results = []

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] Testing: {query[:60]}...")

        # Clear conversation to prevent memory accumulation
        clear_conversation()

        response, elapsed = query_rag(query)

        if response and elapsed:
            print(f"  Response time: {elapsed:.2f}s")
            # Remove Unicode characters that can't be encoded for console output
            safe_response = response.encode('ascii', 'ignore').decode('ascii')
            print(f"  Answer: {safe_response[:100]}...")
            results.append({
                'query': query,
                'elapsed': elapsed,
                'response': response
            })
        else:
            print(f"  FAILED")

        print()

    # Statistics
    if results:
        response_times = [r['elapsed'] for r in results]

        print("="*80)
        print("RESULTS")
        print("="*80)
        print(f"Total queries: {len(results)}")
        print(f"Mean response time: {mean(response_times):.2f}s")
        print(f"Median response time: {median(response_times):.2f}s")
        print(f"Min: {min(response_times):.2f}s")
        print(f"Max: {max(response_times):.2f}s")
        print("="*80)

        # Save results
        with open('logs/real_performance_test.json', 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'queries': TEST_QUERIES,
                'results': results,
                'statistics': {
                    'mean': mean(response_times),
                    'median': median(response_times),
                    'min': min(response_times),
                    'max': max(response_times)
                }
            }, f, indent=2)

        print("Results saved to logs/real_performance_test.json")

if __name__ == "__main__":
    main()
