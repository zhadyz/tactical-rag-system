"""
Real System Performance Test
Test the actual RAG application with diverse queries and measure response times
"""

import requests
import time
from datetime import datetime

# Configuration
APP_URL = "http://localhost:7860"

# 10 diverse test questions about Air Force regulations
test_questions = [
    "What are the grooming standards for male service members?",
    "Can I wear civilian clothes while on duty?",
    "What is the policy on tattoos in the Air Force?",
    "Are beards allowed in the military?",
    "What are the rules for wearing the dress uniform?",
    "Can I have colored hair in the Air Force?",
    "What are the requirements for physical fitness?",
    "Is it permissible to wear earrings while in uniform?",
    "What are the standards for military bearing?",
    "Can I wear a religious head covering with my uniform?"
]

def query_system(question: str) -> dict:
    """Query the RAG system via Gradio API"""
    try:
        start_time = time.time()

        response = requests.post(
            f"{APP_URL}/api/predict",
            json={
                "data": [question, True]  # question, use_context
            },
            timeout=120
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "answer": result["data"][0],
                "elapsed_seconds": elapsed,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "elapsed_seconds": elapsed,
                "timestamp": datetime.now().isoformat()
            }
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "error": "Timeout (>120s)",
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "error": str(e),
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now().isoformat()
        }

def check_system_ready():
    """Check if RAG system is running"""
    try:
        response = requests.get(APP_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

# Main test
print("="*80)
print("REAL SYSTEM PERFORMANCE TEST")
print("="*80)
print()

# Check system
print("Checking if system is running...")
if not check_system_ready():
    print(f"[ERROR] System not reachable at {APP_URL}")
    print("Please ensure Docker containers are running:")
    print("  docker-compose up -d")
    exit(1)

print(f"[OK] System is running at {APP_URL}")
print()

# Run tests
results = []
total_time = 0
successful_queries = 0

print(f"Testing {len(test_questions)} diverse questions...")
print("-"*80)
print()

for i, question in enumerate(test_questions, 1):
    print(f"[{i}/{len(test_questions)}] {question[:60]}...")

    result = query_system(question)
    results.append({
        "question": question,
        "result": result
    })

    if result["success"]:
        elapsed = result["elapsed_seconds"]
        total_time += elapsed
        successful_queries += 1

        # Show answer preview
        answer = result["answer"]
        answer_preview = answer[:100] + "..." if len(answer) > 100 else answer

        print(f"     Time: {elapsed:.3f}s")
        print(f"     Answer: {answer_preview}")

        # Determine cache status (heuristic: <0.5s likely cached)
        cache_status = "CACHED" if elapsed < 0.5 else "UNCACHED"
        print(f"     Status: {cache_status}")
    else:
        print(f"     ERROR: {result['error']}")

    print()

# Summary statistics
print("="*80)
print("PERFORMANCE SUMMARY")
print("="*80)
print()

print(f"Total queries: {len(test_questions)}")
print(f"Successful: {successful_queries}")
print(f"Failed: {len(test_questions) - successful_queries}")
print()

if successful_queries > 0:
    avg_time = total_time / successful_queries
    min_time = min(r["result"]["elapsed_seconds"] for r in results if r["result"]["success"])
    max_time = max(r["result"]["elapsed_seconds"] for r in results if r["result"]["success"])

    print(f"Average response time: {avg_time:.3f}s")
    print(f"Fastest response: {min_time:.3f}s")
    print(f"Slowest response: {max_time:.3f}s")
    print()

    # Categorize by speed
    fast = sum(1 for r in results if r["result"]["success"] and r["result"]["elapsed_seconds"] < 1.0)
    medium = sum(1 for r in results if r["result"]["success"] and 1.0 <= r["result"]["elapsed_seconds"] < 5.0)
    slow = sum(1 for r in results if r["result"]["success"] and r["result"]["elapsed_seconds"] >= 5.0)

    print(f"Performance breakdown:")
    print(f"  Fast (<1s): {fast} queries ({fast/successful_queries*100:.0f}%)")
    print(f"  Medium (1-5s): {medium} queries ({medium/successful_queries*100:.0f}%)")
    print(f"  Slow (>5s): {slow} queries ({slow/successful_queries*100:.0f}%)")
    print()

    # Detailed results table
    print("Detailed Results:")
    print("-"*80)
    print(f"{'#':<3} {'Time (s)':<10} {'Status':<10} {'Question':<50}")
    print("-"*80)

    for i, item in enumerate(results, 1):
        if item["result"]["success"]:
            elapsed = item["result"]["elapsed_seconds"]
            status = "CACHED" if elapsed < 0.5 else "UNCACHED"
            question_short = item["question"][:47] + "..." if len(item["question"]) > 50 else item["question"]
            print(f"{i:<3} {elapsed:<10.3f} {status:<10} {question_short:<50}")
        else:
            print(f"{i:<3} {'ERROR':<10} {'FAILED':<10} {item['question'][:50]:<50}")

print()
print("="*80)
