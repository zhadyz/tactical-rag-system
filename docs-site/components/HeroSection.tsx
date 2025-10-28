import React from 'react'
import { Sparkles, ArrowRight, Github } from 'lucide-react'

export function HeroSection() {
  return (
    <div className="hero-section -mx-6 -mt-6 relative overflow-hidden px-6 py-24 md:py-32 lg:py-40">
      {/* Animated background effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-950 via-gray-950 to-purple-950 dark:from-gray-950 dark:via-blue-950 dark:to-purple-950" />
      <div className="absolute inset-0 bg-grid-pattern opacity-20" />
      <div className="absolute inset-0 bg-gradient-radial from-transparent via-transparent to-gray-950/50" />

      {/* Gradient fade to next section */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-b from-transparent to-white dark:to-gray-950" />

      {/* Animated GPU particles */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="gpu-particle gpu-particle-1" />
        <div className="gpu-particle gpu-particle-2" />
        <div className="gpu-particle gpu-particle-3" />
        <div className="gpu-particle gpu-particle-4" />
        <div className="gpu-particle gpu-particle-5" />
      </div>

      <div className="relative z-10 mx-auto max-w-4xl text-center">
        {/* Badge */}
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-950/30 px-4 py-2 backdrop-blur-sm animate-fade-in-up">
          <Sparkles className="h-4 w-4 text-blue-400 animate-pulse" />
          <span className="text-sm font-medium text-blue-300">Version 4.2 • Now with 10x faster GPU acceleration</span>
        </div>

        {/* Main heading with gradient text */}
        <h1 className="mb-6 text-6xl font-bold tracking-tight text-white md:text-7xl lg:text-8xl animate-fade-in-up animation-delay-100">
          Apollo <span className="gpu-gradient-text">RAG</span>
        </h1>

        <p className="mb-4 text-2xl font-semibold text-blue-100 md:text-3xl lg:text-4xl animate-fade-in-up animation-delay-200">
          GPU-Accelerated Document Intelligence
        </p>

        <p className="mx-auto mb-10 max-w-3xl text-lg leading-relaxed text-gray-300 md:text-xl animate-fade-in-up animation-delay-300">
          Production-ready RAG system with <span className="font-semibold text-white">CUDA optimization</span>,
          adaptive retrieval strategies, and enterprise-grade deployment.
          Built for <span className="font-semibold text-blue-300">speed</span>,{' '}
          <span className="font-semibold text-purple-300">scale</span>, and{' '}
          <span className="font-semibold text-green-300">precision</span>.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-wrap justify-center gap-4 animate-fade-in-up animation-delay-400">
          <a
            href="/interactive-demos"
            className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 px-8 py-4 font-semibold text-white shadow-lg shadow-blue-500/25 transition-all hover:scale-105 hover:shadow-xl hover:shadow-blue-500/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-950"
          >
            View Demo
            <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
          </a>

          <a
            href="/api-reference"
            className="group inline-flex items-center gap-2 rounded-xl border-2 border-gray-700 bg-gray-900/50 px-8 py-4 font-semibold text-white backdrop-blur-sm transition-all hover:border-gray-600 hover:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-950"
          >
            API Reference
            <ArrowRight className="h-5 w-5 opacity-0 transition-all group-hover:opacity-100 group-hover:translate-x-1" />
          </a>

          <a
            href="https://github.com/zhadyz/tactical-rag-system"
            target="_blank"
            rel="noopener noreferrer"
            className="group inline-flex items-center gap-2 rounded-xl border-2 border-gray-700 bg-gray-900/50 px-8 py-4 font-semibold text-white backdrop-blur-sm transition-all hover:border-gray-600 hover:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-950"
          >
            <Github className="h-5 w-5" />
            GitHub
          </a>
        </div>

        {/* Quick stats */}
        <div className="mt-16 grid grid-cols-1 gap-6 border-t border-gray-800 pt-12 animate-fade-in-up animation-delay-500 sm:grid-cols-3 sm:gap-8">
          <div className="text-center">
            <div className="mb-2 text-4xl font-bold text-white">127<span className="text-xl text-gray-400">ms</span></div>
            <div className="text-sm text-gray-400">P95 Latency</div>
          </div>
          <div className="text-center">
            <div className="mb-2 text-4xl font-bold text-white">450<span className="text-xl text-gray-400">q/s</span></div>
            <div className="text-sm text-gray-400">Throughput</div>
          </div>
          <div className="text-center">
            <div className="mb-2 text-4xl font-bold text-white">94.2<span className="text-xl text-gray-400">%</span></div>
            <div className="text-sm text-gray-400">Accuracy</div>
          </div>
        </div>
      </div>
    </div>
  )
}
