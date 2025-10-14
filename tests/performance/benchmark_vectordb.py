"""
Performance Benchmark: ChromaDB vs Qdrant
Compares vector database performance at different scales
TARGET: Qdrant should be 10x+ faster at 100k+ vectors
"""

import asyncio
import time
import json
import numpy as np
from pathlib import Path
import sys
from typing import List, Dict
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_src"))

from qdrant_store import QdrantVectorStore
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings


class VectorDBBenchmark:
    """Benchmark suite for vector databases"""

    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_type": "vectordb_comparison",
            "scales": [],
            "summary": {}
        }

        # Test scales
        self.test_scales = [1000, 10000, 50000, 100000]  # 500k requires migration

        # Initialize embeddings
        print("Initializing embedding model...")
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

        # Test embedding
        test_emb = self.embeddings.embed_query("test")
        self.embedding_dim = len(test_emb)
        print(f"Embedding dimension: {self.embedding_dim}")

    def generate_test_data(self, count: int) -> List[Dict]:
        """Generate synthetic test documents"""
        print(f"Generating {count} test documents...")

        docs = []
        for i in range(count):
            # Generate varied text
            text = f"Document {i}: " + " ".join([
                f"word{j}" for j in range(20 + (i % 30))
            ])

            # Generate embedding (random for speed)
            embedding = np.random.randn(self.embedding_dim).astype(np.float32)

            docs.append({
                "text": text,
                "embedding": embedding,
                "metadata": {
                    "doc_id": f"doc_{i}",
                    "index": i,
                    "category": f"cat_{i % 10}"
                }
            })

            if (i + 1) % 10000 == 0:
                print(f"  Generated {i+1}/{count}")

        return docs

    async def benchmark_qdrant_indexing(self, docs: List[Dict], scale: int) -> Dict:
        """Benchmark Qdrant indexing performance"""
        print(f"\n[Qdrant] Indexing {scale} documents...")

        try:
            # Initialize Qdrant
            store = QdrantVectorStore(
                host="localhost",
                port=6333,
                collection_name=f"benchmark_{scale}",
                vector_size=self.embedding_dim
            )

            # Create collection
            store.create_collection(recreate=True)

            # Benchmark indexing
            start = time.time()
            await store.index_documents(docs, batch_size=100, show_progress=True)
            indexing_time = time.time() - start

            # Get collection info
            info = store.get_collection_info()

            print(f"  Indexing time: {indexing_time:.2f}s")
            print(f"  Throughput: {scale / indexing_time:.0f} docs/sec")

            # Cleanup
            store.client.delete_collection(f"benchmark_{scale}")

            return {
                "indexing_time": indexing_time,
                "throughput": scale / indexing_time,
                "success": True
            }

        except Exception as e:
            print(f"  Error: {e}")
            return {
                "indexing_time": None,
                "throughput": None,
                "success": False,
                "error": str(e)
            }

    async def benchmark_qdrant_search(self, docs: List[Dict], scale: int, num_queries: int = 100) -> Dict:
        """Benchmark Qdrant search performance"""
        print(f"\n[Qdrant] Searching {num_queries} queries at {scale} scale...")

        try:
            # Initialize and index
            store = QdrantVectorStore(
                host="localhost",
                port=6333,
                collection_name=f"benchmark_search_{scale}",
                vector_size=self.embedding_dim
            )

            store.create_collection(recreate=True)
            await store.index_documents(docs, batch_size=100, show_progress=False)

            # Generate query vectors
            query_vectors = [
                np.random.randn(self.embedding_dim).astype(np.float32)
                for _ in range(num_queries)
            ]

            # Benchmark search
            latencies = []
            for i, query_vec in enumerate(query_vectors):
                start = time.time()
                results = await store.search(query_vec.tolist(), top_k=10)
                latency = (time.time() - start) * 1000  # ms
                latencies.append(latency)

                if (i + 1) % 20 == 0:
                    print(f"  {i+1}/{num_queries} queries")

            # Calculate statistics
            p50 = statistics.median(latencies)
            p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            p99 = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
            avg = statistics.mean(latencies)

            print(f"  P50 latency: {p50:.2f}ms")
            print(f"  P95 latency: {p95:.2f}ms")
            print(f"  P99 latency: {p99:.2f}ms")
            print(f"  Avg latency: {avg:.2f}ms")

            # Cleanup
            store.client.delete_collection(f"benchmark_search_{scale}")

            return {
                "p50_latency_ms": p50,
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "avg_latency_ms": avg,
                "queries_per_sec": 1000 / avg,
                "success": True
            }

        except Exception as e:
            print(f"  Error: {e}")
            return {
                "p50_latency_ms": None,
                "p95_latency_ms": None,
                "p99_latency_ms": None,
                "avg_latency_ms": None,
                "queries_per_sec": None,
                "success": False,
                "error": str(e)
            }

    async def benchmark_chromadb_search(self, docs: List[Dict], scale: int, num_queries: int = 100) -> Dict:
        """Benchmark ChromaDB search performance"""
        print(f"\n[ChromaDB] Searching {num_queries} queries at {scale} scale...")

        try:
            # Create temporary ChromaDB
            from langchain.docstore.document import Document
            import tempfile

            temp_dir = tempfile.mkdtemp()

            # Convert docs to LangChain format
            langchain_docs = [
                Document(page_content=doc["text"], metadata=doc["metadata"])
                for doc in docs
            ]

            # Initialize ChromaDB with embeddings
            print("  Creating ChromaDB collection...")
            chroma = Chroma.from_documents(
                documents=langchain_docs,
                embedding=self.embeddings,
                persist_directory=temp_dir
            )

            # Generate queries (use some document texts)
            queries = [docs[i % len(docs)]["text"] for i in range(num_queries)]

            # Benchmark search
            latencies = []
            for i, query in enumerate(queries):
                start = time.time()
                results = chroma.similarity_search(query, k=10)
                latency = (time.time() - start) * 1000  # ms
                latencies.append(latency)

                if (i + 1) % 20 == 0:
                    print(f"  {i+1}/{num_queries} queries")

            # Calculate statistics
            p50 = statistics.median(latencies)
            p95 = statistics.quantiles(latencies, n=20)[18]
            p99 = statistics.quantiles(latencies, n=100)[98]
            avg = statistics.mean(latencies)

            print(f"  P50 latency: {p50:.2f}ms")
            print(f"  P95 latency: {p95:.2f}ms")
            print(f"  P99 latency: {p99:.2f}ms")
            print(f"  Avg latency: {avg:.2f}ms")

            # Cleanup
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            return {
                "p50_latency_ms": p50,
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "avg_latency_ms": avg,
                "queries_per_sec": 1000 / avg,
                "success": True
            }

        except Exception as e:
            print(f"  Error: {e}")
            return {
                "p50_latency_ms": None,
                "p95_latency_ms": None,
                "p99_latency_ms": None,
                "avg_latency_ms": None,
                "queries_per_sec": None,
                "success": False,
                "error": str(e)
            }

    async def run_benchmark(self):
        """Run complete benchmark suite"""
        print("="*80)
        print("VECTOR DATABASE BENCHMARK: ChromaDB vs Qdrant")
        print("="*80)

        for scale in self.test_scales:
            print(f"\n{'='*80}")
            print(f"SCALE: {scale:,} documents")
            print(f"{'='*80}")

            # Generate test data
            docs = self.generate_test_data(scale)

            # Benchmark Qdrant
            qdrant_index = await self.benchmark_qdrant_indexing(docs, scale)
            qdrant_search = await self.benchmark_qdrant_search(docs, scale)

            # Benchmark ChromaDB (skip large scales to save time)
            if scale <= 10000:
                chroma_search = await self.benchmark_chromadb_search(docs, scale)
            else:
                print(f"\n[ChromaDB] Skipping at {scale} scale (too slow)")
                chroma_search = {
                    "p50_latency_ms": None,
                    "p95_latency_ms": None,
                    "p99_latency_ms": None,
                    "avg_latency_ms": None,
                    "queries_per_sec": None,
                    "success": False,
                    "error": "Skipped (scale too large)"
                }

            # Calculate speedup
            speedup = None
            if chroma_search["success"] and qdrant_search["success"]:
                if qdrant_search["avg_latency_ms"] and chroma_search["avg_latency_ms"]:
                    speedup = chroma_search["avg_latency_ms"] / qdrant_search["avg_latency_ms"]

            # Store results
            scale_result = {
                "scale": scale,
                "qdrant": {
                    "indexing": qdrant_index,
                    "search": qdrant_search
                },
                "chromadb": {
                    "search": chroma_search
                },
                "speedup": speedup
            }

            self.results["scales"].append(scale_result)

            # Print comparison
            print(f"\n{'='*80}")
            print(f"COMPARISON AT {scale:,} DOCUMENTS:")
            if speedup:
                print(f"  Qdrant is {speedup:.1f}x faster than ChromaDB")
            print(f"  Qdrant P95: {qdrant_search.get('p95_latency_ms', 'N/A'):.2f}ms")
            print(f"  ChromaDB P95: {chroma_search.get('p95_latency_ms', 'N/A') if chroma_search.get('p95_latency_ms') else 'N/A'}ms")
            print(f"{'='*80}")

    def save_results(self):
        """Save benchmark results to file"""
        output_dir = Path("logs/benchmarks")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"vectordb_benchmark_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: {output_file}")
        return output_file

    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)

        for scale_result in self.results["scales"]:
            scale = scale_result["scale"]
            qdrant = scale_result["qdrant"]["search"]
            chroma = scale_result["chromadb"]["search"]
            speedup = scale_result["speedup"]

            print(f"\n{scale:,} documents:")
            print(f"  Qdrant:  {qdrant.get('p95_latency_ms', 'N/A'):.2f}ms P95")
            print(f"  ChromaDB: {chroma.get('p95_latency_ms', 'N/A') if chroma.get('p95_latency_ms') else 'N/A'}ms P95")
            if speedup:
                print(f"  Speedup: {speedup:.1f}x")

        print("\n" + "="*80)


async def main():
    """Main benchmark execution"""
    benchmark = VectorDBBenchmark()

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
