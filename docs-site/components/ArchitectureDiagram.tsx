'use client'

import React, { useState } from 'react'
import { cn } from '@/lib/utils'

interface BoxProps {
  label: string
  sublabel?: string
  className?: string
  small?: boolean
}

function Box({ label, sublabel, className, small }: BoxProps) {
  return (
    <div
      className={cn(
        'rounded-lg border px-3 py-2 text-center font-medium transition-all duration-200 hover:scale-[1.03]',
        small ? 'text-xs' : 'text-sm',
        className
      )}
    >
      <div>{label}</div>
      {sublabel && (
        <div className={cn('mt-0.5 font-normal opacity-70', small ? 'text-[10px]' : 'text-xs')}>
          {sublabel}
        </div>
      )}
    </div>
  )
}

function Arrow({ direction = 'down', className }: { direction?: 'down' | 'right'; className?: string }) {
  if (direction === 'right') {
    return (
      <div className={cn('flex items-center justify-center px-1', className)}>
        <svg width="24" height="12" viewBox="0 0 24 12" fill="none" className="text-gray-400 dark:text-gray-600">
          <path d="M0 6H20M20 6L15 1M20 6L15 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    )
  }
  return (
    <div className={cn('flex items-center justify-center py-1', className)}>
      <svg width="12" height="24" viewBox="0 0 12 24" fill="none" className="text-gray-400 dark:text-gray-600">
        <path d="M6 0V20M6 20L1 15M6 20L11 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  )
}

function TierLabel({ label, color }: { label: string; color: string }) {
  return (
    <div
      className={cn(
        'absolute -left-1 top-3 rounded-r-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white sm:px-3 sm:text-xs',
        color
      )}
    >
      {label}
    </div>
  )
}

export function ArchitectureDiagram() {
  const [activeTier, setActiveTier] = useState<string | null>(null)

  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <div className="mb-10 text-center">
        <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
          System Architecture
        </h2>
        <p className="mx-auto max-w-2xl text-gray-600 dark:text-gray-400">
          Three-tier architecture: desktop app, agentic backend, and GPU-optimized infrastructure.
        </p>
      </div>

      <div className="mx-auto max-w-5xl space-y-3">
        {/* TIER 1: Frontend */}
        <div
          className={cn(
            'relative rounded-xl border-2 p-6 pt-10 transition-all duration-300',
            activeTier === 'frontend'
              ? 'border-sky-400 bg-sky-50/60 shadow-lg shadow-sky-500/10 dark:border-sky-500 dark:bg-sky-950/30'
              : 'border-sky-200 bg-sky-50/30 dark:border-sky-900 dark:bg-sky-950/10'
          )}
          onMouseEnter={() => setActiveTier('frontend')}
          onMouseLeave={() => setActiveTier(null)}
        >
          <TierLabel label="Frontend" color="bg-sky-500" />

          <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center sm:gap-4">
            <Box
              label="Tauri Desktop"
              sublabel="Native shell"
              className="border-sky-300 bg-white text-sky-800 dark:border-sky-700 dark:bg-sky-950/50 dark:text-sky-200"
            />
            <Arrow direction="right" className="hidden sm:flex" />
            <Arrow direction="down" className="sm:hidden" />
            <Box
              label="React UI"
              sublabel="TypeScript + Tailwind"
              className="border-sky-300 bg-white text-sky-800 dark:border-sky-700 dark:bg-sky-950/50 dark:text-sky-200"
            />
            <Arrow direction="right" className="hidden sm:flex" />
            <Arrow direction="down" className="sm:hidden" />
            <div className="flex flex-wrap justify-center gap-2">
              {['Agent Reasoning', 'Chat', 'Sources'].map((panel) => (
                <Box
                  key={panel}
                  label={panel}
                  small
                  className="border-sky-200 bg-sky-100/50 text-sky-700 dark:border-sky-800 dark:bg-sky-900/40 dark:text-sky-300"
                />
              ))}
            </div>
          </div>
        </div>

        <Arrow />

        {/* TIER 2: Backend */}
        <div
          className={cn(
            'relative rounded-xl border-2 p-6 pt-10 transition-all duration-300',
            activeTier === 'backend'
              ? 'border-indigo-400 bg-indigo-50/60 shadow-lg shadow-indigo-500/10 dark:border-indigo-500 dark:bg-indigo-950/30'
              : 'border-indigo-200 bg-indigo-50/30 dark:border-indigo-900 dark:bg-indigo-950/10'
          )}
          onMouseEnter={() => setActiveTier('backend')}
          onMouseLeave={() => setActiveTier(null)}
        >
          <TierLabel label="Backend" color="bg-indigo-500" />

          {/* Row 1: FastAPI -> LangGraph Agent */}
          <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center sm:gap-4">
            <Box
              label="FastAPI"
              sublabel="SSE streaming"
              className="border-indigo-300 bg-white text-indigo-800 dark:border-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-200"
            />
            <Arrow direction="right" className="hidden sm:flex" />
            <Arrow direction="down" className="sm:hidden" />
            <Box
              label="LangGraph Agent"
              sublabel="Agentic orchestrator"
              className="border-indigo-400 bg-indigo-100/50 text-indigo-900 font-semibold dark:border-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-100"
            />
          </div>

          <Arrow />

          {/* Row 2: Tools */}
          <div className="mb-3 text-center text-xs font-medium text-indigo-500 dark:text-indigo-400">
            Tools
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            {[
              { name: 'semantic_search', desc: 'Dense vectors' },
              { name: 'proposition_search', desc: 'Atomic claims' },
              { name: 'keyword_search', desc: 'BM25 sparse' },
              { name: 'graph_traverse', desc: 'Entity links' },
            ].map((tool) => (
              <Box
                key={tool.name}
                label={tool.name}
                sublabel={tool.desc}
                small
                className="border-indigo-200 bg-white font-mono text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-300"
              />
            ))}
          </div>

          <Arrow />

          {/* Row 3: Processing pipeline */}
          <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center sm:gap-3">
            <Box
              label="CRAG Gate"
              sublabel="Quality filter"
              small
              className="border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-200"
            />
            <Arrow direction="right" className="hidden sm:flex" />
            <Arrow direction="down" className="sm:hidden" />
            <Box
              label="ColBERT Reranker"
              sublabel="Late interaction"
              small
              className="border-purple-300 bg-purple-50 text-purple-800 dark:border-purple-700 dark:bg-purple-950/40 dark:text-purple-200"
            />
            <Arrow direction="right" className="hidden sm:flex" />
            <Arrow direction="down" className="sm:hidden" />
            <Box
              label="Generator"
              sublabel="Streaming LLM"
              small
              className="border-indigo-300 bg-indigo-50 text-indigo-800 dark:border-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200"
            />
            <Arrow direction="right" className="hidden sm:flex" />
            <Arrow direction="down" className="sm:hidden" />
            <Box
              label="Verifier"
              sublabel="Claim checking"
              small
              className="border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-200"
            />
          </div>
        </div>

        <Arrow />

        {/* TIER 3: Infrastructure */}
        <div
          className={cn(
            'relative rounded-xl border-2 p-6 pt-10 transition-all duration-300',
            activeTier === 'infra'
              ? 'border-emerald-400 bg-emerald-50/60 shadow-lg shadow-emerald-500/10 dark:border-emerald-500 dark:bg-emerald-950/30'
              : 'border-emerald-200 bg-emerald-50/30 dark:border-emerald-900 dark:bg-emerald-950/10'
          )}
          onMouseEnter={() => setActiveTier('infra')}
          onMouseLeave={() => setActiveTier(null)}
        >
          <TierLabel label="Infra" color="bg-emerald-500" />

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-emerald-200 bg-white p-4 text-center dark:border-emerald-800 dark:bg-emerald-950/40">
              <div className="mb-1 text-sm font-semibold text-emerald-800 dark:text-emerald-200">
                Qdrant
              </div>
              <div className="space-y-1">
                {['Dense vectors', 'Sparse (BM25)', 'ColBERT multi-vec'].map((item) => (
                  <div
                    key={item}
                    className="rounded bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-emerald-200 bg-white p-4 text-center dark:border-emerald-800 dark:bg-emerald-950/40">
              <div className="mb-1 text-sm font-semibold text-emerald-800 dark:text-emerald-200">
                Redis
              </div>
              <div className="space-y-1">
                {['Semantic cache', 'Query cache', 'Result cache', 'Session cache'].map((item) => (
                  <div
                    key={item}
                    className="rounded bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-emerald-200 bg-white p-4 text-center dark:border-emerald-800 dark:bg-emerald-950/40">
              <div className="mb-1 text-sm font-semibold text-emerald-800 dark:text-emerald-200">
                llama.cpp
              </div>
              <div className="space-y-1">
                {['Qwen 3 14B', 'Q4_K_M quant', 'CUDA GPU'].map((item) => (
                  <div
                    key={item}
                    className="rounded bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
