import React from 'react'
import { Zap, Cpu, Gauge, Lock, ArrowRight } from 'lucide-react'

export function WhyApollo() {
  return (
    <div className="mx-auto my-20 max-w-7xl px-4">
      <div className="mb-16 text-center">
        <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white md:text-4xl">
          Why Apollo
        </h2>
        <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Four core principles that set us apart from traditional RAG frameworks
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:gap-8">
        <div className="group relative overflow-hidden rounded-2xl border border-gray-200/50 bg-gradient-to-br from-white via-gray-50/50 to-white p-10 shadow-sm transition-all hover:shadow-xl dark:border-gray-800/50 dark:from-gray-900 dark:via-gray-900/80 dark:to-gray-900">
          <div className="absolute right-0 top-0 h-32 w-32 translate-x-8 -translate-y-8 rounded-full bg-blue-500/10 blur-2xl" />
          <div className="relative">
            <div className="mb-6 inline-flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
                <Zap className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                True GPU Acceleration
              </h3>
            </div>
            <p className="mb-4 leading-relaxed text-gray-700 dark:text-gray-300">
              Unlike frameworks that claim GPU support but run most operations on CPU, Apollo leverages CUDA for
              <span className="font-semibold text-gray-900 dark:text-white"> every</span> compute-intensive operation:
              embeddings, similarity search, re-ranking, and token generation.
            </p>
            <a href="/core-concepts/gpu-acceleration" className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">
              <span>Learn about our GPU architecture</span>
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-gray-200/50 bg-gradient-to-br from-white via-gray-50/50 to-white p-10 shadow-sm transition-all hover:shadow-xl dark:border-gray-800/50 dark:from-gray-900 dark:via-gray-900/80 dark:to-gray-900">
          <div className="absolute right-0 top-0 h-32 w-32 translate-x-8 -translate-y-8 rounded-full bg-purple-500/10 blur-2xl" />
          <div className="relative">
            <div className="mb-6 inline-flex items-center gap-3">
              <div className="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
                <Cpu className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                Adaptive Retrieval Intelligence
              </h3>
            </div>
            <p className="mb-4 leading-relaxed text-gray-700 dark:text-gray-300">
              Apollo analyzes query complexity in real-time and automatically adjusts retrieval strategies,
              chunk sizes, and re-ranking depth to optimize both latency and accuracy. No manual tuning required.
            </p>
            <a href="/core-concepts/adaptive-retrieval" className="inline-flex items-center gap-2 text-sm font-medium text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300">
              <span>Explore adaptive strategies</span>
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-gray-200/50 bg-gradient-to-br from-white via-gray-50/50 to-white p-10 shadow-sm transition-all hover:shadow-xl dark:border-gray-800/50 dark:from-gray-900 dark:via-gray-900/80 dark:to-gray-900">
          <div className="absolute right-0 top-0 h-32 w-32 translate-x-8 -translate-y-8 rounded-full bg-orange-500/10 blur-2xl" />
          <div className="relative">
            <div className="mb-6 inline-flex items-center gap-3">
              <div className="rounded-lg bg-orange-100 p-2 dark:bg-orange-900/30">
                <Gauge className="h-5 w-5 text-orange-600 dark:text-orange-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                Production Observability
              </h3>
            </div>
            <p className="mb-4 leading-relaxed text-gray-700 dark:text-gray-300">
              Built-in metrics, tracing, and profiling at every layer. Know exactly what's happening in your RAG
              pipeline with OpenTelemetry integration and custom performance dashboards.
            </p>
            <a href="/advanced/monitoring" className="inline-flex items-center gap-2 text-sm font-medium text-orange-600 hover:text-orange-700 dark:text-orange-400 dark:hover:text-orange-300">
              <span>View monitoring features</span>
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-gray-200/50 bg-gradient-to-br from-white via-gray-50/50 to-white p-10 shadow-sm transition-all hover:shadow-xl dark:border-gray-800/50 dark:from-gray-900 dark:via-gray-900/80 dark:to-gray-900">
          <div className="absolute right-0 top-0 h-32 w-32 translate-x-8 -translate-y-8 rounded-full bg-red-500/10 blur-2xl" />
          <div className="relative">
            <div className="mb-6 inline-flex items-center gap-3">
              <div className="rounded-lg bg-red-100 p-2 dark:bg-red-900/30">
                <Lock className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                Enterprise Ready
              </h3>
            </div>
            <p className="mb-4 leading-relaxed text-gray-700 dark:text-gray-300">
              Multi-tenant architecture, role-based access control, comprehensive audit logging, and compliance features
              designed for regulated industries and enterprise deployments.
            </p>
            <a href="/advanced/security" className="inline-flex items-center gap-2 text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
              <span>See security features</span>
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
