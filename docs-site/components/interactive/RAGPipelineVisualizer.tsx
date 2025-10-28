'use client'

import React, { useState, useRef, useEffect } from 'react'
import { motion, useInView, AnimatePresence } from 'motion/react'
import { FileText, Brain, Zap, Target, Database, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react'

const pipelineStages = [
  {
    id: 'ingest',
    title: 'Document Ingestion',
    icon: FileText,
    color: '#3b82f6',
    description: 'Multi-format parsing with GPU-accelerated OCR',
    metrics: { time: '45ms', throughput: '1200 docs/s' },
    details: ['PDF, DOCX, HTML parsing', 'Table extraction', 'Image OCR', 'Metadata extraction']
  },
  {
    id: 'chunk',
    title: 'Intelligent Chunking',
    icon: Database,
    color: '#8b5cf6',
    description: 'Adaptive chunk sizing based on content complexity',
    metrics: { time: '23ms', chunks: '450/doc' },
    details: ['Semantic boundaries', 'Context preservation', 'Overlap optimization', 'Multi-scale chunks']
  },
  {
    id: 'embed',
    title: 'GPU Embeddings',
    icon: Zap,
    color: '#f59e0b',
    description: 'CUDA-accelerated vector generation',
    metrics: { time: '12ms', vectors: '1536-dim' },
    details: ['Batch processing', 'Model quantization', 'Cache optimization', '10x CPU speedup']
  },
  {
    id: 'index',
    title: 'Vector Indexing',
    icon: Brain,
    color: '#10b981',
    description: 'HNSW graph construction on GPU',
    metrics: { time: '67ms', recall: '99.2%' },
    details: ['Graph building', 'Approximate NN', 'Dynamic updates', 'Multi-index support']
  },
  {
    id: 'retrieve',
    title: 'Retrieval',
    icon: Target,
    color: '#ec4899',
    description: 'Hybrid search with re-ranking',
    metrics: { time: '34ms', precision: '94.8%' },
    details: ['Vector similarity', 'BM25 fusion', 'Cross-encoder rerank', 'Top-k selection']
  }
]

interface AnimatedBeamProps {
  from: string
  to: string
  active: boolean
  delay?: number
}

function AnimatedBeam({ from, to, active, delay = 0 }: AnimatedBeamProps) {
  const [path, setPath] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const updatePath = () => {
      if (!containerRef.current) return
      const fromEl = document.getElementById(from)
      const toEl = document.getElementById(to)
      if (!fromEl || !toEl) return

      const container = containerRef.current.getBoundingClientRect()
      const fromRect = fromEl.getBoundingClientRect()
      const toRect = toEl.getBoundingClientRect()

      const x1 = fromRect.right - container.left
      const y1 = fromRect.top + fromRect.height / 2 - container.top
      const x2 = toRect.left - container.left
      const y2 = toRect.top + toRect.height / 2 - container.top

      const curve = Math.abs(x2 - x1) * 0.2
      setPath(`M ${x1} ${y1} Q ${(x1 + x2) / 2} ${y1 - curve} ${x2} ${y2}`)
    }

    updatePath()
    window.addEventListener('resize', updatePath)
    return () => window.removeEventListener('resize', updatePath)
  }, [from, to])

  return (
    <svg
      ref={containerRef}
      className="pointer-events-none absolute inset-0"
      style={{ width: '100%', height: '100%' }}
    >
      <defs>
        <linearGradient id={`gradient-${from}-${to}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0" />
          <stop offset="50%" stopColor="#3b82f6" stopOpacity="1" />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d={path}
        stroke="#374151"
        strokeWidth="2"
        fill="none"
        opacity="0.2"
      />
      {active && (
        <motion.path
          d={path}
          stroke={`url(#gradient-${from}-${to})`}
          strokeWidth="3"
          fill="none"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{
            pathLength: { duration: 1.5, delay, ease: 'easeInOut' },
            opacity: { duration: 0.3, delay }
          }}
        />
      )}
    </svg>
  )
}

interface StageNodeProps {
  stage: typeof pipelineStages[0]
  index: number
  selected: string | null
  setSelected: (id: string) => void
  active: boolean
}

