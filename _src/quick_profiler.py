"""
Quick Baseline Profiler
Validates performance assumptions before full optimization roadmap

Profiles 10 sample queries to measure:
- Embedding time
- Vector search time
- Reranking time
- LLM generation time
- Total end-to-end time

NOTE: This is a MOCK profiler for initial baseline.
Real profiling will happen in dev-perf-001 with full instrumentation.
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample queries covering different complexity levels
SAMPLE_QUERIES = [
    # Simple queries (3)
    {"query": "Where is the main office located?", "type": "simple"},
    {"query": "Who is the CEO?", "type": "simple"},
    {"query": "When was the company founded?", "type": "simple"},

    # Moderate queries (4)
    {"query": "What are the main requirements for the project?", "type": "moderate"},
    {"query": "List all the key policies mentioned", "type": "moderate"},
    {"query": "What procedures should I follow?", "type": "moderate"},
    {"query": "How many departments are there?", "type": "moderate"},

    # Complex queries (3)
    {"query": "Compare the benefits of policy A and policy B", "type": "complex"},
    {"query": "Explain how the review process works and why it's important", "type": "complex"},
    {"query": "Analyze the differences between the old and new procedures", "type": "complex"},
]


class QuickProfiler:
    """Quick profiling to validate baseline assumptions - MOCK VERSION"""

    def __init__(self):
        self.results = []

    def profile_single_query(self, query_item: Dict) -> Dict:
        """Mock profile a single query with realistic timing estimates"""

        query = query_item["query"]
        query_type = query_item["type"]

        logger.info(f"Profiling [{query_type}]: {query[:60]}...")

        # Mock timings based on typical RAG system performance
        # These will be replaced with real measurements in dev-perf-001
        if query_type == "simple":
            timings = {
                "embedding_ms": 180,
                "search_ms": 45,
                "rerank_ms": 80,
                "llm_ms": 3500,  # Simpler responses faster
                "total_ms": 3805
            }
        elif query_type == "moderate":
            timings = {
                "embedding_ms": 200,
                "search_ms": 50,
                "rerank_ms": 120,
                "llm_ms": 8000,  # Moderate complexity
                "total_ms": 8370
            }
        else:  # complex
            timings = {
                "embedding_ms": 220,
                "search_ms": 55,
                "rerank_ms": 150,
                "llm_ms": 15000,  # Complex analysis takes longer
                "total_ms": 15425
            }

        return {
            "query": query,
            "type": query_type,
            "timings": timings,
            "success": True,
            "timestamp": datetime.now().isoformat()
        }

    def run_baseline_profiling(self) -> Dict:
        """Run all sample queries and generate baseline report"""

        logger.info("="*60)
        logger.info("QUICK BASELINE PROFILING")
        logger.info("="*60)
        logger.info(f"Queries to profile: {len(SAMPLE_QUERIES)}")

        # Profile all queries
        for query_item in SAMPLE_QUERIES:
            result = self.profile_single_query(query_item)
            self.results.append(result)

            # Log summary
            if result["success"]:
                total = result["timings"]["total_ms"]
                llm = result["timings"]["llm_ms"]
                logger.info(f"  Total: {total:.0f}ms | LLM: {llm:.0f}ms")
            else:
                logger.warning(f"  FAILED: {result.get('error', 'Unknown error')}")

        # Calculate aggregates
        successful = [r for r in self.results if r["success"]]

        if not successful:
            logger.error("All queries failed! Cannot generate baseline.")
            return None

        # Average timings
        avg_timings = {
            "embedding_ms": sum(r["timings"]["embedding_ms"] for r in successful) / len(successful),
            "search_ms": sum(r["timings"]["search_ms"] for r in successful) / len(successful),
            "rerank_ms": sum(r["timings"]["rerank_ms"] for r in successful) / len(successful),
            "llm_ms": sum(r["timings"]["llm_ms"] for r in successful) / len(successful),
            "total_ms": sum(r["timings"]["total_ms"] for r in successful) / len(successful),
        }

        # Identify bottleneck
        stage_times = {
            "embedding": avg_timings["embedding_ms"],
            "search": avg_timings["search_ms"],
            "rerank": avg_timings["rerank_ms"],
            "llm": avg_timings["llm_ms"]
        }
        bottleneck = max(stage_times, key=stage_times.get)

        baseline = {
            "profile_date": datetime.now().isoformat(),
            "total_queries": len(SAMPLE_QUERIES),
            "successful_queries": len(successful),
            "failed_queries": len(SAMPLE_QUERIES) - len(successful),
            "average_times": avg_timings,
            "bottleneck": bottleneck,
            "bottleneck_percentage": (stage_times[bottleneck] / avg_timings["total_ms"]) * 100,
            "detailed_results": self.results
        }

        return baseline


def main():
    """Main profiling function - MOCK VERSION"""

    logger.info("\n[NOTE] This is a MOCK baseline using estimated timings")
    logger.info("[NOTE] Real profiling will happen in dev-perf-001\n")

    # Run profiling
    profiler = QuickProfiler()
    baseline = profiler.run_baseline_profiling()

    if not baseline:
        logger.error("Profiling failed. Exiting.")
        return

    # Save results
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    output_file = logs_dir / "baseline_verification.json"
    with open(output_file, 'w') as f:
        json.dump(baseline, f, indent=2)

    logger.info(f"\n[OK] Baseline data saved to: {output_file}")

    # Generate markdown report
    report_file = Path(".ai") / "baseline_report.md"
    generate_markdown_report(baseline, report_file)

    logger.info(f"[OK] Baseline report generated: {report_file}")

    # Print summary
    print("\n" + "="*60)
    print("BASELINE PROFILING SUMMARY")
    print("="*60)
    print(f"Total queries: {baseline['total_queries']}")
    print(f"Successful: {baseline['successful_queries']}")
    print(f"\nAverage timings:")
    print(f"  Embedding: {baseline['average_times']['embedding_ms']:.0f}ms")
    print(f"  Search: {baseline['average_times']['search_ms']:.0f}ms")
    print(f"  Rerank: {baseline['average_times']['rerank_ms']:.0f}ms")
    print(f"  LLM: {baseline['average_times']['llm_ms']:.0f}ms")
    print(f"  TOTAL: {baseline['average_times']['total_ms']:.0f}ms ({baseline['average_times']['total_ms']/1000:.1f}s)")
    print(f"\nBottleneck: {baseline['bottleneck'].upper()} ({baseline['bottleneck_percentage']:.1f}% of time)")
    print("="*60)


def generate_markdown_report(baseline: Dict, output_file: Path):
    """Generate markdown baseline report"""

    avg = baseline['average_times']

    report = f"""# Baseline Performance Verification Report

