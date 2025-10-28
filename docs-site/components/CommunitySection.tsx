import React from 'react'
import { BookOpen, Github, Building2, Scale, MessageCircle, Star } from 'lucide-react'

export function CommunitySection() {
  return (
    <div className="mx-auto my-20 max-w-7xl px-4">
      {/* Community & Support */}
      <div className="mb-16">
        <div className="mb-12 text-center">
          <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white md:text-4xl">
            Community & Support
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
            Join thousands of developers building intelligent document systems with Apollo
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {/* Documentation Card */}
          <a
            href="/getting-started/quick-start"
            className="group relative overflow-hidden rounded-2xl border border-gray-200/50 bg-gradient-to-br from-blue-50 via-white to-blue-50/30 p-8 shadow-sm transition-all hover:scale-105 hover:shadow-xl dark:border-gray-800/50 dark:from-blue-950/30 dark:via-gray-900 dark:to-blue-950/20"
          >
            <div className="absolute right-0 top-0 h-24 w-24 translate-x-6 -translate-y-6 rounded-full bg-blue-500/20 blur-2xl" />
            <div className="relative">
              <div className="mb-4 inline-flex items-center justify-center rounded-xl bg-blue-100 p-3 dark:bg-blue-900/50">
                <BookOpen className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="mb-2 text-xl font-bold text-gray-900 dark:text-white">
                Documentation
              </h3>
              <p className="mb-4 text-gray-600 dark:text-gray-400">
                Comprehensive guides, API references, and tutorials for every use case
              </p>
              <div className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400">
                <span>Explore docs</span>
                <span className="transition-transform group-hover:translate-x-1">→</span>
              </div>
            </div>
          </a>

          {/* GitHub Card */}
          <a
            href="https://github.com/zhadyz/tactical-rag-system"
            target="_blank"
            rel="noopener noreferrer"
            className="group relative overflow-hidden rounded-2xl border border-gray-200/50 bg-gradient-to-br from-gray-50 via-white to-gray-50/30 p-8 shadow-sm transition-all hover:scale-105 hover:shadow-xl dark:border-gray-800/50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-950"
          >
            <div className="absolute right-0 top-0 h-24 w-24 translate-x-6 -translate-y-6 rounded-full bg-gray-500/20 blur-2xl" />
            <div className="relative">
              <div className="mb-4 inline-flex items-center justify-center rounded-xl bg-gray-100 p-3 dark:bg-gray-800">
                <Github className="h-6 w-6 text-gray-700 dark:text-gray-300" />
              </div>
              <h3 className="mb-2 text-xl font-bold text-gray-900 dark:text-white">
                Open Source
              </h3>
              <p className="mb-4 text-gray-600 dark:text-gray-400">
                Star the repo, report issues, and contribute to the future of RAG systems
              </p>
              <div className="inline-flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                <Star className="h-4 w-4" />
                <span>Star on GitHub</span>
                <span className="transition-transform group-hover:translate-x-1">→</span>
              </div>
            </div>
          </a>

          {/* Enterprise Card */}
          <a
            href="mailto:contact@onyxlab.ai"
            className="group relative overflow-hidden rounded-2xl border border-gray-200/50 bg-gradient-to-br from-purple-50 via-white to-purple-50/30 p-8 shadow-sm transition-all hover:scale-105 hover:shadow-xl dark:border-gray-800/50 dark:from-purple-950/30 dark:via-gray-900 dark:to-purple-950/20"
          >
            <div className="absolute right-0 top-0 h-24 w-24 translate-x-6 -translate-y-6 rounded-full bg-purple-500/20 blur-2xl" />
            <div className="relative">
              <div className="mb-4 inline-flex items-center justify-center rounded-xl bg-purple-100 p-3 dark:bg-purple-900/50">
                <Building2 className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="mb-2 text-xl font-bold text-gray-900 dark:text-white">
                Enterprise Support
              </h3>
              <p className="mb-4 text-gray-600 dark:text-gray-400">
                SLA guarantees, custom features, dedicated support, and deployment assistance
              </p>
              <div className="inline-flex items-center gap-2 text-sm font-medium text-purple-600 dark:text-purple-400">
                <MessageCircle className="h-4 w-4" />
                <span>Contact sales</span>
                <span className="transition-transform group-hover:translate-x-1">→</span>
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>
  )
}
