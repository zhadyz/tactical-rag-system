'use client'

import React, { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface PipelineStep {
  id: string
  label: string
  sublabel: string
  color: string
  activeBg: string
  activeText: string
  isLoop?: boolean
}

const steps: PipelineStep[] = [
  {
    id: 'query',
    label: 'Query',
    sublabel: 'User input',
    color: 'border-gray-300 dark:border-gray-700',
    activeBg: 'bg-gray-100 dark:bg-gray-800',
    activeText: 'text-gray-900 dark:text-gray-100',
  },
  {
    id: 'analyze',
    label: 'Analyze',
    sublabel: 'Classify intent',
    color: 'border-blue-300 dark:border-blue-700',
    activeBg: 'bg-blue-50 dark:bg-blue-950/40',
    activeText: 'text-blue-800 dark:text-blue-200',
  },
  {
    id: 'agent-loop',
    label: 'Agent Loop',
    sublabel: 'Max 3 iterations',
    color: 'border-indigo-400 dark:border-indigo-600',
    activeBg: 'bg-indigo-50 dark:bg-indigo-950/40',
    activeText: 'text-indigo-800 dark:text-indigo-200',
    isLoop: true,
  },
  {
    id: 'rerank',
    label: 'Rerank',
    sublabel: 'ColBERT scoring',
    color: 'border-purple-300 dark:border-purple-700',
    activeBg: 'bg-purple-50 dark:bg-purple-950/40',
    activeText: 'text-purple-800 dark:text-purple-200',
  },
  {
    id: 'generate',
    label: 'Generate',
    sublabel: 'Stream tokens',
    color: 'border-emerald-300 dark:border-emerald-700',
    activeBg: 'bg-emerald-50 dark:bg-emerald-950/40',
    activeText: 'text-emerald-800 dark:text-emerald-200',
  },
  {
    id: 'verify',
    label: 'Verify',
    sublabel: 'Check claims',
    color: 'border-amber-300 dark:border-amber-700',
    activeBg: 'bg-amber-50 dark:bg-amber-950/40',
    activeText: 'text-amber-800 dark:text-amber-200',
  },
  {
    id: 'stream',
    label: 'Stream',
    sublabel: 'SSE response',
    color: 'border-green-300 dark:border-green-700',
    activeBg: 'bg-green-50 dark:bg-green-950/40',
    activeText: 'text-green-800 dark:text-green-200',
  },
]

const loopSteps = [
  { label: 'Think', desc: 'Plan next action' },
  { label: 'Tool Call', desc: 'Execute search' },
  { label: 'Observe', desc: 'Parse results' },
  { label: 'CRAG Gate', desc: 'Quality check' },
]

export function PipelineDiagram() {
  const [activeStep, setActiveStep] = useState<number>(-1)
  const [isAnimating, setIsAnimating] = useState(false)
  const [loopIteration, setLoopIteration] = useState(0)

  const runAnimation = () => {
    setIsAnimating(true)
    setActiveStep(0)
    setLoopIteration(0)

    let step = 0
    const interval = setInterval(() => {
      step++
      if (step === 2) {
        // We're at agent loop, cycle through iterations
        let iter = 0
        const loopInterval = setInterval(() => {
          setLoopIteration(iter + 1)
          iter++
          if (iter >= 3) {
            clearInterval(loopInterval)
            // Continue to next steps
            const continueInterval = setInterval(() => {
              step++
              if (step >= steps.length) {
                clearInterval(continueInterval)
                setTimeout(() => {
                  setIsAnimating(false)
                  setActiveStep(-1)
                  setLoopIteration(0)
                }, 1500)
              } else {
                setActiveStep(step)
              }
            }, 600)
          }
        }, 800)
      } else if (step < 2) {
        setActiveStep(step)
      }
    }, 600)
  }

  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <div className="mb-8 text-center">
        <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
          Agentic Query Pipeline
        </h2>
        <p className="mx-auto max-w-2xl text-gray-600 dark:text-gray-400">
          Every query flows through an intelligent pipeline with iterative agent reasoning.
        </p>
      </div>

      {/* Animate button */}
      <div className="mb-8 text-center">
        <button
          onClick={runAnimation}
          disabled={isAnimating}
          className={cn(
            'rounded-lg px-5 py-2 text-sm font-medium transition-all',
            isAnimating
              ? 'cursor-not-allowed bg-gray-200 text-gray-500 dark:bg-gray-800 dark:text-gray-500'
              : 'bg-indigo-600 text-white hover:bg-indigo-700 active:scale-95'
          )}
        >
          {isAnimating ? 'Running...' : 'Animate Pipeline'}
        </button>
      </div>

      {/* Pipeline flow */}
      <div className="mx-auto max-w-4xl">
        {/* Main horizontal flow */}
        <div className="flex flex-wrap items-start justify-center gap-2">
          {steps.map((step, idx) => (
            <React.Fragment key={step.id}>
              {/* Step box */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'relative rounded-xl border-2 px-4 py-3 text-center transition-all duration-300 min-w-[90px]',
                    step.color,
                    activeStep === idx
                      ? cn(step.activeBg, step.activeText, 'scale-110 shadow-lg border-opacity-100')
                      : 'bg-white dark:bg-gray-900',
                    activeStep === idx && 'ring-2 ring-offset-2 ring-offset-white dark:ring-offset-gray-950',
                    activeStep === idx && step.id === 'agent-loop' && 'ring-indigo-400',
                    activeStep === idx && step.id === 'query' && 'ring-gray-400',
                    activeStep === idx && step.id === 'analyze' && 'ring-blue-400',
                    activeStep === idx && step.id === 'rerank' && 'ring-purple-400',
                    activeStep === idx && step.id === 'generate' && 'ring-emerald-400',
                    activeStep === idx && step.id === 'verify' && 'ring-amber-400',
                    activeStep === idx && step.id === 'stream' && 'ring-green-400'
                  )}
                >
                  {/* Step number */}
                  <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                    {idx + 1}
                  </div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">
                    {step.label}
                  </div>
                  <div className="mt-0.5 text-[10px] text-gray-500 dark:text-gray-400">
                    {step.sublabel}
                  </div>

                  {/* Loop indicator for agent loop */}
                  {step.isLoop && (
                    <div className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500 text-[9px] font-bold text-white">
                      {'\u27F2'}
                    </div>
                  )}
                </div>

                {/* Agent loop expansion */}
                {step.isLoop && (
                  <div className="mt-3 w-full min-w-[200px] sm:min-w-[280px]">
                    <div className="rounded-lg border border-indigo-200 bg-indigo-50/50 p-3 dark:border-indigo-800 dark:bg-indigo-950/30">
                      <div className="mb-2 text-center text-[10px] font-bold uppercase tracking-wider text-indigo-500 dark:text-indigo-400">
                        Agent Loop (max 3 iterations)
                      </div>
                      <div className="flex flex-wrap items-center justify-center gap-1.5">
                        {loopSteps.map((ls, li) => (
                          <React.Fragment key={ls.label}>
                            <div
                              className={cn(
                                'rounded-md border px-2 py-1 text-center transition-all duration-200',
                                loopIteration > 0 && activeStep === 2
                                  ? 'border-indigo-300 bg-indigo-100 text-indigo-800 dark:border-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-200'
                                  : 'border-indigo-200 bg-white text-indigo-600 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-400'
                              )}
                            >
                              <div className="text-[11px] font-semibold">{ls.label}</div>
                              <div className="text-[9px] opacity-70">{ls.desc}</div>
                            </div>
                            {li < loopSteps.length - 1 && (
                              <span className="text-xs text-indigo-400">{'\u2192'}</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                      {/* Iteration indicators */}
                      <div className="mt-2 flex justify-center gap-1.5">
                        {[1, 2, 3].map((i) => (
                          <div
                            key={i}
                            className={cn(
                              'h-1.5 w-8 rounded-full transition-all duration-300',
                              loopIteration >= i
                                ? 'bg-indigo-500'
                                : 'bg-indigo-200 dark:bg-indigo-800'
                            )}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Arrow between steps */}
              {idx < steps.length - 1 && !step.isLoop && (
                <div className="mt-5 hidden items-center sm:flex">
                  <svg width="20" height="12" viewBox="0 0 20 12" fill="none" className="text-gray-300 dark:text-gray-700">
                    <path d="M0 6H16M16 6L11 1M16 6L11 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </section>
  )
}
