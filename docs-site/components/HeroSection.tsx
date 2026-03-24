'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Play } from 'lucide-react'

const stats = [
  { label: '14 Techniques', value: '14' },
  { label: '10/10 Tests Pass', value: '10/10' },
  { label: '16GB VRAM', value: '16GB' },
  { label: '<10s Queries', value: '<10s' },
]

export function HeroSection() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <section className="relative min-h-[90vh] flex flex-col items-center justify-center overflow-hidden bg-white dark:bg-gray-950">
      {/* Background grid pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-40 dark:opacity-20" />

      {/* Radial gradient overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(59,130,246,0.08),transparent_70%)] dark:bg-[radial-gradient(ellipse_at_center,rgba(59,130,246,0.15),transparent_70%)]" />

      {/* Floating particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="gpu-particle gpu-particle-1" />
        <div className="gpu-particle gpu-particle-2" />
        <div className="gpu-particle gpu-particle-3" />
        <div className="gpu-particle gpu-particle-4" />
        <div className="gpu-particle gpu-particle-5" />
      </div>

      {/* Glowing orbs for dark mode */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 dark:bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 dark:bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />

      {/* Main content */}
      <div className="relative z-10 mx-auto max-w-5xl px-6 text-center">
        {/* Version badge */}
        <div
          className={`mb-8 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50/80 px-4 py-1.5 text-sm font-medium text-blue-700 backdrop-blur-sm dark:border-blue-800 dark:bg-blue-950/50 dark:text-blue-300 transition-all duration-700 ${
            mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500" />
          </span>
          V5 — 14 cutting-edge RAG techniques
        </div>

        {/* Title */}
        <h1
          className={`mb-6 text-6xl font-extrabold tracking-tight sm:text-7xl md:text-8xl lg:text-9xl transition-all duration-700 delay-100 ${
            mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
          }`}
        >
          <span className="gpu-gradient-text">Forge</span>
        </h1>

        {/* Tagline */}
        <p
          className={`mx-auto mb-4 max-w-3xl text-xl font-medium text-gray-700 dark:text-gray-200 sm:text-2xl md:text-3xl transition-all duration-700 delay-200 ${
            mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
          }`}
        >
          The most advanced RAG system you can run on a single GPU
        </p>

        {/* Subtitle */}
        <p
          className={`mx-auto mb-10 max-w-2xl text-base text-gray-500 dark:text-gray-400 sm:text-lg md:text-xl transition-all duration-700 delay-300 ${
            mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
          }`}
        >
          14 cutting-edge techniques. Agentic retrieval. Self-verifying answers.
        </p>

        {/* CTA Buttons */}
        <div
          className={`mb-16 flex flex-col items-center gap-4 sm:flex-row sm:justify-center transition-all duration-700 delay-[400ms] ${
            mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
          }`}
        >
          <Link
            href="/getting-started/quick-start"
            className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-blue-500/25 transition-all hover:shadow-xl hover:shadow-blue-500/30 hover:scale-[1.02] active:scale-[0.98] dark:shadow-blue-500/20"
          >
            Get Started
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            href="/architecture/overview"
            className="group inline-flex items-center gap-2 rounded-xl border border-gray-300 bg-white/80 px-8 py-3.5 text-base font-semibold text-gray-700 backdrop-blur-sm transition-all hover:border-blue-300 hover:bg-blue-50/50 hover:text-blue-700 active:scale-[0.98] dark:border-gray-700 dark:bg-gray-900/80 dark:text-gray-300 dark:hover:border-blue-700 dark:hover:bg-blue-950/30 dark:hover:text-blue-300"
          >
            <Play className="h-4 w-4" />
            View Architecture
          </Link>
        </div>

        {/* Stats bar */}
        <div
          className={`mx-auto max-w-3xl rounded-2xl border border-gray-200/60 bg-white/70 p-6 backdrop-blur-md dark:border-gray-800/60 dark:bg-gray-900/70 transition-all duration-700 delay-500 ${
            mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
          }`}
        >
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
            {stats.map((stat, i) => (
              <div key={stat.label} className="text-center">
                <div className="text-2xl font-bold text-gray-900 dark:text-white sm:text-3xl">
                  {stat.value}
                </div>
                <div className="mt-1 text-xs font-medium text-gray-500 dark:text-gray-400 sm:text-sm">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white dark:from-gray-950" />
    </section>
  )
}
