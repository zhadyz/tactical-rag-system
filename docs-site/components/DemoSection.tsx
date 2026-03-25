'use client'

import { motion } from 'motion/react'
import { LiveDemo } from './LiveDemo'

export function DemoSection() {
  return (
    <section className="relative py-32 sm:py-40" style={{ background: 'var(--forge-bg)' }}>
      {/* Glow behind demo */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[800px] rounded-full bg-gradient-radial from-indigo-600/[0.05] via-blue-600/[0.02] to-transparent blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-4xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-12 text-center"
        >
          <div className="section-pill mb-6 mx-auto w-fit text-emerald-400 border-emerald-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Live Demo
          </div>
          <h2 className="text-display-lg font-bold text-white mb-4">
            Watch the agent{' '}
            <span className="text-gradient-blue">think.</span>
          </h2>
          <p className="text-lg text-zinc-500 max-w-2xl mx-auto">
            A real agentic query: tool selection, CRAG evaluation, ColBERT reranking, token streaming, and claim verification — all visible in real-time.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.1 }}
        >
          <LiveDemo />
        </motion.div>
      </div>
    </section>
  )
}
