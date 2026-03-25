'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Play, RotateCcw, Brain, Search, Shield, CheckCircle, Zap, FileText, Send } from 'lucide-react'

interface DemoEvent {
  type: 'thinking' | 'tool_call' | 'tool_result' | 'crag' | 'rerank' | 'token' | 'verify' | 'done'
  icon: typeof Brain
  color: string
  label: string
  content: string
  delay: number
  tokens?: string
}

const DEMO_EVENTS: DemoEvent[] = [
  { type: 'thinking', icon: Brain, color: 'text-violet-400 bg-violet-500/10 border-violet-500/20', label: 'THINKING', content: 'Analyzing query complexity... classifying as PROCEDURAL. Planning: semantic_search + proposition_search.', delay: 0 },
  { type: 'tool_call', icon: Search, color: 'text-blue-400 bg-blue-500/10 border-blue-500/20', label: 'TOOL', content: 'semantic_search({ query: "military leave policy accrual rate", level: "L2", k: 20 })', delay: 800 },
  { type: 'tool_result', icon: FileText, color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20', label: 'RESULT', content: '15 documents retrieved — top score: 0.94 — 45ms', delay: 1400 },
  { type: 'tool_call', icon: Search, color: 'text-blue-400 bg-blue-500/10 border-blue-500/20', label: 'TOOL', content: 'proposition_search({ query: "leave days per month active duty", k: 10 })', delay: 2000 },
  { type: 'tool_result', icon: FileText, color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20', label: 'RESULT', content: '8 propositions matched — top score: 0.97 — 32ms', delay: 2600 },
  { type: 'crag', icon: Shield, color: 'text-amber-400 bg-amber-500/10 border-amber-500/20', label: 'CRAG', content: '12 docs evaluated: 8 CORRECT ✓ · 3 AMBIGUOUS → expanded · 1 REJECTED ✗', delay: 3200 },
  { type: 'rerank', icon: Zap, color: 'text-purple-400 bg-purple-500/10 border-purple-500/20', label: 'RERANK', content: 'ColBERT MaxSim reranking — 8 docs → top 5 selected — 180ms', delay: 3800 },
  { type: 'token', icon: Send, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', label: 'STREAM', content: '', delay: 4400, tokens: 'Active duty members are entitled to 30 days of leave per fiscal year, accruing at a rate of 2.5 days per month of service. [Source 1: AFI 36-3003, §3.1] Members may carry over a maximum of 60 days, with combat zone deployments allowing up to 120 days under special authority. [Source 2: AFI 36-3003, §3.2-3.3]' },
  { type: 'verify', icon: CheckCircle, color: 'text-green-400 bg-green-500/10 border-green-500/20', label: 'VERIFY', content: '3 claims extracted — 3/3 verified against source documents ✓', delay: 6800 },
  { type: 'done', icon: CheckCircle, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', label: 'DONE', content: 'Confidence: 92% — 7.2s total — 2 tool calls — 3 claims verified', delay: 7400 },
]

function TokenStream({ text, isActive }: { text: string; isActive: boolean }) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (!isActive) return
    setDisplayed('')
    setDone(false)
    let i = 0
    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1))
        i++
      } else {
        setDone(true)
        clearInterval(interval)
      }
    }, 18)
    return () => clearInterval(interval)
  }, [text, isActive])

  return (
    <span className="text-zinc-200 leading-relaxed">
      {displayed}
      {!done && isActive && <span className="inline-block w-[2px] h-3.5 bg-emerald-400 ml-0.5 align-middle" style={{ animation: 'typewriter-cursor 0.6s step-end infinite' }} />}
    </span>
  )
}

