"""
Simple Direct Performance Test
Tests RAG system directly without Gradio API or conversation memory
"""

import asyncio
import time
import json
from statistics import mean, median
import sys
import os

# Add _src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_src'))

from app import create_rag_system
from config import load_config

TEST_QUERIES = [
    "What is the dress code policy?",
    "Who can approve leave requests?",
    "What are the uniform requirements?",
    "When can I wear civilian clothes?",
    "What is the purpose of Protocol?",
]

async def test_query(rag_system, query):
    """Test a single query and measure response time"""
    start_time = time.time()

    try:
        # Query without conversation context
        result = await rag_system.query(query, use_context=False)
        elapsed = time.time() - start_time

        return {
            'query': query,
            'elapsed': elapsed,
            'response': result.get('answer', ''),
            'success': True
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            'query': query,
            'elapsed': elapsed,
            'response': f'ERROR: {str(e)}',
            'success': False
        }

async def main():
    print("="*80)
    print("DIRECT PERFORMANCE TEST - Tactical RAG System")
    print("="*80)
    print("Testing without conversation memory accumulation...")
    print(f"Testing {len(TEST_QUERIES)} queries...")
    print()

    # Initialize RAG system
    config = load_config()
    rag_system = create_rag_system(config)

    results = []

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] Testing: {query[:60]}...")

        result = await test_query(rag_system, query)

        if result['success']:
            print(f"  Response time: {result['elapsed']:.2f}s")
            # Remove Unicode for console
            safe_response = result['response'].encode('ascii', 'ignore').decode('ascii')
            print(f"  Answer: {safe_response[:100]}...")
            results.append(result)
        else:
            print(f"  FAILED: {result['response']}")
            results.append(result)

        print()

    # Statistics
    if results:
        successful_results = [r for r in results if r['success']]
        response_times = [r['elapsed'] for r in successful_results]

        print("="*80)
        print("RESULTS")
        print("="*80)
        print(f"Total queries: {len(results)}")
        print(f"Successful: {len(successful_results)}")
        print(f"Failed: {len(results) - len(successful_results)}")

        if response_times:
            print(f"Mean response time: {mean(response_times):.2f}s")
            print(f"Median response time: {median(response_times):.2f}s")
            print(f"Min: {min(response_times):.2f}s")
            print(f"Max: {max(response_times):.2f}s")

        print("="*80)

        # Save results
        with open('logs/direct_performance_test.json', 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'test_type': 'direct_no_conversation_memory',
                'queries': TEST_QUERIES,
                'results': results,
                'statistics': {
                    'total': len(results),
                    'successful': len(successful_results),
                    'failed': len(results) - len(successful_results),
                    'mean': mean(response_times) if response_times else None,
                    'median': median(response_times) if response_times else None,
                    'min': min(response_times) if response_times else None,
                    'max': max(response_times) if response_times else None
                }
            }, f, indent=2)

        print("Results saved to logs/direct_performance_test.json")

if __name__ == "__main__":
    asyncio.run(main())
