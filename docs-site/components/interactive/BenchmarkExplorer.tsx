'use client'

import React, { useState, useRef } from 'react'
import { motion, useInView, AnimatePresence } from 'motion/react'
import { BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Sparkles, TrendingUp, Zap, Shield, Gauge } from 'lucide-react'

const benchmarkData = [
  {
    name: 'Apollo',
    latency: 127,
    throughput: 450,
    accuracy: 94.2,
    gpuUtil: 88,
    color: '#3b82f6',
    icon: Zap,
    description: 'GPU-accelerated with CUDA optimization',
    highlights: ['Fastest latency', 'Highest throughput', 'Best accuracy']
  },
  {
    name: 'LangChain',
    latency: 892,
    throughput: 67,
    accuracy: 89.1,
    gpuUtil: 23,
    color: '#10b981',
    icon: Shield,
    description: 'Popular Python framework',
    highlights: ['Good accuracy', 'Wide ecosystem']
  },
  {
    name: 'LlamaIndex',
    latency: 654,
    throughput: 102,
    accuracy: 91.3,
    gpuUtil: 41,
    color: '#f59e0b',
    icon: Gauge,
    description: 'Data framework for LLM applications',
    highlights: ['Balanced performance', 'Good accuracy']
  },
  {
    name: 'Haystack',
    latency: 543,
    throughput: 134,
    accuracy: 90.7,
    gpuUtil: 35,
    color: '#8b5cf6',
    icon: TrendingUp,
    description: 'NLP framework by deepset',
    highlights: ['Decent throughput', 'Solid accuracy']
  }
]

const radarData = benchmarkData.map(item => ({
  system: item.name,
  'Latency (inv)': Math.round((1000 - item.latency) / 10),
  Throughput: Math.round(item.throughput / 5),
  Accuracy: item.accuracy,
  'GPU Util': item.gpuUtil
}))

interface BenchmarkCardProps {
  system: typeof benchmarkData[0]
  index: number
  focused: number | null
  setFocused: (index: number | null) => void
}

