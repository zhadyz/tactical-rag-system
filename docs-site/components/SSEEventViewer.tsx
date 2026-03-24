'use client'

import React, { useState, useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Play, RotateCcw, ChevronDown, ChevronRight } from 'lucide-react'

interface SSEEvent {
  type: string
  content: string
  timestamp: number
  detail?: Record<string, unknown>
  color: string
}

const sampleEvents: Omit<SSEEvent, 'timestamp'>[] = [
  {
    type: 'agent_thinking',
    content: 'Analyzing query: "What is the leave policy?"',
    detail: { query: 'What is the leave policy?', intent: 'factual_lookup', complexity: 'medium' },
    color: 'text-blue-500 dark:text-blue-400',
  },
  {
    type: 'tool_call',
    content: 'semantic_search({query: "leave policy", k: 20})',
    detail: { tool: 'semantic_search', args: { query: 'leave policy', k: 20 }, iteration: 1 },
    color: 'text-indigo-500 dark:text-indigo-400',
  },
  {
    type: 'tool_result',
    content: '15 results, top score: 0.92 (45ms)',
    detail: { results: 15, top_score: 0.92, latency_ms: 45, collection: 'dense_vectors' },
    color: 'text-cyan-600 dark:text-cyan-400',
  },
  {
    type: 'tool_call',
    content: 'proposition_search({query: "leave accrual rate"})',
    detail: { tool: 'proposition_search', args: { query: 'leave accrual rate' }, iteration: 1 },
    color: 'text-indigo-500 dark:text-indigo-400',
  },
  {
    type: 'tool_result',
    content: '8 results, top score: 0.95 (32ms)',
    detail: { results: 8, top_score: 0.95, latency_ms: 32, collection: 'propositions' },
    color: 'text-cyan-600 dark:text-cyan-400',
  },
  {
    type: 'crag_evaluation',
    content: '12 docs evaluated, 8 correct, 3 ambiguous, 1 rejected',
    detail: { total: 12, correct: 8, ambiguous: 3, rejected: 1, threshold: 0.7 },
    color: 'text-amber-600 dark:text-amber-400',
  },
  {
    type: 'retrieval_complete',
    content: '8 documents approved',
    detail: { approved: 8, avg_score: 0.89, total_tokens: 3420 },
    color: 'text-emerald-600 dark:text-emerald-400',
  },
  {
    type: 'token',
    content: '"Active" "duty" "members" "are" "entitled" "to" "30" "days" "..."',
    detail: { tokens_generated: 142, model: 'qwen3-14b', temperature: 0.1 },
    color: 'text-gray-700 dark:text-gray-300',
  },
  {
    type: 'verification',
    content: '3 claims verified, 3/3 supported',
    detail: { claims: 3, supported: 3, contradicted: 0, unverifiable: 0 },
    color: 'text-green-600 dark:text-green-400',
  },
  {
    type: 'done',
    content: 'Complete. Total: 847ms',
    detail: { total_ms: 847, retrieval_ms: 312, generation_ms: 480, verification_ms: 55 },
    color: 'text-green-500 dark:text-green-400',
  },
]

const typeIcons: Record<string, string> = {
  agent_thinking: '\u{1F9E0}',
  tool_call: '\u{1F527}',
  tool_result: '\u{1F4E6}',
  crag_evaluation: '\u{1F6E1}',
  retrieval_complete: '\u2705',
  token: '\u{1F4DD}',
  verification: '\u{1F50D}',
  done: '\u{1F3C1}',
}

