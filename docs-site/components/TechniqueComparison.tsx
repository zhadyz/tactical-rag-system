'use client'

import React, { useState } from 'react'
import { cn } from '@/lib/utils'
import { Check, X, ArrowRight } from 'lucide-react'

interface ComparisonRow {
  aspect: string
  standard: string
  forge: string
  impact?: string
}

const comparisons: ComparisonRow[] = [
  {
    aspect: 'Retrieval',
    standard: 'Single-shot',
    forge: 'Agentic multi-step',
    impact: 'Finds answers standard RAG misses entirely',
  },
  {
    aspect: 'Chunking',
    standard: 'Fixed-size',
    forge: 'Hierarchical 4-level',
    impact: 'Doc \u2192 Section \u2192 Chunk \u2192 Proposition',
  },
  {
    aspect: 'Embeddings',
    standard: 'Single dense vector',
    forge: 'Tri-modal (dense+sparse+ColBERT)',
    impact: '3 complementary retrieval signals',
  },
  {
    aspect: 'Quality Gate',
    standard: 'None',
    forge: 'CRAG with re-retrieval',
    impact: 'Filters irrelevant docs before generation',
  },
  {
    aspect: 'Verification',
    standard: 'None',
    forge: 'Claim-by-claim',
    impact: 'Every claim traced to source',
  },
  {
    aspect: 'Context',
    standard: 'Raw chunks',
    forge: 'Contextually enriched',
    impact: '49% better retrieval recall',
  },
  {
    aspect: 'Precision',
    standard: 'Chunk-level',
    forge: 'Proposition-level',
    impact: 'Atomic facts, not paragraphs',
  },
  {
    aspect: 'Relationships',
    standard: 'Vector similarity only',
    forge: 'Knowledge graph traversal',
    impact: 'Follows entity relationships',
  },
]

export function TechniqueComparison() {
  const [hoveredRow, setHoveredRow] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table')

  return (
    <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
      <div className="mb-10 text-center">
        <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
          Standard RAG vs <span className="text-gradient">Forge V5</span>
        </h2>
        <p className="mx-auto max-w-2xl text-gray-600 dark:text-gray-400">
          Every dimension of RAG, reimagined. This is not an incremental improvement.
        </p>
      </div>

      {/* View toggle */}
      <div className="mb-6 flex justify-center">
        <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-0.5 dark:border-gray-800 dark:bg-gray-900">
          <button
            onClick={() => setViewMode('table')}
            className={cn(
              'rounded-md px-4 py-1.5 text-sm font-medium transition-all',
              viewMode === 'table'
                ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-800 dark:text-white'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            )}
          >
            Table
          </button>
          <button
            onClick={() => setViewMode('cards')}
            className={cn(
              'rounded-md px-4 py-1.5 text-sm font-medium transition-all',
              viewMode === 'cards'
                ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-800 dark:text-white'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            )}
          >
            Cards
          </button>
        </div>
      </div>

      {viewMode === 'table' ? (
        /* Table view */
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 sm:px-6">
                    Aspect
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-red-500 dark:text-red-400 sm:px-6">
                    <span className="flex items-center gap-1.5">
                      <X className="h-3.5 w-3.5" />
                      Standard RAG
                    </span>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 sm:px-6">
                    <span className="flex items-center gap-1.5">
                      <Check className="h-3.5 w-3.5" />
                      Forge V5
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((row, idx) => (
                  <tr
                    key={row.aspect}
                    className={cn(
                      'border-b border-gray-100 transition-colors last:border-0 dark:border-gray-800/50',
                      hoveredRow === idx
                        ? 'bg-blue-50/50 dark:bg-blue-950/20'
                        : idx % 2 === 0
                        ? 'bg-white dark:bg-gray-900'
                        : 'bg-gray-50/50 dark:bg-gray-950/30'
                    )}
                    onMouseEnter={() => setHoveredRow(idx)}
                    onMouseLeave={() => setHoveredRow(null)}
                  >
                    <td className="px-4 py-3.5 sm:px-6">
                      <div className="text-sm font-semibold text-gray-900 dark:text-white">
                        {row.aspect}
                      </div>
                      {row.impact && hoveredRow === idx && (
                        <div className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                          {row.impact}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3.5 sm:px-6">
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-red-100 dark:bg-red-950/40">
                          <X className="h-3 w-3 text-red-500" />
                        </span>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {row.standard}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 sm:px-6">
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-950/40">
                          <Check className="h-3 w-3 text-emerald-500" />
                        </span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {row.forge}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Cards view */
        <div className="grid gap-4 sm:grid-cols-2">
          {comparisons.map((row) => (
            <div
              key={row.aspect}
              className="group rounded-xl border border-gray-200 bg-white p-5 transition-all hover:shadow-lg hover:border-blue-300 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-blue-700"
            >
              <div className="mb-3 text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                {row.aspect}
              </div>

              <div className="flex items-center gap-3">
                {/* Standard */}
                <div className="flex-1 rounded-lg bg-red-50 p-3 dark:bg-red-950/20">
                  <div className="mb-1 flex items-center gap-1.5">
                    <X className="h-3.5 w-3.5 text-red-400" />
                    <span className="text-[10px] font-semibold uppercase text-red-500">Standard</span>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{row.standard}</div>
                </div>

                {/* Arrow */}
                <ArrowRight className="h-4 w-4 flex-shrink-0 text-gray-300 dark:text-gray-700" />

                {/* Forge */}
                <div className="flex-1 rounded-lg bg-emerald-50 p-3 dark:bg-emerald-950/20">
                  <div className="mb-1 flex items-center gap-1.5">
                    <Check className="h-3.5 w-3.5 text-emerald-500" />
                    <span className="text-[10px] font-semibold uppercase text-emerald-600 dark:text-emerald-400">Forge</span>
                  </div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">{row.forge}</div>
                </div>
              </div>

              {row.impact && (
                <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                  {'\u2192'} {row.impact}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Bottom summary */}
      <div className="mt-8 rounded-xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-blue-50 p-5 dark:border-emerald-800 dark:from-emerald-950/20 dark:to-blue-950/20">
        <div className="flex flex-col items-center gap-3 text-center sm:flex-row sm:text-left">
          <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-emerald-100 text-2xl dark:bg-emerald-900/50">
            {'\u{1F680}'}
          </div>
          <div>
            <div className="text-base font-semibold text-gray-900 dark:text-white">
              8 dimensions. 0 compromises.
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Forge V5 advances every aspect of RAG — from retrieval to verification — while running entirely on a single 16GB GPU.
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
