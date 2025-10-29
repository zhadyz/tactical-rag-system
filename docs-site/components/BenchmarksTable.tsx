import React from 'react'
import { ArrowRight } from 'lucide-react'

export function BenchmarksTable() {
  return (
    <div className="mx-auto my-20 max-w-6xl px-4">
      <div className="mb-12 text-center">
        <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white md:text-4xl">
          Performance Comparison
        </h2>
        <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Apollo consistently outperforms popular RAG frameworks in real-world benchmarks
        </p>
      </div>

      <div className="overflow-hidden rounded-2xl border border-gray-200/50 bg-white shadow-sm dark:border-gray-800/50 dark:bg-gray-900/50">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50/50 dark:border-gray-800 dark:bg-gray-900">
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">System</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">Latency (P95)</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">Throughput</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">Accuracy</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">GPU Utilization</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              <tr className="bg-blue-50/30 dark:bg-blue-950/20">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-gray-900 dark:text-white">Apollo</span>
                    <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">Best</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-base font-bold text-gray-900 dark:text-white">127ms</td>
                <td className="px-6 py-4 text-base font-bold text-gray-900 dark:text-white">450 q/s</td>
                <td className="px-6 py-4 text-base font-bold text-gray-900 dark:text-white">94.2%</td>
                <td className="px-6 py-4 text-base font-bold text-gray-900 dark:text-white">88%</td>
              </tr>
              <tr className="hover:bg-gray-50/50 dark:hover:bg-gray-900/30">
                <td className="px-6 py-4 font-medium text-gray-900 dark:text-gray-300">LangChain</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">892ms</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">67 q/s</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">89.1%</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">23%</td>
              </tr>
              <tr className="hover:bg-gray-50/50 dark:hover:bg-gray-900/30">
                <td className="px-6 py-4 font-medium text-gray-900 dark:text-gray-300">LlamaIndex</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">654ms</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">102 q/s</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">91.3%</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">41%</td>
              </tr>
              <tr className="hover:bg-gray-50/50 dark:hover:bg-gray-900/30">
                <td className="px-6 py-4 font-medium text-gray-900 dark:text-gray-300">Haystack</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">543ms</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">134 q/s</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">90.7%</td>
                <td className="px-6 py-4 text-gray-600 dark:text-gray-400">35%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
        <p className="mb-3">Benchmark conditions: 100K document corpus, NVIDIA A100 40GB, concurrent queries, mixed complexity</p>
        <a href="/benchmarks/overview" className="inline-flex items-center gap-2 font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">
          <span>View detailed benchmark methodology and reproduce results</span>
          <ArrowRight className="h-4 w-4" />
        </a>
      </div>
    </div>
  )
}