function EventRow({ event, index }: { event: SSEEvent; index: number }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className="animate-fade-in-up border-b border-gray-100 dark:border-gray-800 last:border-0"
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      <button
        onClick={() => event.detail && setExpanded(!expanded)}
        className="flex w-full items-start gap-3 px-4 py-2.5 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
      >
        {/* Expand icon */}
        <div className="mt-0.5 flex-shrink-0 text-gray-400">
          {event.detail ? (
            expanded ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )
          ) : (
            <div className="h-3.5 w-3.5" />
          )}
        </div>

        {/* Type icon */}
        <span className="flex-shrink-0 text-sm">{typeIcons[event.type] || '\u25CF'}</span>

        {/* Event type badge */}
        <span
          className={cn(
            'flex-shrink-0 rounded px-1.5 py-0.5 font-mono text-[11px] font-medium',
            event.color,
            'bg-gray-100 dark:bg-gray-800'
          )}
        >
          {event.type}
        </span>

        {/* Content */}
        <span className="min-w-0 flex-1 truncate font-mono text-xs text-gray-700 dark:text-gray-300">
          {event.content}
        </span>

        {/* Timestamp */}
        <span className="flex-shrink-0 font-mono text-[10px] text-gray-400 dark:text-gray-600">
          +{event.timestamp}ms
        </span>
      </button>

      {/* Expanded detail */}
      {expanded && event.detail && (
        <div className="mx-12 mb-2 rounded-lg bg-gray-50 p-3 dark:bg-gray-800/80">
          <pre className="overflow-x-auto font-mono text-[11px] text-gray-600 dark:text-gray-400">
            {JSON.stringify(event.detail, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export function SSEEventViewer() {
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [isPlaying, setIsPlaying] = useState(false)
  const [isDone, setIsDone] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout[]>([])

  const clearTimeouts = () => {
    timeoutRef.current.forEach(clearTimeout)
    timeoutRef.current = []
  }

  const reset = () => {
    clearTimeouts()
    setEvents([])
    setIsPlaying(false)
    setIsDone(false)
  }

  const play = () => {
    reset()
    setIsPlaying(true)

    let cumulativeTime = 0
    const delays = [0, 200, 350, 550, 700, 900, 1100, 1350, 1600, 1800]

    sampleEvents.forEach((evt, idx) => {
      const delay = delays[idx] || idx * 200
      cumulativeTime += (idx === 0 ? 0 : delays[idx] - delays[idx - 1]) || 200

      const timeout = setTimeout(() => {
        const timestamps = [0, 45, 90, 180, 212, 320, 380, 420, 790, 847]
        setEvents((prev) => [
          ...prev,
          { ...evt, timestamp: timestamps[idx] || cumulativeTime },
        ])

        // Auto-scroll
        if (containerRef.current) {
          containerRef.current.scrollTop = containerRef.current.scrollHeight
        }

        // Mark done on last event
        if (idx === sampleEvents.length - 1) {
          setIsPlaying(false)
          setIsDone(true)
        }
      }, delay)

      timeoutRef.current.push(timeout)
    })
  }

  useEffect(() => {
    return () => clearTimeouts()
  }, [])

  return (
    <section className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
      <div className="mb-8 text-center">
        <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
          Live Event Stream
        </h2>
        <p className="mx-auto max-w-2xl text-gray-600 dark:text-gray-400">
          Watch a real agentic query unfold. Every event is streamed via SSE in real time.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg dark:border-gray-800 dark:bg-gray-900">
        {/* Terminal header */}
        <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-2.5 dark:border-gray-800 dark:bg-gray-950">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="h-3 w-3 rounded-full bg-red-400" />
              <div className="h-3 w-3 rounded-full bg-yellow-400" />
              <div className="h-3 w-3 rounded-full bg-green-400" />
            </div>
            <span className="ml-2 font-mono text-xs text-gray-500 dark:text-gray-400">
              SSE Event Stream
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={play}
              disabled={isPlaying}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium transition-all',
                isPlaying
                  ? 'cursor-not-allowed bg-gray-200 text-gray-500 dark:bg-gray-800 dark:text-gray-500'
                  : 'bg-emerald-500 text-white hover:bg-emerald-600 active:scale-95'
              )}
            >
              <Play className="h-3 w-3" />
              {isPlaying ? 'Streaming...' : 'Play Demo'}
            </button>
            {isDone && (
              <button
                onClick={reset}
                className="flex items-center gap-1 rounded-md bg-gray-200 px-3 py-1 text-xs font-medium text-gray-700 transition-all hover:bg-gray-300 active:scale-95 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                <RotateCcw className="h-3 w-3" />
                Reset
              </button>
            )}
          </div>
        </div>

        {/* Event list */}
        <div
          ref={containerRef}
          className="max-h-[400px] min-h-[200px] overflow-y-auto"
        >
          {events.length === 0 && !isPlaying && (
            <div className="flex h-[200px] items-center justify-center text-sm text-gray-400 dark:text-gray-600">
              Press "Play Demo" to simulate an agentic query
            </div>
          )}
          {events.map((event, idx) => (
            <EventRow key={`${event.type}-${idx}`} event={event} index={idx} />
          ))}
          {isPlaying && (
            <div className="flex items-center gap-2 px-4 py-2">
              <div className="flex gap-1">
                <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-500 [animation-delay:0ms]" />
                <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-500 [animation-delay:150ms]" />
                <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-500 [animation-delay:300ms]" />
              </div>
              <span className="font-mono text-xs text-gray-400">receiving events...</span>
            </div>
          )}
        </div>

        {/* Footer with stats */}
        {isDone && (
          <div className="border-t border-gray-200 bg-gray-50 px-4 py-2 dark:border-gray-800 dark:bg-gray-950">
            <div className="flex flex-wrap gap-4 font-mono text-[11px] text-gray-500 dark:text-gray-400">
              <span>Events: {events.length}</span>
              <span>Retrieval: 312ms</span>
              <span>Generation: 480ms</span>
              <span>Verification: 55ms</span>
              <span className="font-semibold text-emerald-600 dark:text-emerald-400">Total: 847ms</span>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
