import React from 'react'
import { Zap, Cpu, Database, Lock, Gauge, Box } from 'lucide-react'

export function KeyFeatures() {
  return (
    <div className="mx-auto my-20 max-w-5xl px-4">
      <div className="mb-16 text-center">
        <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white md:text-4xl">
          Built for Production Scale
        </h2>
        <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Enterprise-grade capabilities that power mission-critical applications
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="group relative overflow-hidden rounded-2xl border border-blue-200/50 bg-white p-8 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-500/10 dark:border-blue-900/30 dark:bg-gray-900/50">
          <div className="absolute right-0 top-0 h-40 w-40 translate-x-10 -translate-y-10 rounded-full bg-blue-500/10 blur-3xl transition-all group-hover:bg-blue-500/20" />
          <div className="relative">
            <div className="mb-5 inline-flex rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 p-3 shadow-lg shadow-blue-500/25">
              <Zap className="h-6 w-6 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold text-gray-900 dark:text-white">
              GPU Acceleration
            </h3>
            <p className="leading-relaxed text-gray-600 dark:text-gray-400">
              CUDA-optimized embeddings and vector operations deliver 10x faster retrieval compared to CPU-only solutions
            </p>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-purple-200/50 bg-white p-8 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-purple-500/10 dark:border-purple-900/30 dark:bg-gray-900/50">
          <div className="absolute right-0 top-0 h-40 w-40 translate-x-10 -translate-y-10 rounded-full bg-purple-500/10 blur-3xl transition-all group-hover:bg-purple-500/20" />
          <div className="relative">
            <div className="mb-5 inline-flex rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 p-3 shadow-lg shadow-purple-500/25">
              <Cpu className="h-6 w-6 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold text-gray-900 dark:text-white">
              Adaptive Retrieval
            </h3>
            <p className="leading-relaxed text-gray-600 dark:text-gray-400">
              Multi-stage ranking with real-time query complexity analysis and dynamic top-k selection
            </p>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-cyan-200/50 bg-white p-8 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-cyan-500/10 dark:border-cyan-900/30 dark:bg-gray-900/50">
          <div className="absolute right-0 top-0 h-40 w-40 translate-x-10 -translate-y-10 rounded-full bg-cyan-500/10 blur-3xl transition-all group-hover:bg-cyan-500/20" />
          <div className="relative">
            <div className="mb-5 inline-flex rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 p-3 shadow-lg shadow-cyan-500/25">
              <Database className="h-6 w-6 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold text-gray-900 dark:text-white">
              Hybrid Search
            </h3>
            <p className="leading-relaxed text-gray-600 dark:text-gray-400">
              Combines semantic similarity with BM25 keyword matching for optimal recall and precision
            </p>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-red-200/50 bg-white p-8 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-red-500/10 dark:border-red-900/30 dark:bg-gray-900/50">
          <div className="absolute right-0 top-0 h-40 w-40 translate-x-10 -translate-y-10 rounded-full bg-red-500/10 blur-3xl transition-all group-hover:bg-red-500/20" />
          <div className="relative">
            <div className="mb-5 inline-flex rounded-xl bg-gradient-to-br from-red-500 to-red-600 p-3 shadow-lg shadow-red-500/25">
              <Lock className="h-6 w-6 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold text-gray-900 dark:text-white">
              Enterprise Security
            </h3>
            <p className="leading-relaxed text-gray-600 dark:text-gray-400">
              Role-based access control, comprehensive audit logging, and SOC 2 compliance ready
            </p>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-orange-200/50 bg-white p-8 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-orange-500/10 dark:border-orange-900/30 dark:bg-gray-900/50">
          <div className="absolute right-0 top-0 h-40 w-40 translate-x-10 -translate-y-10 rounded-full bg-orange-500/10 blur-3xl transition-all group-hover:bg-orange-500/20" />
          <div className="relative">
            <div className="mb-5 inline-flex rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 p-3 shadow-lg shadow-orange-500/25">
              <Gauge className="h-6 w-6 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold text-gray-900 dark:text-white">
              Real-time Monitoring
            </h3>
            <p className="leading-relaxed text-gray-600 dark:text-gray-400">
              Prometheus metrics, Grafana dashboards, and distributed tracing for full observability
            </p>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-green-200/50 bg-white p-8 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-green-500/10 dark:border-green-900/30 dark:bg-gray-900/50">
          <div className="absolute right-0 top-0 h-40 w-40 translate-x-10 -translate-y-10 rounded-full bg-green-500/10 blur-3xl transition-all group-hover:bg-green-500/20" />
          <div className="relative">
            <div className="mb-5 inline-flex rounded-xl bg-gradient-to-br from-green-500 to-green-600 p-3 shadow-lg shadow-green-500/25">
              <Box className="h-6 w-6 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold text-gray-900 dark:text-white">
              Production Deploy
            </h3>
            <p className="leading-relaxed text-gray-600 dark:text-gray-400">
              Docker containers, Kubernetes manifests, and auto-scaling configurations included
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
