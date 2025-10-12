"""Quick single query test"""
import time
import requests
import json

# Clear conversation first
clear_url = "http://localhost:7860/gradio_api/call/clear_chat"
try:
    resp = requests.post(clear_url, json={"data": []}, timeout=5)
    print(f"Clear response: {resp.status_code}")
except Exception as e:
    print(f"Clear failed: {e}")

# Send query
API_URL = "http://localhost:7860/gradio_api/call/respond"
query = "What is the dress code policy?"

print(f"\nQuerying: {query}")
start_time = time.time()

response = requests.post(API_URL, json={"data": [query, []]})
print(f"POST response: {response.status_code}")

if response.status_code == 200:
    event_id = response.json()["event_id"]
    print(f"Event ID: {event_id}")

    result_url = f"http://localhost:7860/gradio_api/call/respond/{event_id}"

    # Poll for result
    found = False
    while time.time() - start_time < 120:
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
                                elapsed = time.time() - start_time
                                answer = last_msg.get('content', '')
                                print(f"\nResponse time: {elapsed:.2f}s")
                                print(f"Answer: {answer[:200]}...")
                                found = True
                                break
            if found:
                break

        time.sleep(0.5)

    if not found:
        print(f"Timeout or no response after {time.time() - start_time:.2f}s")
