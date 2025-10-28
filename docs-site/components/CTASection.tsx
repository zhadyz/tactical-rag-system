import React from 'react'
import { ArrowRight, Github } from 'lucide-react'

export function CTASection() {
  return (
    <div className="relative my-24 overflow-hidden rounded-3xl border border-blue-200/50 bg-gradient-to-br from-blue-50 via-white to-purple-50 p-12 text-center shadow-xl dark:border-blue-900/30 dark:from-blue-950/30 dark:via-gray-900 dark:to-purple-950/30 md:p-16">
      <div className="absolute inset-0 bg-grid-pattern opacity-10" />
      <div className="absolute right-0 top-0 h-64 w-64 translate-x-32 -translate-y-32 rounded-full bg-blue-500/20 blur-3xl" />
      <div className="absolute bottom-0 left-0 h-64 w-64 -translate-x-32 translate-y-32 rounded-full bg-purple-500/20 blur-3xl" />

      <div className="relative z-10">
        <h2 className="mb-4 text-3xl font-bold text-gray-900 dark:text-white md:text-4xl">
          Ready to Accelerate Your Document Intelligence?
        </h2>
        <p className="mx-auto mb-8 max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Join teams using Apollo to process millions of documents with GPU-accelerated speed and precision
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <a
            href="/getting-started"
            className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 px-8 py-4 font-semibold text-white shadow-lg shadow-blue-500/25 transition-all hover:scale-105 hover:shadow-xl hover:shadow-blue-500/40"
          >
            Start Building
            <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
          </a>
          <a
            href="https://github.com/zhadyz/tactical-rag-system"
            target="_blank"
            rel="noopener noreferrer"
            className="group inline-flex items-center gap-2 rounded-xl border-2 border-gray-300 bg-white px-8 py-4 font-semibold text-gray-900 transition-all hover:border-gray-400 hover:shadow-lg dark:border-gray-700 dark:bg-gray-900 dark:text-white dark:hover:border-gray-600"
          >
            <Github className="h-5 w-5" />
            View on GitHub
          </a>
        </div>
      </div>
    </div>
  )
}
