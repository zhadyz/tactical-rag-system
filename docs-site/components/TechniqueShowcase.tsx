'use client'

import { useRef } from 'react'
import { motion, useInView } from 'motion/react'
import { Bot, ShieldCheck, GitBranch, FileSearch, Layers, Network, Cpu, Fingerprint, Search, CheckCircle2, BarChart3, Split, Lightbulb, Expand } from 'lucide-react'

type Category = 'retrieval' | 'indexing' | 'search' | 'quality'

interface Technique {
  num: string
  title: string
  desc: string
  category: Category
  icon: typeof Bot
  hero?: boolean
  href: string
}

const CATEGORY_STYLES: Record<Category, { badge: string; border: string; glow: string }> = {
  retrieval: { badge: 'text-blue-400 bg-blue-500/10 border-blue-500/20', border: 'hover:border-blue-500/30', glow: 'glow-border-blue' },
  indexing: { badge: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', border: 'hover:border-emerald-500/30', glow: 'glow-border-emerald' },
  search: { badge: 'text-violet-400 bg-violet-500/10 border-violet-500/20', border: 'hover:border-violet-500/30', glow: 'glow-border-purple' },
  quality: { badge: 'text-amber-400 bg-amber-500/10 border-amber-500/20', border: 'hover:border-amber-500/30', glow: 'glow-border-amber' },
}

const CATEGORY_LABELS: Record<Category, string> = {
  retrieval: 'Retrieval', indexing: 'Indexing', search: 'Search', quality: 'Quality'
}

const TECHNIQUES: Technique[] = [
  { num: '01', title: 'Agentic RAG', desc: 'LangGraph ReAct loop — the LLM autonomously decides which retrieval tools to invoke, iterating until it has sufficient evidence to answer.', category: 'retrieval', icon: Bot, hero: true, href: '/techniques/agentic-rag' },
  { num: '02', title: 'Contextual Retrieval', desc: 'Anthropic\'s technique: LLM prepends chunk-specific context before embedding. 49% fewer retrieval failures, 67% with reranking.', category: 'indexing', icon: FileSearch, hero: true, href: '/techniques/contextual-retrieval' },
  { num: '03', title: 'CRAG Quality Gate', desc: 'Cross-encoder evaluates every retrieved document as CORRECT, AMBIGUOUS, or INCORRECT before it reaches generation. Re-retrieves on failure.', category: 'retrieval', icon: ShieldCheck, hero: true, href: '/techniques/crag' },
  { num: '04', title: 'ColBERT Late Interaction', desc: 'Token-level MaxSim scoring catches specific facts that dense vectors miss.', category: 'search', icon: Fingerprint, href: '/techniques/colbert' },
  { num: '05', title: 'Proposition Indexing', desc: 'Atomic factual claims indexed as standalone searchable units for precision retrieval.', category: 'indexing', icon: Layers, href: '/techniques/proposition-indexing' },
  { num: '06', title: 'Hierarchical 4-Level', desc: 'L0 doc summaries → L1 sections → L2 semantic chunks → L3 propositions.', category: 'indexing', icon: GitBranch, href: '/techniques/hierarchical-indexing' },
  { num: '07', title: 'BGE-M3 Tri-Modal', desc: 'One model, three vector types: dense + sparse + ColBERT multi-vector.', category: 'search', icon: Cpu, href: '/techniques/bge-m3' },
  { num: '08', title: 'Knowledge Graph', desc: 'Entity relationships for structural queries via graph traversal.', category: 'search', icon: Network, href: '/techniques/knowledge-graph' },
  { num: '09', title: 'Self-Verification', desc: 'Post-generation claim-by-claim audit against source documents.', category: 'quality', icon: CheckCircle2, href: '/techniques/self-verification' },
  { num: '10', title: '6-Signal Confidence', desc: 'Multi-dimensional reliability scoring across retrieval, CRAG, and verification.', category: 'quality', icon: BarChart3, href: '/techniques/overview' },
  { num: '11', title: 'Query Decomposition', desc: 'Complex questions split into targeted sub-queries for parallel retrieval.', category: 'quality', icon: Split, href: '/techniques/overview' },
  { num: '12', title: 'HyDE', desc: 'Generate a hypothetical ideal answer, embed it, search for real matches.', category: 'quality', icon: Lightbulb, href: '/techniques/overview' },
  { num: '13', title: 'Multi-Hop Reasoning', desc: 'Follow cross-references iteratively across document boundaries.', category: 'retrieval', icon: Search, href: '/techniques/overview' },
  { num: '14', title: 'Parent Expansion', desc: 'Match a chunk, return the parent section for full context fidelity.', category: 'quality', icon: Expand, href: '/techniques/overview' },
]

function TechCard({ technique, index }: { technique: Technique; index: number }) {
  const style = CATEGORY_STYLES[technique.category]
  const Icon = technique.icon

  return (
    <motion.a
      href={technique.href}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.5, delay: index * 0.04, ease: [0.16, 1, 0.3, 1] }}
      className={`group relative block rounded-2xl border border-white/[0.06] p-6 transition-all duration-300 ${style.border} ${style.glow} ${technique.hero ? 'row-span-1 md:col-span-2' : ''}`}
      style={{ background: 'var(--forge-surface)' }}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${style.badge}`}>
          <Icon className="h-5 w-5" />
        </div>
        <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-wider uppercase ${style.badge}`}>
          {CATEGORY_LABELS[technique.category]}
        </span>
      </div>

      <div className="mb-1.5 text-[11px] font-bold tracking-wider text-zinc-600 font-mono">{technique.num}</div>
      <h3 className="mb-2 text-lg font-bold text-zinc-100 group-hover:text-white transition-colors">{technique.title}</h3>
      <p className="text-sm leading-relaxed text-zinc-500 group-hover:text-zinc-400 transition-colors">{technique.desc}</p>

      {/* Hover arrow */}
      <div className="absolute bottom-5 right-5 opacity-0 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-0 -translate-x-1">
        <span className="text-sm text-zinc-500">→</span>
      </div>
    </motion.a>
  )
}

export function TechniqueShowcase() {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-100px' })

  return (
    <section ref={ref} className="relative py-32 sm:py-40" style={{ background: 'var(--forge-bg)' }}>
      <div className="pointer-events-none absolute inset-0 bg-dot-grid opacity-20" />

      <div className="relative mx-auto max-w-7xl px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-16 max-w-2xl"
        >
          <div className="section-pill mb-6 text-blue-400 border-blue-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />
            14 Techniques
          </div>
          <h2 className="text-display-lg font-bold text-white mb-4">
            Every failure mode,{' '}
            <span className="text-gradient-blue">handled.</span>
          </h2>
          <p className="text-lg text-zinc-500 leading-relaxed">
            Each technique solves a specific retrieval failure. Together they form the most comprehensive RAG pipeline assembled for a single-GPU system.
          </p>
        </motion.div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {TECHNIQUES.map((t, i) => (
            <TechCard key={t.num} technique={t} index={i} />
          ))}
        </div>
      </div>
    </section>
  )
}
