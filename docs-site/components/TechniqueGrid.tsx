'use client'

import React, { useState } from 'react'
import { cn } from '@/lib/utils'

type Category = 'Retrieval' | 'Indexing' | 'Search' | 'Quality'

interface Technique {
  icon: string
  title: string
  description: string
  category: Category
}

const categoryStyles: Record<Category, { badge: string; border: string; glow: string }> = {
  Retrieval: {
    badge: 'bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300',
    border: 'hover:border-blue-400 dark:hover:border-blue-500',
    glow: 'group-hover:shadow-blue-500/10 dark:group-hover:shadow-blue-500/20',
  },
  Indexing: {
    badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300',
    border: 'hover:border-emerald-400 dark:hover:border-emerald-500',
    glow: 'group-hover:shadow-emerald-500/10 dark:group-hover:shadow-emerald-500/20',
  },
  Search: {
    badge: 'bg-purple-100 text-purple-700 dark:bg-purple-950/50 dark:text-purple-300',
    border: 'hover:border-purple-400 dark:hover:border-purple-500',
    glow: 'group-hover:shadow-purple-500/10 dark:group-hover:shadow-purple-500/20',
  },
  Quality: {
    badge: 'bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300',
    border: 'hover:border-amber-400 dark:hover:border-amber-500',
    glow: 'group-hover:shadow-amber-500/10 dark:group-hover:shadow-amber-500/20',
  },
}

const techniques: Technique[] = [
  { icon: '\u{1F916}', title: 'Agentic RAG', description: 'LLM drives multi-step retrieval decisions', category: 'Retrieval' },
  { icon: '\u{1F6E1}', title: 'CRAG Quality Gate', description: 'Filter irrelevant docs before generation', category: 'Retrieval' },
  { icon: '\u{1F517}', title: 'Multi-Hop Reasoning', description: 'Follow cross-references iteratively', category: 'Retrieval' },
  { icon: '\u{1F4D6}', title: 'Contextual Retrieval', description: 'LLM-enriched chunk context for 49% better recall', category: 'Indexing' },
  { icon: '\u{2699}', title: 'Proposition Indexing', description: 'Atomic claims for precision retrieval', category: 'Indexing' },
  { icon: '\u{1F3D7}', title: 'Hierarchical 4-Level', description: 'Doc \u2192 Section \u2192 Chunk \u2192 Proposition', category: 'Indexing' },
  { icon: '\u{1F50D}', title: 'BGE-M3 Tri-Modal', description: 'Dense + sparse + ColBERT in one model', category: 'Search' },
  { icon: '\u{1F3AF}', title: 'ColBERT Late Interaction', description: 'Token-level matching for specific facts', category: 'Search' },
  { icon: '\u{1F578}', title: 'Knowledge Graph', description: 'Entity relationships for structural queries', category: 'Search' },
  { icon: '\u2705', title: 'Self-Verification', description: 'Claim-by-claim source verification', category: 'Quality' },
  { icon: '\u{1F4CA}', title: '6-Signal Confidence', description: 'Multi-dimensional answer reliability scoring', category: 'Quality' },
  { icon: '\u{1F9E9}', title: 'Query Decomposition', description: 'Break complex questions into sub-queries', category: 'Quality' },
  { icon: '\u{1F4A1}', title: 'HyDE', description: 'Hypothetical document embeddings for semantic matching', category: 'Quality' },
  { icon: '\u{1F4C2}', title: 'Parent Expansion', description: 'Retrieve chunk, return section for context', category: 'Quality' },
]

const allCategories: Category[] = ['Retrieval', 'Indexing', 'Search', 'Quality']

export function TechniqueGrid() {
  const [activeFilter, setActiveFilter] = useState<Category | 'All'>('All')

  const filteredTechniques =
    activeFilter === 'All'
      ? techniques
      : techniques.filter((t) => t.category === activeFilter)

  return (
    <section className="mx-auto max-w-7xl px-6 py-20">
      {/* Section header */}
      <div className="mb-12 text-center">
        <h2 className="mb-4 text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
          <span className="text-gradient">14 Techniques</span>, One System
        </h2>
        <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Every cutting-edge RAG technique, integrated and optimized to work together on a single GPU.
        </p>
      </div>

      {/* Filter buttons */}
      <div className="mb-10 flex flex-wrap justify-center gap-2">
        <button
          onClick={() => setActiveFilter('All')}
          className={cn(
            'rounded-full px-4 py-1.5 text-sm font-medium transition-all',
            activeFilter === 'All'
              ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'
          )}
        >
          All ({techniques.length})
        </button>
        {allCategories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveFilter(cat)}
            className={cn(
              'rounded-full px-4 py-1.5 text-sm font-medium transition-all',
              activeFilter === cat
                ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'
            )}
          >
            {cat} ({techniques.filter((t) => t.category === cat).length})
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filteredTechniques.map((technique) => {
          const styles = categoryStyles[technique.category]
          return (
            <div
              key={technique.title}
              className={cn(
                'group relative rounded-xl border border-gray-200 bg-white p-5 transition-all duration-300 dark:border-gray-800 dark:bg-gray-900/80',
                styles.border,
                'hover:shadow-lg',
                styles.glow
              )}
            >
              {/* Icon */}
              <div className="mb-3 text-2xl">{technique.icon}</div>

              {/* Title */}
              <h3 className="mb-1.5 text-base font-semibold text-gray-900 dark:text-white">
                {technique.title}
              </h3>

              {/* Description */}
              <p className="mb-3 text-sm leading-relaxed text-gray-600 dark:text-gray-400">
                {technique.description}
              </p>

              {/* Category badge */}
              <span
                className={cn(
                  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                  styles.badge
                )}
              >
                {technique.category}
              </span>
            </div>
          )
        })}
      </div>
    </section>
  )
}
