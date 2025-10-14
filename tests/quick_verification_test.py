"""
Quick Verification Test - Validate Agent 3's Fixes
Tests 10 queries to verify evaluation fixes reveal true accuracy
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from run_baseline_test import BaselineAccuracyTester
import json

def quick_test():
    print("=" * 80)
    print("QUICK VERIFICATION TEST - Agent 3 Fixes Applied")
    print("=" * 80)
    print()
    print("Testing 10 queries to verify evaluation fixes...")
    print()

    # Load test suite
    with open('tests/retrieval_test_suite.json', 'r') as f:
        test_suite = json.load(f)

    # Take first 10 queries
    test_queries = test_suite['test_queries'][:10]

    # Initialize tester
    tester = BaselineAccuracyTester('tests/retrieval_test_suite.json')
    tester.test_suite = test_suite
    tester.results['total_queries'] = 10

    # Test Simple mode only
    print("Testing SIMPLE MODE (10 queries)...")
    print()

    mode_results = []
    for i, test_case in enumerate(test_queries, 1):
        print(f"[{i}/10] {test_case['query'][:60]}...")

        # Run query
        query_result = tester.run_test_query(test_case, 'simple')

        # Evaluate with FIXED evaluation logic
        evaluation = tester.evaluate_answer(query_result)
        query_result['evaluation'] = evaluation

        mode_results.append(query_result)

        # Show result
        result = evaluation['result']
        sim = evaluation['semantic_similarity']
        recall = evaluation['source_recall']
        print(f"  [{result}] Similarity: {sim:.2f}, Source Recall: {recall:.2f}")
        print()

    # Calculate metrics
    metrics = tester.calculate_mode_metrics(mode_results)

    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    print(f"Overall Accuracy: {metrics['overall_accuracy']:.1%} (was 5% before)")
    print(f"Pass: {metrics['pass']}, Partial: {metrics['partial']}, Fail: {metrics['fail']}")
    print(f"Avg Semantic Similarity: {metrics['avg_semantic_similarity']:.2f}")
    print(f"Avg Source Recall: {metrics['avg_source_recall']:.2f}")
    print()

    if metrics['overall_accuracy'] >= 0.70:
        print("[SUCCESS] Fixes revealed TRUE baseline of 70%+!")
        print("Agent 3 was correct - the system works, evaluation was broken!")
    elif metrics['overall_accuracy'] >= 0.50:
        print("[PARTIAL] Fixes improved accuracy to 50-70%")
        print("Some improvement, but may need additional tuning")
    else:
        print("[WARNING] Accuracy still <50%")
        print("May need to investigate further")

    print()
    print("=" * 80)

    # Save quick results
    with open('logs/quick_verification_results.json', 'w') as f:
        json.dump({
            "test_count": 10,
            "mode": "simple",
            "metrics": metrics,
            "results": mode_results
        }, f, indent=2)

    print("Results saved to: logs/quick_verification_results.json")
    print("=" * 80)

if __name__ == "__main__":
    quick_test()
