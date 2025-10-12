"""
50-Query Benchmark Suite
Comprehensive performance testing with diverse query types

Generates baseline performance data for optimization tracking
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from app import EnterpriseRAGSystem
from config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 50 diverse queries covering simple, moderate, and complex scenarios
BENCHMARK_QUERIES = [
    # Simple queries (15) - Direct factual questions
    {"query": "Where is the main office located?", "type": "simple"},
    {"query": "Who is the CEO?", "type": "simple"},
    {"query": "When was the company founded?", "type": "simple"},
    {"query": "What is the contact email?", "type": "simple"},
    {"query": "Is there a privacy policy?", "type": "simple"},
    {"query": "Where can I find the terms of service?", "type": "simple"},
    {"query": "What is the company mission?", "type": "simple"},
    {"query": "Who handles customer support?", "type": "simple"},
    {"query": "When are the business hours?", "type": "simple"},
    {"query": "What is the refund policy?", "type": "simple"},
    {"query": "Is there a warranty?", "type": "simple"},
    {"query": "What payment methods are accepted?", "type": "simple"},
    {"query": "Where is shipping available?", "type": "simple"},
    {"query": "What is the company address?", "type": "simple"},
    {"query": "Who founded the company?", "type": "simple"},

    # Moderate queries (20) - Lists, procedures, multi-step info
    {"query": "What are the main product features?", "type": "moderate"},
    {"query": "List all available services", "type": "moderate"},
    {"query": "What are the requirements for enrollment?", "type": "moderate"},
    {"query": "How do I create an account?", "type": "moderate"},
    {"query": "What are the pricing tiers?", "type": "moderate"},
    {"query": "List the key policies mentioned", "type": "moderate"},
    {"query": "What procedures should I follow for returns?", "type": "moderate"},
    {"query": "How many departments are there?", "type": "moderate"},
    {"query": "What certifications does the company have?", "type": "moderate"},
    {"query": "What are the shipping options?", "type": "moderate"},
    {"query": "List the customer support channels", "type": "moderate"},
    {"query": "What are the security features?", "type": "moderate"},
    {"query": "How do I update my account information?", "type": "moderate"},
    {"query": "What are the membership benefits?", "type": "moderate"},
    {"query": "List the available integrations", "type": "moderate"},
    {"query": "What are the system requirements?", "type": "moderate"},
    {"query": "How do I cancel my subscription?", "type": "moderate"},
    {"query": "What are the compliance requirements?", "type": "moderate"},
    {"query": "List all available documentation", "type": "moderate"},
    {"query": "What training resources are available?", "type": "moderate"},

    # Complex queries (15) - Analysis, comparison, reasoning
    {"query": "Compare the benefits of the premium and basic plans", "type": "complex"},
    {"query": "Explain how the review process works and why it's important", "type": "complex"},
    {"query": "Analyze the differences between the old and new procedures", "type": "complex"},
    {"query": "Why should I choose this service over competitors?", "type": "complex"},
    {"query": "How does the security system protect user data and what are the key features?", "type": "complex"},
    {"query": "Explain the relationship between the various departments and their responsibilities", "type": "complex"},
    {"query": "What are the pros and cons of each pricing tier?", "type": "complex"},
    {"query": "How does the onboarding process work from start to finish?", "type": "complex"},
    {"query": "Analyze the impact of recent policy changes on existing customers", "type": "complex"},
    {"query": "Why are certain procedures required and what happens if they're not followed?", "type": "complex"},
    {"query": "Compare the features and limitations of different access levels", "type": "complex"},
    {"query": "Explain the entire lifecycle of a customer request", "type": "complex"},
    {"query": "What are the trade-offs between different implementation strategies?", "type": "complex"},
    {"query": "How do all the components work together to deliver the service?", "type": "complex"},
    {"query": "Analyze the decision-making process for approvals and escalations", "type": "complex"},
]


class BenchmarkRunner:
    """Run comprehensive benchmarks and generate reports"""

    def __init__(self, output_dir: Path = Path("benchmark_results")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.rag_system: EnterpriseRAGSystem = None

    async def initialize(self) -> bool:
        """Initialize RAG system"""

        logger.info("Initializing RAG system for benchmarking...")

        config = load_config()
        self.rag_system = EnterpriseRAGSystem(config)
        success, message = await self.rag_system.initialize()

        if not success:
            logger.error(f"Failed to initialize: {message}")
            return False

        logger.info("RAG system ready for benchmarking")
        return True

    async def run_benchmark(self, version: str = "v3.6") -> Dict:
        """Run full 50-query benchmark"""

        logger.info("="*60)
        logger.info(f"BENCHMARK SUITE - {version}")
        logger.info("="*60)
        logger.info(f"Total queries: {len(BENCHMARK_QUERIES)}")

        # Clear profiler
        if self.rag_system.profiler:
            self.rag_system.profiler.reset()

        # Run all queries
        for i, query_item in enumerate(BENCHMARK_QUERIES, 1):
            query = query_item["query"]
            expected_type = query_item["type"]

            logger.info(f"\n[{i}/{len(BENCHMARK_QUERIES)}] Running: {query[:60]}...")
            logger.info(f"Expected type: {expected_type}")

            try:
                result = await self.rag_system.query(query, use_context=False)

                if result.get("error"):
                    logger.warning(f"Query failed: {result.get('answer')}")
                else:
                    actual_type = result.get("metadata", {}).get("query_type", "unknown")
                    strategy = result.get("metadata", {}).get("strategy_used", "unknown")

                    match = "✓" if actual_type == expected_type else "X"
                    logger.info(f"{match} Actual type: {actual_type} | Strategy: {strategy}")

            except Exception as e:
                logger.error(f"Query exception: {e}")

        # Get profiling results
        if not self.rag_system.profiler:
            logger.error("Profiler not available")
            return {}

        summary = self.rag_system.profiler.get_summary()

        # Save profiles
        profile_file = self.rag_system.profiler.save_profiles(
            filename=f"{version}_profiles.json"
        )

        logger.info(f"\nProfile data saved to: {profile_file}")

        return summary

    def generate_report(self, summary: Dict, version: str = "v3.6") -> None:
        """Generate markdown benchmark report"""

        if not summary:
            logger.error("No summary data to generate report")
            return

        total = summary["total_queries"]
        successful = summary["successful_queries"]
        failed = summary["failed_queries"]
        avg_times = summary.get("average_times", {})

        # Calculate bottleneck
        timing_keys = {k: v for k, v in avg_times.items() if k != "total_ms"}
        if timing_keys:
            bottleneck_stage = max(timing_keys, key=timing_keys.get)
            bottleneck_time = timing_keys[bottleneck_stage]
            total_time = avg_times.get("total_ms", 1)
            bottleneck_pct = (bottleneck_time / total_time) * 100 if total_time > 0 else 0
        else:
            bottleneck_stage = "unknown"
            bottleneck_time = 0
            bottleneck_pct = 0

        report = f"""# Benchmark Report: {version}