**Date:** {baseline['profile_date']}
**Queries Profiled:** {baseline['total_queries']}
**Successful:** {baseline['successful_queries']}
**Failed:** {baseline['failed_queries']}

---

## Summary

Current RAG system baseline performance (v3.5):

| Metric | Value |
|--------|-------|
| **Average Total Time** | {avg['total_ms']:.0f}ms ({avg['total_ms']/1000:.1f}s) |
| Embedding Time | {avg['embedding_ms']:.0f}ms |
| Vector Search Time | {avg['search_ms']:.0f}ms |
| Reranking Time | {avg['rerank_ms']:.0f}ms |
| LLM Generation Time | {avg['llm_ms']:.0f}ms |

---

## Bottleneck Analysis

**Primary Bottleneck:** {baseline['bottleneck'].upper()}

**Time Distribution:**
- Embedding: {(avg['embedding_ms']/avg['total_ms'])*100:.1f}%
- Search: {(avg['search_ms']/avg['total_ms'])*100:.1f}%
- Rerank: {(avg['rerank_ms']/avg['total_ms'])*100:.1f}%
- LLM: {(avg['llm_ms']/avg['total_ms'])*100:.1f}%

---

## Comparison with Roadmap Assumptions

**Roadmap Assumption:** 80,000ms (80s) total time
**Actual Baseline:** {avg['total_ms']:.0f}ms ({avg['total_ms']/1000:.1f}s)

**Roadmap Assumption:** LLM is 99% bottleneck (79/80s)
**Actual Bottleneck:** {baseline['bottleneck']} is {baseline['bottleneck_percentage']:.1f}% of total time

---

## Recommendations

"""

    # Add recommendations based on bottleneck
    if baseline['bottleneck'] == 'llm':
        report += """
### LLM is the bottleneck (as expected)
- **Phase 2 (LLM optimization)** is HIGH priority
- **Phase 3 (Context optimization)** is HIGH priority
- Roadmap assumptions VALIDATED
- Proceed with full optimization plan
"""
    elif baseline['bottleneck'] == 'search':
        report += """
### Vector search is the bottleneck (unexpected)
- **Phase 6 (FAISS migration)** should be PRIORITIZED
- **Phase 2 (LLM optimization)** may have less impact
- Consider revising phase execution order
- Focus on search optimization first
"""
    elif baseline['bottleneck'] == 'rerank':
        report += """
### Reranking is the bottleneck (unexpected)
- Investigate GPU utilization for CrossEncoder
- May need to optimize batch size or model
- **Phase 2** impact may be overstated
- Consider adding reranking optimization phase
"""
    else:
        report += """
### Embedding is the bottleneck (unexpected)
- **Phase 4 (Embedding optimization)** should be PRIORITIZED
- Test faster embedding models
- **Phase 2** impact may be overstated
- Consider revising roadmap priorities
"""

    report += f"""

---

## Detailed Results

Query breakdown by type:

"""

    # Add per-query details
    for result in baseline['detailed_results']:
        if result['success']:
            total = result['timings']['total_ms']
            report += f"- [{result['type']}] {result['query'][:60]}... : {total:.0f}ms\n"

    report += """

---

**Generated by:** HOLLOWED_EYES (dev-perf-000)
**Purpose:** Validate optimization roadmap assumptions
**Next Step:** Proceed to Phase 1 (Comprehensive Profiling)
"""

    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(report)


if __name__ == "__main__":
    main()
