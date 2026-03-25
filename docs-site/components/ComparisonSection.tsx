'use client'

import { motion } from 'motion/react'
import { X, Check } from 'lucide-react'

const ROWS = [
  { dimension: 'Retrieval', standard: 'Single-shot retrieve-then-read', forge: 'Agentic multi-step with tool use' },
  { dimension: 'Chunking', standard: 'Fixed-size character splits', forge: 'Hierarchical 4-level (doc/section/chunk/proposition)' },
  { dimension: 'Embeddings', standard: 'Single dense vector', forge: 'BGE-M3 tri-modal (dense + sparse + ColBERT)' },
  { dimension: 'Quality Gate', standard: 'None — trust whatever retrieves', forge: 'CRAG cross-encoder evaluation with re-retrieval' },
  { dimension: 'Verification', standard: 'None — hope for the best', forge: 'Claim-by-claim source verification' },
  { dimension: 'Context', standard: 'Raw chunks, no surrounding info', forge: 'Contextual enrichment (49% fewer failures)' },
  { dimension: 'Precision', standard: 'Chunk-level granularity', forge: 'Proposition-level atomic claims' },
  { dimension: 'Relationships', standard: 'Vector similarity only', forge: 'Knowledge graph with entity traversal' },
]

export function ComparisonSection() {
  return (
    <section className="relative py-32 sm:py-40" style={{ background: 'var(--forge-bg)' }}>
      <div className="relative mx-auto max-w-5xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-16 text-center"
        >
          <div className="section-pill mb-6 mx-auto w-fit text-amber-400 border-amber-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            Comparison
          </div>
          <h2 className="text-display-lg font-bold text-white mb-4">
            Standard RAG{' '}
            <span className="text-zinc-600">vs</span>{' '}
            <span className="text-gradient-forge">Forge</span>
          </h2>
        </motion.div>

        <div className="overflow-hidden rounded-2xl border border-white/[0.06]" style={{ background: 'var(--forge-surface)' }}>
          {/* Header */}
          <div className="grid grid-cols-[1fr_1fr_1fr] border-b border-white/[0.06] text-sm font-semibold">
            <div className="px-6 py-4 text-zinc-500" />
            <div className="px-6 py-4 text-zinc-500 text-center border-x border-white/[0.04]">Standard RAG</div>
            <div className="px-6 py-4 text-center text-gradient-blue font-bold">Forge V5</div>
          </div>

          {/* Rows */}
          {ROWS.map((row, i) => (
            <motion.div
              key={row.dimension}
              initial={{ opacity: 0, x: -10 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.05 }}
              className={`grid grid-cols-[1fr_1fr_1fr] text-sm ${i < ROWS.length - 1 ? 'border-b border-white/[0.04]' : ''}`}
            >
              <div className="px-6 py-4 font-semibold text-zinc-300">{row.dimension}</div>
              <div className="px-6 py-4 text-zinc-600 border-x border-white/[0.04] flex items-start gap-2">
                <X className="h-4 w-4 flex-shrink-0 text-red-500/60 mt-0.5" />
                <span>{row.standard}</span>
              </div>
              <div className="px-6 py-4 text-zinc-300 flex items-start gap-2">
                <Check className="h-4 w-4 flex-shrink-0 text-emerald-400 mt-0.5" />
                <span>{row.forge}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