function BenchmarkCard({ system, index, focused, setFocused }: BenchmarkCardProps) {
  const isFocused = focused === index
  const isBlurred = focused !== null && !isFocused
  const Icon = system.icon

  return (
    <motion.div
      onHoverStart={() => setFocused(index)}
      onHoverEnd={() => setFocused(null)}
      animate={{
        scale: isFocused ? 1.05 : isBlurred ? 0.95 : 1,
        opacity: isBlurred ? 0.4 : 1,
        filter: isBlurred ? 'blur(4px)' : 'blur(0px)',
        rotateY: isFocused ? 5 : 0,
        z: isFocused ? 50 : 0
      }}
      transition={{
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1]
      }}
      className={`group relative cursor-pointer overflow-hidden rounded-2xl border-2 p-8 shadow-lg transition-all ${
        index === 0
          ? 'border-blue-500/50 bg-gradient-to-br from-blue-50 to-blue-100/50 dark:from-blue-950/30 dark:to-blue-900/20'
          : 'border-gray-200/50 bg-gradient-to-br from-white to-gray-50/50 dark:border-gray-800/50 dark:from-gray-900/50 dark:to-gray-800/30'
      }`}
      style={{
        transformStyle: 'preserve-3d',
        perspective: '1000px'
      }}
    >
      {/* Glow effect on hover */}
      <div
        className="absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: `radial-gradient(circle at 50% 50%, ${system.color}20, transparent 70%)`
        }}
      />

      {/* Badge */}
      {index === 0 && (
        <div className="absolute right-4 top-4 rounded-full bg-blue-600 px-3 py-1 text-xs font-bold text-white shadow-lg">
          BEST
        </div>
      )}

      {/* Icon */}
      <div
        className="mb-6 inline-flex rounded-xl p-3 shadow-lg"
        style={{ backgroundColor: `${system.color}20` }}
      >
        <Icon className="h-8 w-8" style={{ color: system.color }} />
      </div>

      {/* Title */}
      <h3 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
        {system.name}
      </h3>
      <p className="mb-6 text-sm text-gray-600 dark:text-gray-400">
        {system.description}
      </p>

      {/* Metrics Grid */}
      <div className="mb-6 grid grid-cols-2 gap-4">
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-500">Latency</div>
          <div className="text-2xl font-bold" style={{ color: system.color }}>
            {system.latency}ms
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-500">Throughput</div>
          <div className="text-2xl font-bold" style={{ color: system.color }}>
            {system.throughput} q/s
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-500">Accuracy</div>
          <div className="text-2xl font-bold" style={{ color: system.color }}>
            {system.accuracy}%
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-500">GPU Util</div>
          <div className="text-2xl font-bold" style={{ color: system.color }}>
            {system.gpuUtil}%
          </div>
        </div>
      </div>

      {/* Highlights */}
      <AnimatePresence>
        {isFocused && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-gray-200 pt-4 dark:border-gray-700"
          >
            <div className="text-xs font-semibold uppercase text-gray-500">Key Strengths</div>
            <ul className="mt-2 space-y-1">
              {system.highlights.map((highlight, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300"
                >
                  <Sparkles className="h-3 w-3" style={{ color: system.color }} />
                  {highlight}
                </motion.li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export function BenchmarkExplorer() {
  const [focused, setFocused] = useState<number | null>(null)
  const [activeView, setActiveView] = useState<'cards' | 'bar' | 'radar'>('cards')
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, amount: 0.2 })

  return (
    <div ref={ref} className="mx-auto my-32 max-w-7xl px-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.6 }}
        className="mb-12 text-center"
      >
        <h2 className="mb-4 text-4xl font-bold text-gray-900 dark:text-white md:text-5xl">
          Interactive Benchmark Explorer
        </h2>
        <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Explore comprehensive performance metrics across leading RAG frameworks
        </p>
      </motion.div>

      {/* View Selector */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="mb-8 flex justify-center gap-2"
      >
        {(['cards', 'bar', 'radar'] as const).map((view) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className={`rounded-lg px-6 py-2 font-semibold transition-all ${
              activeView === view
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
            }`}
          >
            {view === 'cards' ? 'Cards' : view === 'bar' ? 'Bar Chart' : 'Radar Chart'}
          </button>
        ))}
      </motion.div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeView === 'cards' && (
          <motion.div
            key="cards"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
            className="grid gap-6 md:grid-cols-2"
          >
            {benchmarkData.map((system, index) => (
              <BenchmarkCard
                key={system.name}
                system={system}
                index={index}
                focused={focused}
                setFocused={setFocused}
              />
            ))}
          </motion.div>
        )}

        {activeView === 'bar' && (
          <motion.div
            key="bar"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
            className="overflow-hidden rounded-2xl border border-gray-200 bg-white p-8 shadow-lg dark:border-gray-800 dark:bg-gray-900"
          >
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={benchmarkData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                <XAxis dataKey="name" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Legend />
                <Bar dataKey="throughput" fill="#3b82f6" name="Throughput (q/s)" radius={[8, 8, 0, 0]} />
                <Bar dataKey="accuracy" fill="#10b981" name="Accuracy (%)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        )}

        {activeView === 'radar' && (
          <motion.div
            key="radar"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
            className="overflow-hidden rounded-2xl border border-gray-200 bg-white p-8 shadow-lg dark:border-gray-800 dark:bg-gray-900"
          >
            <ResponsiveContainer width="100%" height={500}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis dataKey="system" stroke="#9ca3af" />
                <PolarRadiusAxis stroke="#9ca3af" />
                <Radar name="Apollo" dataKey="Latency (inv)" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
                <Radar name="Throughput" dataKey="Throughput" stroke="#10b981" fill="#10b981" fillOpacity={0.4} />
                <Radar name="Accuracy" dataKey="Accuracy" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.4} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Methodology Note */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={isInView ? { opacity: 1 } : {}}
        transition={{ duration: 0.6, delay: 0.8 }}
        className="mt-8 rounded-xl border border-blue-200/50 bg-blue-50/50 p-6 dark:border-blue-800/30 dark:bg-blue-950/30"
      >
        <h4 className="mb-2 font-semibold text-blue-900 dark:text-blue-100">Benchmark Methodology</h4>
        <p className="text-sm text-blue-800 dark:text-blue-200">
          All benchmarks conducted on NVIDIA A100 40GB with 100K document corpus, concurrent queries, and mixed complexity workloads.
          Latency measured at P95, throughput as queries/second at steady state.
        </p>
      </motion.div>
    </div>
  )
}
