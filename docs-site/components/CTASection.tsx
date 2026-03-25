'use client'

import { motion } from 'motion/react'
import { ArrowRight, Github } from 'lucide-react'

export function CTASection() {
  return (
    <section className="relative py-32 sm:py-40 overflow-hidden" style={{ background: 'var(--forge-bg)' }}>
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[800px] rounded-full bg-gradient-radial from-blue-600/[0.06] via-indigo-600/[0.03] to-transparent blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-3xl px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="mb-4 font-display text-display-lg italic text-white">
            Ready to <span className="text-gradient-forge">forge?</span>
          </h2>
          <p className="mb-10 text-lg text-zinc-500 max-w-xl mx-auto">
            14 techniques. One GPU. No open-source system combines all of these.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <a href="/getting-started/quick-start"
              className="group relative inline-flex items-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-4 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition-all duration-300 hover:shadow-xl hover:shadow-blue-600/30 active:scale-[0.98]">
              <span className="relative z-10 flex items-center gap-2">
                Get Started
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-indigo-500 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
            </a>
            <a href="https://github.com/zhadyz/tactical-rag-system" target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.02] px-8 py-4 text-sm font-semibold text-zinc-300 backdrop-blur-sm transition-all duration-300 hover:border-white/[0.15] hover:bg-white/[0.05] active:scale-[0.98]">
              <Github className="h-4 w-4" />
              View Source
            </a>
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="relative mt-24 border-t border-white/[0.06] pt-8 text-center">
        <p className="text-xs text-zinc-600">
          Built by{' '}
          <a href="https://github.com/hollowed_eyes" className="text-zinc-500 hover:text-zinc-300 transition-colors">
            hollowed_eyes
          </a>{' '}
          &middot; Forge V5 is a portfolio project demonstrating world-class RAG engineering.
        </p>
      </div>
    </section>
  )
}
