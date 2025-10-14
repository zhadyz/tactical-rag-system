"""
Comprehensive Real-World Testing Suite
Executes 60 diverse queries to thoroughly validate RAG system performance
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys

API_URL = "http://localhost:8000/api/query"
TEST_SUITE_PATH = "tests/comprehensive_test_suite.json"
RESULTS_DIR = Path("logs/comprehensive_test")

class ComprehensiveTestRunner:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "comprehensive",
            "total_queries": 0,
            "modes_tested": ["simple", "adaptive"],
            "results": []
        }

        # Load test suite
        with open(TEST_SUITE_PATH, 'r') as f:
            self.test_suite = json.load(f)

        self.total_queries = len(self.test_suite['test_queries'])
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE TEST SUITE - {self.total_queries} QUERIES")
        print(f"{'='*80}\n")

        # Create results directory
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    def test_single_query(self, query_obj, mode):
        """Execute a single query and record results"""
        query_id = query_obj['id']
        query = query_obj['query']
        category = query_obj['category']
        difficulty = query_obj['difficulty']

        print(f"  [{mode.upper()}] {query_id}: {query[:60]}...")

        start_time = time.time()

        try:
            response = requests.post(
                API_URL,
                json={"question": query, "mode": mode},
                timeout=180
            )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                sources = data.get('sources', [])
                metadata = data.get('metadata', {})

                # Determine if answer is valid
                is_error = 'error' in answer.lower() and len(answer) < 100
                is_timeout = 'timeout' in answer.lower()
                is_out_of_scope = 'not covered' in answer.lower() or 'not in' in answer.lower()

                # Expected out-of-scope
                should_be_out_of_scope = category == 'negative_cases'

                # Determine success
                if should_be_out_of_scope:
                    success = is_out_of_scope
                    status = "CORRECT_REJECTION" if is_out_of_scope else "FALSE_POSITIVE"
                elif is_error or is_timeout:
                    success = False
                    status = "ERROR" if is_error else "TIMEOUT"
                else:
                    # Answer provided - assume success if not error
                    success = len(answer) > 20 and len(sources) > 0
                    status = "ANSWERED" if success else "POOR_QUALITY"

                print(f"    [OK] {elapsed:.2f}s | {status} | {len(answer)} chars | {len(sources)} sources")

                result = {
                    "query_id": query_id,
                    "query": query,
                    "category": category,
                    "difficulty": difficulty,
                    "mode": mode,
                    "answer": answer,
                    "answer_length": len(answer),
                    "sources_count": len(sources),
                    "response_time": elapsed,
                    "cache_hit": metadata.get('cache_hit', False),
                    "strategy": metadata.get('strategy_used', 'unknown'),
                    "success": success,
                    "status": status,
                    "is_out_of_scope": is_out_of_scope,
                    "should_be_out_of_scope": should_be_out_of_scope,
                    "error": False
                }

                return result

            else:
                print(f"    [ERR] HTTP {response.status_code}")
                return self._create_error_result(query_obj, mode, f"HTTP {response.status_code}", time.time() - start_time)

        except requests.Timeout:
            print(f"    [TIMEOUT] >180s")
            return self._create_error_result(query_obj, mode, "Timeout", 180)

        except Exception as e:
            print(f"    [ERR] {str(e)[:50]}")
            return self._create_error_result(query_obj, mode, str(e), time.time() - start_time)

    def _create_error_result(self, query_obj, mode, error_msg, elapsed):
        """Create error result object"""
        return {
            "query_id": query_obj['id'],
            "query": query_obj['query'],
            "category": query_obj['category'],
            "difficulty": query_obj['difficulty'],
            "mode": mode,
            "answer": f"ERROR: {error_msg}",
            "answer_length": 0,
            "sources_count": 0,
            "response_time": elapsed,
            "cache_hit": False,
            "strategy": "error",
            "success": False,
            "status": "ERROR",
            "is_out_of_scope": False,
            "should_be_out_of_scope": query_obj['category'] == 'negative_cases',
            "error": True
        }

    def run_all_tests(self):
        """Execute all test queries"""
        print(f"\nTesting {self.total_queries} queries in both modes ({self.total_queries * 2} total requests)")
        print(f"Estimated time: 15-30 minutes\n")

        test_queries = self.test_suite['test_queries']

        for mode in ['simple', 'adaptive']:
            print(f"\n{'='*80}")
            print(f"TESTING {mode.upper()} MODE")
            print(f"{'='*80}\n")

            mode_results = []

            for i, query_obj in enumerate(test_queries, 1):
                print(f"\nQuery {i}/{self.total_queries}")

                result = self.test_single_query(query_obj, mode)
                mode_results.append(result)
                self.results['results'].append(result)

                # Save checkpoint every 10 queries
                if i % 10 == 0:
                    self._save_checkpoint(mode, i)

                # Brief pause to avoid overwhelming system
                time.sleep(0.2)

            # Mode complete summary
            self._print_mode_summary(mode, mode_results)

    def _save_checkpoint(self, mode, query_num):
        """Save intermediate results"""
        checkpoint_file = RESULTS_DIR / f"checkpoint_{mode}_{query_num}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"    [CHECKPOINT] Saved at query {query_num}")

    def _print_mode_summary(self, mode, results):
        """Print summary statistics for a mode"""
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        errors = sum(1 for r in results if r['error'])
        timeouts = sum(1 for r in results if r['status'] == 'TIMEOUT')
        out_of_scope_correct = sum(1 for r in results if r['should_be_out_of_scope'] and r['is_out_of_scope'])
        out_of_scope_total = sum(1 for r in results if r['should_be_out_of_scope'])

        avg_time = sum(r['response_time'] for r in results) / total if total > 0 else 0
        cache_hits = sum(1 for r in results if r['cache_hit'])

        print(f"\n{'-'*80}")
        print(f"{mode.upper()} MODE SUMMARY:")
        print(f"  Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
        print(f"  Errors: {errors}")
        print(f"  Timeouts: {timeouts}")
        print(f"  Out-of-scope handled: {out_of_scope_correct}/{out_of_scope_total}")
        print(f"  Avg Response Time: {avg_time:.2f}s")
        print(f"  Cache Hit Rate: {cache_hits}/{total} ({cache_hits/total*100:.1f}%)")
        print(f"{'-'*80}\n")

    def analyze_results(self):
        """Comprehensive analysis of all results"""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE ANALYSIS")
        print(f"{'='*80}\n")

        # Overall stats
        all_results = self.results['results']
        total = len(all_results)

        # By mode
        simple_results = [r for r in all_results if r['mode'] == 'simple']
        adaptive_results = [r for r in all_results if r['mode'] == 'adaptive']

        simple_success = sum(1 for r in simple_results if r['success'])
        adaptive_success = sum(1 for r in adaptive_results if r['success'])

        print(f"OVERALL RESULTS:")
        print(f"  Total Queries: {total // 2} (x2 modes = {total} requests)")
        print(f"  Simple Mode: {simple_success}/{len(simple_results)} ({simple_success/len(simple_results)*100:.1f}%)")
        print(f"  Adaptive Mode: {adaptive_success}/{len(adaptive_results)} ({adaptive_success/len(adaptive_results)*100:.1f}%)")

        # By category
        print(f"\nBY CATEGORY:")
        categories = defaultdict(lambda: {'simple': [], 'adaptive': []})
        for r in all_results:
            categories[r['category']][r['mode']].append(r['success'])

        for cat in sorted(categories.keys()):
            simple_cat = categories[cat]['simple']
            adaptive_cat = categories[cat]['adaptive']
            simple_rate = sum(simple_cat) / len(simple_cat) * 100 if simple_cat else 0
            adaptive_rate = sum(adaptive_cat) / len(adaptive_cat) * 100 if adaptive_cat else 0

            print(f"  {cat:20s}: Simple {simple_rate:5.1f}% | Adaptive {adaptive_rate:5.1f}%")

        # By difficulty
        print(f"\nBY DIFFICULTY:")
        difficulties = defaultdict(lambda: {'simple': [], 'adaptive': []})
        for r in all_results:
            difficulties[r['difficulty']][r['mode']].append(r['success'])

        for diff in ['easy', 'medium', 'hard']:
            if diff in difficulties:
                simple_diff = difficulties[diff]['simple']
                adaptive_diff = difficulties[diff]['adaptive']
                simple_rate = sum(simple_diff) / len(simple_diff) * 100 if simple_diff else 0
                adaptive_rate = sum(adaptive_diff) / len(adaptive_diff) * 100 if adaptive_diff else 0

                print(f"  {diff.upper():8s}: Simple {simple_rate:5.1f}% | Adaptive {adaptive_rate:5.1f}%")

        # Failures analysis
        print(f"\nFAILURES:")
        simple_failures = [r for r in simple_results if not r['success']]
        adaptive_failures = [r for r in adaptive_results if not r['success']]

        print(f"  Simple Mode Failures: {len(simple_failures)}")
        for f in simple_failures[:10]:  # Show first 10
            print(f"    - {f['query_id']}: {f['query'][:50]}... ({f['status']})")

        print(f"\n  Adaptive Mode Failures: {len(adaptive_failures)}")
        for f in adaptive_failures[:10]:  # Show first 10
            print(f"    - {f['query_id']}: {f['query'][:50]}... ({f['status']})")

        # Performance stats
        print(f"\nPERFORMANCE:")
        simple_times = [r['response_time'] for r in simple_results]
        adaptive_times = [r['response_time'] for r in adaptive_results]

        print(f"  Simple Mode:")
        print(f"    Avg: {sum(simple_times)/len(simple_times):.2f}s")
        print(f"    Min: {min(simple_times):.2f}s")
        print(f"    Max: {max(simple_times):.2f}s")

        print(f"  Adaptive Mode:")
        print(f"    Avg: {sum(adaptive_times)/len(adaptive_times):.2f}s")
        print(f"    Min: {min(adaptive_times):.2f}s")
        print(f"    Max: {max(adaptive_times):.2f}s")

    def save_results(self):
        """Save final results"""
        output_file = RESULTS_DIR / f"comprehensive_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n{'='*80}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*80}\n")

        return output_file

def main():
    """Main execution"""
    try:
        # Check API availability
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code != 200:
            print("ERROR: Backend API is not healthy")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot connect to backend API: {e}")
        sys.exit(1)

    # Run tests
    runner = ComprehensiveTestRunner()
    runner.run_all_tests()
    runner.analyze_results()
    output_file = runner.save_results()

    print(f"\n[COMPLETE] Comprehensive test finished!")
    print(f"  Results: {output_file}")
    print(f"  Total time: {sum(r['response_time'] for r in runner.results['results']):.1f}s")

if __name__ == "__main__":
    main()