export function LiveDemo() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [visibleEvents, setVisibleEvents] = useState<number[]>([])
  const [tokenStreamActive, setTokenStreamActive] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const timeoutsRef = useRef<NodeJS.Timeout[]>([])

  const play = () => {
    setIsPlaying(true)
    setVisibleEvents([])
    setTokenStreamActive(false)
    timeoutsRef.current.forEach(clearTimeout)
    timeoutsRef.current = []

    DEMO_EVENTS.forEach((event, i) => {
      const t = setTimeout(() => {
        setVisibleEvents(prev => [...prev, i])
        if (event.type === 'token') setTokenStreamActive(true)
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
      }, event.delay)
      timeoutsRef.current.push(t)
    })

    const endTimeout = setTimeout(() => setIsPlaying(false), 8500)
    timeoutsRef.current.push(endTimeout)
  }

  const reset = () => {
    timeoutsRef.current.forEach(clearTimeout)
    timeoutsRef.current = []
    setIsPlaying(false)
    setVisibleEvents([])
    setTokenStreamActive(false)
  }

  useEffect(() => { return () => timeoutsRef.current.forEach(clearTimeout) }, [])

  return (
    <div className="relative rounded-2xl overflow-hidden" style={{ background: 'var(--forge-surface)', border: '1px solid var(--forge-border)' }}>
      {/* Terminal header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="h-2.5 w-2.5 rounded-full bg-zinc-700" />
            <div className="h-2.5 w-2.5 rounded-full bg-zinc-700" />
            <div className="h-2.5 w-2.5 rounded-full bg-zinc-700" />
          </div>
          <span className="text-[11px] font-mono font-medium text-zinc-500">forge query --mode agentic --stream</span>
        </div>
        <div className="flex items-center gap-2">
          {!isPlaying ? (
            <button onClick={play} className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 text-xs font-medium text-emerald-400 transition-all hover:bg-emerald-500/20">
              <Play className="h-3 w-3" /> Run Demo
            </button>
          ) : (
            <button onClick={reset} className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-500/10 border border-zinc-500/20 px-3 py-1.5 text-xs font-medium text-zinc-400 transition-all hover:bg-zinc-500/20">
              <RotateCcw className="h-3 w-3" /> Reset
            </button>
          )}
        </div>
      </div>

      {/* Query input */}
      <div className="border-b border-white/[0.06] px-5 py-3">
        <div className="flex items-center gap-3">
          <span className="text-emerald-500 font-mono text-sm">❯</span>
          <span className="text-zinc-300 font-mono text-sm">&quot;What is the military leave accrual rate for active duty members?&quot;</span>
        </div>
      </div>

      {/* Event stream */}
      <div ref={scrollRef} className="h-[420px] overflow-y-auto p-5 space-y-3 scroll-smooth" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.08) transparent' }}>
        {visibleEvents.length === 0 && !isPlaying && (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <div className="mb-3 text-zinc-600">
                <Play className="mx-auto h-8 w-8" />
              </div>
              <p className="text-sm text-zinc-500">Click <span className="text-emerald-400 font-medium">Run Demo</span> to see an agentic query in action</p>
            </div>
          </div>
        )}

        <AnimatePresence>
          {visibleEvents.map((eventIdx) => {
            const event = DEMO_EVENTS[eventIdx]
            const Icon = event.icon
            return (
              <motion.div
                key={eventIdx}
                initial={{ opacity: 0, y: 8, height: 0 }}
                animate={{ opacity: 1, y: 0, height: 'auto' }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="flex gap-3"
              >
                {/* Time gutter */}
                <div className="flex-shrink-0 w-12 pt-1 text-right">
                  <span className="text-[10px] font-mono text-zinc-700">{(event.delay / 1000).toFixed(1)}s</span>
                </div>

                {/* Event card */}
                <div className={`flex-1 rounded-xl border px-4 py-3 ${event.color}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className="h-3.5 w-3.5 flex-shrink-0" />
                    <span className="text-[10px] font-bold tracking-wider uppercase opacity-80">{event.label}</span>
                  </div>
                  {event.type === 'token' ? (
                    <div className="text-sm font-mono leading-relaxed">
                      <TokenStream text={event.tokens || ''} isActive={tokenStreamActive} />
                    </div>
                  ) : (
                    <p className="text-sm font-mono opacity-90 leading-relaxed">{event.content}</p>
                  )}
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>

        {isPlaying && visibleEvents.length > 0 && visibleEvents.length < DEMO_EVENTS.length && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2 pl-16">
            <div className="flex gap-1">
              <div className="h-1.5 w-1.5 rounded-full bg-zinc-600 animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="h-1.5 w-1.5 rounded-full bg-zinc-600 animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="h-1.5 w-1.5 rounded-full bg-zinc-600 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}
