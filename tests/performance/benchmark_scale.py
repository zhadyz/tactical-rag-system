"""
Scale Performance Benchmark
Tests system performance at target production scale (500k vectors)
Tests concurrent user load (1, 10, 50, 100 users)
TARGET: <10s P95 latency, handles 100+ concurrent users
"""

import asyncio
import time
import json
import sys
from pathlib import Path
from typing import List, Dict
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_src"))

from config import load_config
from app import EnterpriseRAGSystem


class ScaleBenchmark:
    """Production scale and concurrency benchmark"""

    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_type": "scale_and_concurrency",
            "tests": []
        }

        # Test queries
        self.test_queries = [
            "What are the uniform regulations?",
            "How many days of leave per year?",
            "What are the physical fitness standards?",
            "What is the rank structure in the Air Force?",
            "What are the deployment rotation policies?",
            "What is the process for promotion?",
            "What are the education requirements?",
            "What training is required annually?",
            "What are the housing allowances?",
            "What is the medical benefits policy?"
        ]

    async def initialize_system(self, use_qdrant: bool = False):
        """Initialize RAG system"""
        print(f"Initializing system (Qdrant={use_qdrant})...")

        config = load_config()
        config.use_qdrant = use_qdrant

        system = EnterpriseRAGSystem(config)
        success, message = await system.initialize()

        if not success:
            raise RuntimeError(f"System initialization failed: {message}")

        print("System ready!")
        return system

    async def execute_query(self, system: EnterpriseRAGSystem, query: str) -> Dict:
        """Execute single query and measure performance"""
        start = time.time()

        try:
            result = await system.query(query)
            latency = (time.time() - start) * 1000  # ms

            return {
                "success": not result.get("error", False),
                "latency_ms": latency,
                "answer_length": len(result.get("answer", "")),
                "sources_count": len(result.get("sources", [])),
                "error": None
            }

        except Exception as e:
            latency = (time.time() - start) * 1000
            return {
                "success": False,
                "latency_ms": latency,
                "answer_length": 0,
                "sources_count": 0,
                "error": str(e)
            }

    async def benchmark_single_user(self, system: EnterpriseRAGSystem, num_queries: int = 100) -> Dict:
        """Benchmark single user sequential queries"""
        print(f"\nBenchmarking single user ({num_queries} queries)...")

        results = []
        for i, query in enumerate([self.test_queries[i % len(self.test_queries)] for i in range(num_queries)]):
            result = await self.execute_query(system, query)
            results.append(result)

            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{num_queries} queries completed")

        # Calculate statistics
        latencies = [r["latency_ms"] for r in results if r["success"]]

        if not latencies:
            return {"success": False, "error": "No successful queries"}

        stats = {
            "success": True,
            "total_queries": num_queries,
            "successful_queries": len(latencies),
            "failed_queries": num_queries - len(latencies),
            "p50_latency_ms": statistics.median(latencies),
            "p95_latency_ms": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
            "p99_latency_ms": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
            "avg_latency_ms": statistics.mean(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "queries_per_sec": 1000 / statistics.mean(latencies)
        }

        print(f"  P50 latency: {stats['p50_latency_ms']:.2f}ms")
        print(f"  P95 latency: {stats['p95_latency_ms']:.2f}ms")
        print(f"  P99 latency: {stats['p99_latency_ms']:.2f}ms")
        print(f"  Success rate: {stats['successful_queries']}/{stats['total_queries']}")

        return stats

    async def benchmark_concurrent_users(
        self,
        system: EnterpriseRAGSystem,
        num_users: int,
        queries_per_user: int = 10
    ) -> Dict:
        """Benchmark concurrent users"""
        print(f"\nBenchmarking {num_users} concurrent users ({queries_per_user} queries each)...")

        # Create tasks for all users
        async def user_workload(user_id: int):
            """Simulate single user workload"""
            results = []
            for i in range(queries_per_user):
                query = self.test_queries[(user_id * queries_per_user + i) % len(self.test_queries)]
                result = await self.execute_query(system, query)
                results.append(result)
            return results

        # Execute all users concurrently
        start = time.time()
        user_tasks = [user_workload(i) for i in range(num_users)]
        all_results = await asyncio.gather(*user_tasks, return_exceptions=True)
        total_time = time.time() - start

        # Flatten results
        results = []
        for user_results in all_results:
            if isinstance(user_results, Exception):
                continue
            results.extend(user_results)

        # Calculate statistics
        latencies = [r["latency_ms"] for r in results if r["success"]]

        if not latencies:
            return {"success": False, "error": "No successful queries"}

        total_queries = num_users * queries_per_user

        stats = {
            "success": True,
            "num_users": num_users,
            "total_queries": total_queries,
            "successful_queries": len(latencies),
            "failed_queries": total_queries - len(latencies),
            "total_time_sec": total_time,
            "throughput_qps": total_queries / total_time,
            "p50_latency_ms": statistics.median(latencies),
            "p95_latency_ms": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
            "p99_latency_ms": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
            "avg_latency_ms": statistics.mean(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies)
        }

        print(f"  Total time: {stats['total_time_sec']:.2f}s")
        print(f"  Throughput: {stats['throughput_qps']:.2f} queries/sec")
        print(f"  P95 latency: {stats['p95_latency_ms']:.2f}ms")
        print(f"  Success rate: {stats['successful_queries']}/{stats['total_queries']}")

        return stats

    async def run_benchmark(self):
        """Run complete scale benchmark"""
        print("="*80)
        print("PRODUCTION SCALE & CONCURRENCY BENCHMARK")
        print("="*80)

        # Test configurations
        concurrency_levels = [1, 10, 50, 100]

        # Initialize system
        try:
            system = await self.initialize_system(use_qdrant=True)
        except Exception as e:
            print(f"Failed to initialize Qdrant system: {e}")
            print("Falling back to ChromaDB...")
            system = await self.initialize_system(use_qdrant=False)

        # Single user baseline
        print(f"\n{'='*80}")
        print("TEST 1: Single User Baseline")
        print(f"{'='*80}")

        single_user_stats = await self.benchmark_single_user(system, num_queries=50)
        self.results["tests"].append({
            "test": "single_user",
            "stats": single_user_stats
        })

        # Concurrent users
        for num_users in concurrency_levels[1:]:  # Skip 1 user (already done)
            print(f"\n{'='*80}")
            print(f"TEST: {num_users} Concurrent Users")
            print(f"{'='*80}")

            concurrent_stats = await self.benchmark_concurrent_users(
                system,
                num_users=num_users,
                queries_per_user=10
            )

            self.results["tests"].append({
                "test": f"concurrent_{num_users}_users",
                "stats": concurrent_stats
            })

            # Check if system is degrading
            if concurrent_stats["success"]:
                degradation = concurrent_stats["p95_latency_ms"] / single_user_stats["p95_latency_ms"]
                print(f"  Performance degradation: {degradation:.2f}x")

                if degradation > 5:
                    print("  WARNING: Significant performance degradation detected!")

    def save_results(self):
        """Save benchmark results"""
        output_dir = Path("logs/benchmarks")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"scale_benchmark_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: {output_file}")
        return output_file

    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)

        for test_result in self.results["tests"]:
            test_name = test_result["test"]
            stats = test_result["stats"]

            if not stats.get("success", False):
                print(f"\n{test_name}: FAILED")
                continue

            print(f"\n{test_name}:")
            print(f"  Success rate: {stats['successful_queries']}/{stats['total_queries']}")
            print(f"  P50 latency: {stats['p50_latency_ms']:.2f}ms")
            print(f"  P95 latency: {stats['p95_latency_ms']:.2f}ms")
            print(f"  P99 latency: {stats['p99_latency_ms']:.2f}ms")

            if "throughput_qps" in stats:
                print(f"  Throughput: {stats['throughput_qps']:.2f} queries/sec")

        # Check targets
        print("\n" + "="*80)
        print("TARGET VALIDATION")
        print("="*80)

        single_user = next((t["stats"] for t in self.results["tests"] if t["test"] == "single_user"), None)
        if single_user and single_user.get("success", False):
            p95_ms = single_user["p95_latency_ms"]
            p95_sec = p95_ms / 1000

            print(f"\nP95 Latency: {p95_sec:.2f}s")
            if p95_sec < 10:
                print("  ✓ PASS: Target <10s P95 latency")
            else:
                print("  ✗ FAIL: Target <10s P95 latency")

        # Check 100 users
        hundred_users = next((t["stats"] for t in self.results["tests"] if t["test"] == "concurrent_100_users"), None)
        if hundred_users and hundred_users.get("success", False):
            success_rate = hundred_users["successful_queries"] / hundred_users["total_queries"]
            print(f"\n100 Concurrent Users:")
            print(f"  Success rate: {success_rate*100:.1f}%")
            if success_rate > 0.95:
                print("  ✓ PASS: Handles 100+ concurrent users")
            else:
                print("  ✗ FAIL: Struggles with 100 concurrent users")

        print("\n" + "="*80)


async def main():
    """Main benchmark execution"""
    benchmark = ScaleBenchmark()

    try:
        await benchmark.run_benchmark()
        benchmark.print_summary()
        output_file = benchmark.save_results()
        print(f"\nBenchmark complete! Results: {output_file}")

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted!")
        benchmark.save_results()

    except Exception as e:
        print(f"\nBenchmark failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