**Date:** {summary.get('timestamp', 'N/A')}
**Queries:** {total} total, {successful} successful, {failed} failed

---

## Performance Summary

| Metric | Value |
|--------|-------|
| **Total Queries** | {total} |
| **Success Rate** | {(successful/total*100):.1f}% |
| **Average Total Time** | {avg_times.get('total_ms', 0):.0f}ms ({avg_times.get('total_ms', 0)/1000:.2f}s) |
| **Retrieval Time** | {avg_times.get('retrieval_ms', 0):.0f}ms |
| **LLM Generation Time** | {avg_times.get('llm_ms', 0):.0f}ms |

---

## Bottleneck Analysis

**Primary Bottleneck:** {bottleneck_stage.replace('_ms', '').upper()}

**Time Distribution:**
"""

        # Add time distribution
        if total_time > 0:
            for stage, time_ms in timing_keys.items():
                stage_name = stage.replace('_ms', '').capitalize()
                stage_pct = (time_ms / total_time) * 100
                report += f"- {stage_name}: {stage_pct:.1f}% ({time_ms:.0f}ms)\n"

        report += f"""

**Bottleneck Impact:** {bottleneck_pct:.1f}% of total time

---

## Query Type Breakdown

Analyze detailed profiles in `{version}_profiles.json` for per-query breakdown by type.

---

## Optimization Recommendations

"""

        # Add recommendations based on bottleneck
        if "llm" in bottleneck_stage.lower():
            report += """### LLM is the bottleneck
- Consider prompt optimization to reduce token count
- Implement streaming responses for perceived performance
- Investigate faster LLM models or quantization
- Cache common query patterns aggressively
"""
        elif "retrieval" in bottleneck_stage.lower():
            report += """### Retrieval is the bottleneck
- Optimize vector search with FAISS migration
- Review reranking batch sizes
- Consider reducing K values for simple queries
- Implement semantic caching for common queries
"""
        else:
            report += """### Balanced system
- No single bottleneck dominates
- Focus on incremental optimizations across all stages
- Monitor for regressions in future versions
"""

        report += f"""

---

**Generated by:** Benchmark Suite (ops-perf-001)
**Version:** {version}
**Next Steps:** Compare against future benchmarks to track optimization progress
"""

        # Save report
        report_file = self.output_dir / f"{version}_benchmark_report.md"
        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"Benchmark report saved to: {report_file}")


async def main():
    """Main benchmark execution"""

    runner = BenchmarkRunner()

    # Initialize
    if not await runner.initialize():
        logger.error("Failed to initialize system")
        return

    # Run benchmark
    summary = await runner.run_benchmark(version="v3.6")

    # Generate report
    runner.generate_report(summary, version="v3.6")

    logger.info("\n" + "="*60)
    logger.info("BENCHMARK COMPLETE")
    logger.info("="*60)
    logger.info(f"Total queries: {summary.get('total_queries', 0)}")
    logger.info(f"Successful: {summary.get('successful_queries', 0)}")
    logger.info(f"Average time: {summary.get('average_times', {}).get('total_ms', 0):.0f}ms")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
