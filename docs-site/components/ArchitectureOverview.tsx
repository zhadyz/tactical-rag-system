import React from 'react'
import { Database, Zap, Box, ArrowRight } from 'lucide-react'

export function ArchitectureOverview() {
  return (
    <div className="mx-auto my-20 max-w-5xl px-4">
      <div className="mb-12 text-center">
        <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white md:text-4xl">
          Engineered for Performance
        </h2>
        <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Enterprise-grade architecture with careful optimization at every layer
        </p>
      </div>

      <div className="space-y-4">
        <div className="rounded-xl border border-blue-200/50 bg-gradient-to-r from-blue-50 to-blue-100/50 p-6 dark:border-blue-900/30 dark:from-blue-950/30 dark:to-blue-900/20">
          <div className="mb-2 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500 text-sm font-bold text-white">1</div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">Client Layer</h3>
          </div>
          <p className="ml-11 text-sm text-gray-700 dark:text-gray-300">
            Desktop App (Tauri) • Web UI (React) • REST API • WebSocket
          </p>
        </div>

        <div className="ml-8 h-8 w-0.5 bg-gradient-to-b from-blue-500/50 to-purple-500/50" />

        <div className="rounded-xl border border-purple-200/50 bg-gradient-to-r from-purple-50 to-purple-100/50 p-6 dark:border-purple-900/30 dark:from-purple-950/30 dark:to-purple-900/20">
          <div className="mb-2 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500 text-sm font-bold text-white">2</div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">API Gateway (FastAPI)</h3>
          </div>
          <p className="ml-11 text-sm text-gray-700 dark:text-gray-300">
            Authentication • Rate Limiting • Request Validation
          </p>
        </div>

        <div className="ml-8 h-8 w-0.5 bg-gradient-to-b from-purple-500/50 to-cyan-500/50" />

        <div className="rounded-xl border border-cyan-200/50 bg-gradient-to-r from-cyan-50 to-cyan-100/50 p-6 dark:border-cyan-900/30 dark:from-cyan-950/30 dark:to-cyan-900/20">
          <div className="mb-2 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500 text-sm font-bold text-white">3</div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">RAG Engine Core</h3>
          </div>
          <p className="ml-11 text-sm text-gray-700 dark:text-gray-300">
            Query Analysis • Adaptive Retrieval • Response Generation
          </p>
        </div>

        <div className="ml-8 h-8 w-0.5 bg-gradient-to-b from-cyan-500/50 to-green-500/50" />

        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-green-200/50 bg-gradient-to-br from-green-50 to-green-100/50 p-6 dark:border-green-900/30 dark:from-green-950/30 dark:to-green-900/20">
            <div className="mb-2 flex items-center gap-2">
              <Database className="h-5 w-5 text-green-600 dark:text-green-400" />
              <h4 className="font-bold text-gray-900 dark:text-white">Vector Store</h4>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300">FAISS/Milvus</p>
          </div>

          <div className="rounded-xl border border-orange-200/50 bg-gradient-to-br from-orange-50 to-orange-100/50 p-6 dark:border-orange-900/30 dark:from-orange-950/30 dark:to-orange-900/20">
            <div className="mb-2 flex items-center gap-2">
              <Zap className="h-5 w-5 text-orange-600 dark:text-orange-400" />
              <h4 className="font-bold text-gray-900 dark:text-white">GPU Acceleration</h4>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300">CUDA/cuBLAS</p>
          </div>

          <div className="rounded-xl border border-blue-200/50 bg-gradient-to-br from-blue-50 to-blue-100/50 p-6 dark:border-blue-900/30 dark:from-blue-950/30 dark:to-blue-900/20">
            <div className="mb-2 flex items-center gap-2">
              <Box className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <h4 className="font-bold text-gray-900 dark:text-white">Document Pipeline</h4>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300">PDF/DOCX/TXT</p>
          </div>
        </div>
      </div>

      <div className="mt-8 text-center">
        <a href="/architecture" className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">
          <span className="font-medium">Learn more in the Architecture documentation</span>
          <ArrowRight className="h-4 w-4" />
        </a>
      </div>
    </div>
  )
}
