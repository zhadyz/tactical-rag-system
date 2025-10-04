"""
Enterprise RAG System - Comprehensive Evaluation Suite
Measures retrieval quality, answer accuracy, and system performance
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import numpy as np

from config import load_config
from app import EnterpriseRAGSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEvaluator:
    """Comprehensive RAG system evaluation"""
    
    def __init__(self, rag_system: EnterpriseRAGSystem):
        self.rag_system = rag_system
        self.results = {}
    
    async def run_full_evaluation(self) -> Dict:
        """Run complete evaluation suite"""
        
        logger.info("=" * 70)
        logger.info("ENTERPRISE RAG SYSTEM - EVALUATION SUITE")
        logger.info("=" * 70)
        
        # Test 1: Retrieval Quality
        logger.info("\nðŸ“Š TEST 1: RETRIEVAL QUALITY")
        logger.info("-" * 70)
        retrieval_results = await self.evaluate_retrieval()
        
        # Test 2: Answer Quality
        logger.info("\nðŸ“ TEST 2: ANSWER QUALITY")
        logger.info("-" * 70)
        answer_results = await self.evaluate_answers()
        
        # Test 3: Performance
        logger.info("\nâš¡ TEST 3: PERFORMANCE METRICS")
        logger.info("-" * 70)
        performance_results = await self.evaluate_performance()
        
        # Test 4: Stress Test
        logger.info("\nðŸ”¥ TEST 4: STRESS TEST")
        logger.info("-" * 70)
        stress_results = await self.stress_test()
        
        # Compile results
        self.results = {
            "retrieval": retrieval_results,
            "answers": answer_results,
            "performance": performance_results,
            "stress_test": stress_results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate report
        self.generate_report()
        
        return self.results
    
    async def evaluate_retrieval(self) -> Dict:
        """Evaluate retrieval quality with test cases"""
        
        # Define test cases (customize for your documents)
        test_cases = [
            {
                "query": "What are the main topics?",
                "expected_docs": [],  # Add expected document names
                "difficulty": "easy"
            },
            {
                "query": "Compare the different approaches",
                "expected_docs": [],
                "difficulty": "medium"
            },
            {
                "query": "What are the implications of X on Y?",
                "expected_docs": [],
                "difficulty": "hard"
            }
        ]
        
        results = {
            "total_tests": len(test_cases),
            "precision_scores": [],
            "recall_scores": [],
            "mrr_scores": [],
            "by_difficulty": {}
        }
        
        for test in test_cases:
            query = test["query"]
            expected = set(test["expected_docs"])
            difficulty = test["difficulty"]
            
            # Perform retrieval
            result = await self.rag_system.query(query)
            
            if result.get("error"):
                logger.warning(f"Query failed: {query}")
                continue
            
            # Get retrieved documents
            retrieved = set([
                source["file_name"]
                for source in result.get("sources", [])
            ])
            
            # Calculate metrics (if expected docs provided)
            if expected:
                precision = self._calculate_precision(retrieved, expected)
                recall = self._calculate_recall(retrieved, expected)
                mrr = self._calculate_mrr(
                    [s["file_name"] for s in result.get("sources", [])],
                    expected
                )
                
                results["precision_scores"].append(precision)
                results["recall_scores"].append(recall)
                results["mrr_scores"].append(mrr)
                
                # Track by difficulty
                if difficulty not in results["by_difficulty"]:
                    results["by_difficulty"][difficulty] = {
                        "precision": [],
                        "recall": []
                    }
                
                results["by_difficulty"][difficulty]["precision"].append(precision)
                results["by_difficulty"][difficulty]["recall"].append(recall)
                
                logger.info(f"  Query: {query[:50]}...")
                logger.info(f"  Precision: {precision:.2%} | Recall: {recall:.2%} | MRR: {mrr:.3f}")
        
        # Calculate averages
        if results["precision_scores"]:
            results["avg_precision"] = np.mean(results["precision_scores"])
            results["avg_recall"] = np.mean(results["recall_scores"])
            results["avg_mrr"] = np.mean(results["mrr_scores"])
            results["f1_score"] = (
                2 * results["avg_precision"] * results["avg_recall"] /
                (results["avg_precision"] + results["avg_recall"])
                if (results["avg_precision"] + results["avg_recall"]) > 0 else 0
            )
        
        return results
    
    async def evaluate_answers(self) -> Dict:
        """Evaluate answer quality"""
        
        test_questions = [
            "What is the main purpose of this system?",
            "How does the retrieval process work?",
            "What are the key benefits?",
        ]
        
        results = {
            "total_questions": len(test_questions),
            "answers": [],
            "avg_length": 0,
            "avg_sources_cited": 0
        }
        
        lengths = []
        source_counts = []
        
        for question in test_questions:
            result = await self.rag_system.query(question)
            
            if not result.get("error"):
                answer = result["answer"]
                sources = result.get("sources", [])
                
                lengths.append(len(answer))
                source_counts.append(len(sources))
                
                results["answers"].append({
                    "question": question,
                    "answer_length": len(answer),
                    "num_sources": len(sources),
                    "intent": result.get("metadata", {}).get("intent")
                })
                
                logger.info(f"  Question: {question[:50]}...")
                logger.info(f"  Answer length: {len(answer)} chars")
                logger.info(f"  Sources cited: {len(sources)}")
        
        if lengths:
            results["avg_length"] = np.mean(lengths)
            results["avg_sources_cited"] = np.mean(source_counts)
        
        return results
    
    async def evaluate_performance(self) -> Dict:
        """Evaluate system performance"""
        
        test_queries = [
            "What are the main topics?",
            "Summarize the key points",
            "What is the methodology?",
        ]
        
        latencies = []
        cache_hits = 0
        
        for query in test_queries:
            # First query (cold)
            start = asyncio.get_event_loop().time()
            await self.rag_system.query(query)
            cold_latency = asyncio.get_event_loop().time() - start
            
            # Second query (warm - should hit cache)
            start = asyncio.get_event_loop().time()
            await self.rag_system.query(query)
            warm_latency = asyncio.get_event_loop().time() - start
            
            latencies.append(cold_latency)
            
            if warm_latency < cold_latency * 0.5:  # 50% faster = cache hit
                cache_hits += 1
            
            logger.info(f"  Query: {query[:40]}...")
            logger.info(f"  Cold: {cold_latency:.3f}s | Warm: {warm_latency:.3f}s")
        
        # Get system stats
        status = self.rag_system.get_system_status()
        
        results = {
            "avg_latency": np.mean(latencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "p95_latency": np.percentile(latencies, 95),
            "cache_effectiveness": cache_hits / len(test_queries),
            "system_stats": status
        }
        
        logger.info(f"\n  Average latency: {results['avg_latency']:.3f}s")
        logger.info(f"  P95 latency: {results['p95_latency']:.3f}s")
        logger.info(f"  Cache effectiveness: {results['cache_effectiveness']:.1%}")
        
        return results
    
    async def stress_test(self, num_concurrent: int = 10) -> Dict:
        """Stress test with concurrent queries"""
        
        queries = [
            "What are the main topics?",
            "Summarize the document",
            "What is the methodology?",
            "List key findings",
            "What are the conclusions?",
        ] * (num_concurrent // 5 + 1)
        
        queries = queries[:num_concurrent]
        
        logger.info(f"  Running {num_concurrent} concurrent queries...")
        
        start = asyncio.get_event_loop().time()
        
        # Run all queries concurrently
        tasks = [self.rag_system.query(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = asyncio.get_event_loop().time() - start
        
        # Analyze results
        successes = sum(1 for r in results if not isinstance(r, Exception) and not r.get("error"))
        errors = len(results) - successes
        
        throughput = len(queries) / elapsed
        
        results_dict = {
            "total_queries": len(queries),
            "concurrent_level": num_concurrent,
            "successes": successes,
            "errors": errors,
            "total_time": elapsed,
            "throughput_qps": throughput,
            "avg_time_per_query": elapsed / len(queries)
        }
        
        logger.info(f"\n  Total time: {elapsed:.2f}s")
        logger.info(f"  Throughput: {throughput:.1f} queries/sec")
        logger.info(f"  Success rate: {successes/len(queries):.1%}")
        
        return results_dict
    
    def generate_report(self) -> None:
        """Generate evaluation report"""
        
        logger.info("\n" + "=" * 70)
        logger.info("EVALUATION REPORT")
        logger.info("=" * 70)
        
        # Retrieval Quality
        if self.results["retrieval"].get("avg_precision"):
            logger.info("\nðŸ“Š RETRIEVAL QUALITY:")
            logger.info(f"  Precision: {self.results['retrieval']['avg_precision']:.1%}")
            logger.info(f"  Recall: {self.results['retrieval']['avg_recall']:.1%}")
            logger.info(f"  F1 Score: {self.results['retrieval']['f1_score']:.1%}")
            logger.info(f"  MRR: {self.results['retrieval']['avg_mrr']:.3f}")
        
        # Answer Quality
        if self.results["answers"]:
            logger.info("\nðŸ“ ANSWER QUALITY:")
            logger.info(f"  Avg answer length: {self.results['answers']['avg_length']:.0f} chars")
            logger.info(f"  Avg sources cited: {self.results['answers']['avg_sources_cited']:.1f}")
        
        # Performance
        logger.info("\nâš¡ PERFORMANCE:")
        logger.info(f"  Avg latency: {self.results['performance']['avg_latency']:.3f}s")
        logger.info(f"  P95 latency: {self.results['performance']['p95_latency']:.3f}s")
        logger.info(f"  Cache hit rate: {self.results['performance']['cache_effectiveness']:.1%}")
        
        # Stress Test
        logger.info("\nðŸ”¥ STRESS TEST:")
        logger.info(f"  Throughput: {self.results['stress_test']['throughput_qps']:.1f} QPS")
        logger.info(f"  Success rate: {self.results['stress_test']['successes']/self.results['stress_test']['total_queries']:.1%}")
        
        # Overall Grade
        logger.info("\n" + "=" * 70)
        logger.info("OVERALL ASSESSMENT:")
        logger.info("=" * 70)
        
        # Calculate grade
        grade = self._calculate_grade()
        logger.info(f"\n  Grade: {grade['letter']} ({grade['score']:.1f}/100)")
        logger.info(f"  Status: {grade['status']}")
        
        if grade['recommendations']:
            logger.info("\n  Recommendations:")
            for rec in grade['recommendations']:
                logger.info(f"    - {rec}")
        
        logger.info("\n" + "=" * 70)
        
        # Save to file
        output_file = Path("evaluation_results.json")
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\nâœ“ Full results saved to {output_file}")
    
    def _calculate_grade(self) -> Dict:
        """Calculate overall system grade"""
        
        scores = []
        recommendations = []
        
        # Retrieval quality (40%)
        if self.results["retrieval"].get("f1_score"):
            f1 = self.results["retrieval"]["f1_score"]
            retrieval_score = f1 * 40
            scores.append(retrieval_score)
            
            if f1 < 0.7:
                recommendations.append("Improve retrieval quality (F1 < 70%)")
        
        # Performance (30%)
        latency = self.results["performance"]["avg_latency"]
        if latency < 1.0:
            perf_score = 30
        elif latency < 2.0:
            perf_score = 25
        elif latency < 3.0:
            perf_score = 20
        else:
            perf_score = 15
        scores.append(perf_score)
        
        if latency > 2.0:
            recommendations.append("Optimize performance (avg latency > 2s)")
        
        # Stress test (20%)
        success_rate = (
            self.results['stress_test']['successes'] /
            self.results['stress_test']['total_queries']
        )
        stress_score = success_rate * 20
        scores.append(stress_score)
        
        if success_rate < 0.95:
            recommendations.append("Improve reliability under load")
        
        # Answer quality (10%)
        if self.results["answers"]["avg_sources_cited"] >= 3:
            answer_score = 10
        elif self.results["answers"]["avg_sources_cited"] >= 2:
            answer_score = 7
        else:
            answer_score = 5
        scores.append(answer_score)
        
        # Calculate total
        total_score = sum(scores)
        
        if total_score >= 90:
            letter = "A"
            status = "Excellent - Production Ready"
        elif total_score >= 80:
            letter = "B"
            status = "Good - Minor improvements needed"
        elif total_score >= 70:
            letter = "C"
            status = "Acceptable - Needs optimization"
        elif total_score >= 60:
            letter = "D"
            status = "Poor - Significant improvements needed"
        else:
            letter = "F"
            status = "Failing - Major overhaul required"
        
        return {
            "score": total_score,
            "letter": letter,
            "status": status,
            "recommendations": recommendations
        }
    
    def _calculate_precision(self, retrieved: set, expected: set) -> float:
        """Calculate precision"""
        if not retrieved:
            return 0.0
        return len(retrieved & expected) / len(retrieved)
    
    def _calculate_recall(self, retrieved: set, expected: set) -> float:
        """Calculate recall"""
        if not expected:
            return 0.0
        return len(retrieved & expected) / len(expected)
    
    def _calculate_mrr(self, retrieved_list: List[str], expected: set) -> float:
        """Calculate Mean Reciprocal Rank"""
        for rank, doc in enumerate(retrieved_list, 1):
            if doc in expected:
                return 1.0 / rank
        return 0.0


async def main():
    """Run evaluation"""
    
    # Load config and initialize system
    from config import load_config
    
    config = load_config()
    rag_system = EnterpriseRAGSystem(config)
    
    logger.info("Initializing system for evaluation...")
    success, message = await rag_system.initialize()
    
    if not success:
        logger.error(f"Failed to initialize: {message}")
        return
    
    # Run evaluation
    evaluator = RAGEvaluator(rag_system)
    await evaluator.run_full_evaluation()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\n\nEvaluation cancelled")
    except Exception as e:
        logger.error(f"\n\nEvaluation failed: {e}", exc_info=True)