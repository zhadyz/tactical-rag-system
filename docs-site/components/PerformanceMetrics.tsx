import React from 'react'
import { Gauge, Zap, Database } from 'lucide-react'

export function PerformanceMetrics() {
  return (
    <div className="mx-auto my-20 max-w-5xl px-4">
      <div className="mb-12 text-center">
        <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white md:text-4xl">
          Production-Grade Performance
        </h2>
        <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Real-world metrics from deployments processing millions of queries daily
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="group relative overflow-hidden rounded-2xl border border-gray-200/50 bg-gradient-to-br from-blue-50 via-white to-blue-50/30 p-8 shadow-sm transition-all hover:shadow-xl hover:shadow-blue-500/10 dark:border-gray-800/50 dark:from-blue-950/30 dark:via-gray-900 dark:to-blue-950/20">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
          <div className="relative">
            <div className="mb-4 inline-flex rounded-lg bg-blue-100 p-3 dark:bg-blue-900/30">
              <Gauge className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="mb-2 text-sm font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Query Latency
            </div>
            <div className="mb-1 flex items-baseline gap-2">
              <span className="text-5xl font-bold text-gray-900 dark:text-white">127</span>
              <span className="text-2xl font-semibold text-gray-500 dark:text-gray-400">ms</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">P95 with GPU acceleration</p>
            <div className="mt-4 flex items-center gap-2 text-sm font-medium text-green-600 dark:text-green-400">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              85% faster vs CPU
            </div>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-gray-200/50 bg-gradient-to-br from-purple-50 via-white to-purple-50/30 p-8 shadow-sm transition-all hover:shadow-xl hover:shadow-purple-500/10 dark:border-gray-800/50 dark:from-purple-950/30 dark:via-gray-900 dark:to-purple-950/20">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
          <div className="relative">
            <div className="mb-4 inline-flex rounded-lg bg-purple-100 p-3 dark:bg-purple-900/30">
              <Zap className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="mb-2 text-sm font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Throughput
            </div>
            <div className="mb-1 flex items-baseline gap-2">
              <span className="text-5xl font-bold text-gray-900 dark:text-white">450</span>
              <span className="text-2xl font-semibold text-gray-500 dark:text-gray-400">q/s</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Concurrent queries per second</p>
            <div className="mt-4 flex items-center gap-2 text-sm font-medium text-green-600 dark:text-green-400">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              320% increase
            </div>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-gray-200/50 bg-gradient-to-br from-green-50 via-white to-green-50/30 p-8 shadow-sm transition-all hover:shadow-xl hover:shadow-green-500/10 dark:border-gray-800/50 dark:from-green-950/30 dark:via-gray-900 dark:to-green-950/20">
          <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
          <div className="relative">
            <div className="mb-4 inline-flex rounded-lg bg-green-100 p-3 dark:bg-green-900/30">
              <Database className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <div className="mb-2 text-sm font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Accuracy
            </div>
            <div className="mb-1 flex items-baseline gap-2">
              <span className="text-5xl font-bold text-gray-900 dark:text-white">94.2</span>
              <span className="text-2xl font-semibold text-gray-500 dark:text-gray-400">%</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Context relevance score</p>
            <div className="mt-4 flex items-center gap-2 text-sm font-medium text-green-600 dark:text-green-400">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Industry leading
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