function StageNode({ stage, index, selected, setSelected, active }: StageNodeProps) {
  const Icon = stage.icon
  const isSelected = selected === stage.id

  return (
    <motion.div
      id={stage.id}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.2, duration: 0.5 }}
      className="relative z-10"
    >
      <motion.div
        onClick={() => setSelected(stage.id)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        animate={{
          scale: isSelected ? 1.1 : 1,
          y: isSelected ? -8 : 0
        }}
        className={`group relative cursor-pointer overflow-hidden rounded-2xl border-2 bg-white p-6 shadow-lg transition-all dark:bg-gray-900 ${
          isSelected
            ? 'border-blue-500 shadow-2xl shadow-blue-500/50'
            : 'border-gray-200 hover:border-gray-300 dark:border-gray-800 dark:hover:border-gray-700'
        }`}
        style={{ width: '200px' }}
      >
        {/* Glow effect */}
        {active && (
          <div
            className="absolute inset-0 opacity-50"
            style={{
              background: `radial-gradient(circle at 50% 50%, ${stage.color}30, transparent 70%)`
            }}
          />
        )}

        {/* Active pulse */}
        {active && (
          <motion.div
            className="absolute inset-0 rounded-2xl border-2"
            style={{ borderColor: stage.color }}
            animate={{ scale: [1, 1.05, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}

        <div className="relative">
          {/* Icon */}
          <div
            className="mb-3 inline-flex rounded-xl p-2"
            style={{ backgroundColor: `${stage.color}20` }}
          >
            <Icon className="h-6 w-6" style={{ color: stage.color }} />
          </div>

          {/* Title */}
          <h4 className="mb-1 text-sm font-bold text-gray-900 dark:text-white">
            {stage.title}
          </h4>

          {/* Metrics */}
          <div className="space-y-0.5 text-xs text-gray-600 dark:text-gray-400">
            {Object.entries(stage.metrics).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="capitalize">{key}:</span>
                <span className="font-semibold">{value}</span>
              </div>
            ))}
          </div>

          {/* Active indicator */}
          {active && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -right-2 -top-2"
            >
              <div className="rounded-full bg-green-500 p-1 shadow-lg">
                <CheckCircle2 className="h-4 w-4 text-white" />
              </div>
            </motion.div>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}

export function RAGPipelineVisualizer() {
  const [selected, setSelected] = useState<string | null>(null)
  const [playing, setPlaying] = useState(false)
  const [activeStage, setActiveStage] = useState<number>(-1)
  const [scrollProgress, setScrollProgress] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const sectionRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, amount: 0.2 })

  // Apple-style scroll-driven horizontal navigation
  useEffect(() => {
    const handleScroll = () => {
      if (!sectionRef.current || !scrollContainerRef.current) return

      const section = sectionRef.current
      const container = scrollContainerRef.current
      const rect = section.getBoundingClientRect()
      const windowHeight = window.innerHeight

      // Calculate when section is centered in viewport
      const sectionCenter = rect.top + rect.height / 2
      const viewportCenter = windowHeight / 2
      const distanceFromCenter = sectionCenter - viewportCenter

      // If section is roughly centered, use scroll to drive horizontal movement
      if (Math.abs(distanceFromCenter) < windowHeight * 0.3) {
        // Calculate scroll progress (0 to 1) based on vertical scroll position
        const scrollRange = windowHeight * 0.6 // Range where horizontal scroll is active
        const progress = Math.max(0, Math.min(1, 0.5 - distanceFromCenter / scrollRange))

        setScrollProgress(progress)

        // Drive horizontal scroll based on vertical scroll
        const maxScrollLeft = container.scrollWidth - container.clientWidth
        container.scrollLeft = progress * maxScrollLeft

        // Prevent default scroll if we're in the "locked" range
        if (progress > 0 && progress < 1 && rect.top < viewportCenter && rect.bottom > viewportCenter) {
          // Section is locked, user must scroll through horizontal content first
          document.body.style.overflowY = progress >= 0.99 ? 'auto' : 'hidden'
        } else {
          document.body.style.overflowY = 'auto'
        }
      } else {
        document.body.style.overflowY = 'auto'
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: false })
    return () => {
      window.removeEventListener('scroll', handleScroll)
      document.body.style.overflowY = 'auto'
    }
  }, [])

  const playAnimation = () => {
    setPlaying(true)
    setActiveStage(0)

    pipelineStages.forEach((_, index) => {
      setTimeout(() => {
        setActiveStage(index)
        if (index === pipelineStages.length - 1) {
          setTimeout(() => {
            setPlaying(false)
            setActiveStage(-1)
          }, 2000)
        }
      }, index * 1500)
    })
  }

  const selectedStage = selected ? pipelineStages.find(s => s.id === selected) : null

  return (
    <div ref={sectionRef} className="mx-auto my-32 max-w-7xl px-4">
      <div ref={ref}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="mb-12 text-center"
        >
        <h2 className="mb-4 text-4xl font-bold text-gray-900 dark:text-white md:text-5xl">
          RAG Pipeline Visualizer
        </h2>
        <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Click any stage to explore or watch the data flow through Apollo's pipeline
        </p>
      </motion.div>

      {/* Play Button */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={isInView ? { opacity: 1 } : {}}
        transition={{ delay: 0.3 }}
        className="mb-8 flex justify-center"
      >
        <button
          onClick={playAnimation}
          disabled={playing}
          className="group relative overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-3 font-semibold text-white shadow-lg transition-all hover:scale-105 hover:shadow-2xl disabled:opacity-50 disabled:hover:scale-100"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-blue-700 to-purple-700 opacity-0 transition-opacity group-hover:opacity-100" />
          <span className="relative flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            {playing ? 'Processing...' : 'Animate Data Flow'}
          </span>
        </button>
      </motion.div>

      {/* Pipeline Visualization */}
      <div
        ref={scrollContainerRef}
        className="relative overflow-x-auto rounded-3xl border border-gray-200 bg-gradient-to-br from-gray-50 to-gray-100/50 p-12 dark:border-gray-800 dark:from-gray-900 dark:to-gray-800/50 scroll-smooth"
        style={{
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          WebkitOverflowScrolling: 'touch'
        } as React.CSSProperties}
      >
        <div className="min-w-max">
          {/* Connection lines */}
          {pipelineStages.slice(0, -1).map((stage, index) => (
            <AnimatedBeam
              key={`beam-${index}`}
              from={stage.id}
              to={pipelineStages[index + 1].id}
              active={playing && activeStage >= index}
              delay={index * 1.5}
            />
          ))}

          {/* Stage nodes */}
          <div className="flex items-center justify-start gap-6">
            {pipelineStages.map((stage, index) => (
              <React.Fragment key={stage.id}>
                <StageNode
                  stage={stage}
                  index={index}
                  selected={selected}
                  setSelected={setSelected}
                  active={playing && activeStage === index}
                />
                {index < pipelineStages.length - 1 && (
                  <ArrowRight className="h-6 w-6 flex-shrink-0 text-gray-400" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Details Panel */}
      <AnimatePresence mode="wait">
        {selectedStage && (
          <motion.div
            key={selectedStage.id}
            initial={{ opacity: 0, y: 20, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -20, height: 0 }}
            transition={{ duration: 0.4 }}
            className="mt-8 overflow-hidden rounded-2xl border-2 bg-white p-8 shadow-xl dark:border-gray-800 dark:bg-gray-900"
            style={{ borderColor: selectedStage.color }}
          >
            <div className="flex items-start gap-6">
              <div
                className="rounded-2xl p-4"
                style={{ backgroundColor: `${selectedStage.color}20` }}
              >
                {React.createElement(selectedStage.icon, {
                  className: 'h-12 w-12',
                  style: { color: selectedStage.color }
                })}
              </div>
              <div className="flex-1">
                <h3 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
                  {selectedStage.title}
                </h3>
                <p className="mb-6 text-gray-600 dark:text-gray-400">
                  {selectedStage.description}
                </p>
                <div className="grid gap-3 md:grid-cols-2">
                  {selectedStage.details.map((detail, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center gap-2"
                    >
                      <div className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: selectedStage.color }} />
                      <span className="text-sm text-gray-700 dark:text-gray-300">{detail}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      </div>
    </div>
  )
}
