'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, useScroll, useTransform } from 'motion/react'
import { ArrowRight, Github } from 'lucide-react'

const ROTATING_WORDS = [
  'Agentic retrieval.',
  'Self-verifying answers.',
  'CRAG quality gates.',
  'ColBERT reranking.',
  '14 techniques.',
  '16GB VRAM.',
]

const STATS = [
  { value: '14', label: 'RAG Techniques', color: 'text-blue-400' },
  { value: '<10s', label: 'Agentic Queries', color: 'text-violet-400' },
  { value: '<2s', label: 'Cached Response', color: 'text-emerald-400' },
  { value: '10/10', label: 'Tests Passing', color: 'text-amber-400' },
]

function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationId: number
    let particles: { x: number; y: number; vx: number; vy: number; size: number; opacity: number; hue: number }[] = []

    const resize = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio
      canvas.height = canvas.offsetHeight * window.devicePixelRatio
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
    }

    const init = () => {
      resize()
      const count = Math.min(80, Math.floor((canvas.offsetWidth * canvas.offsetHeight) / 12000))
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * canvas.offsetWidth,
        y: Math.random() * canvas.offsetHeight,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        size: Math.random() * 1.5 + 0.5,
        opacity: Math.random() * 0.3 + 0.1,
        hue: Math.random() > 0.5 ? 220 : 260,
      }))
    }

    const draw = () => {
      const w = canvas.offsetWidth
      const h = canvas.offsetHeight
      ctx.clearRect(0, 0, w, h)

      particles.forEach((p) => {
        p.x += p.vx
        p.y += p.vy
        if (p.x < 0 || p.x > w) p.vx *= -1
        if (p.y < 0 || p.y > h) p.vy *= -1

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = `hsla(${p.hue}, 70%, 65%, ${p.opacity})`
        ctx.fill()
      })

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(99, 102, 241, ${0.06 * (1 - dist / 120)})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }

      animationId = requestAnimationFrame(draw)
    }

    init()
    draw()
    window.addEventListener('resize', init)
    return () => { cancelAnimationFrame(animationId); window.removeEventListener('resize', init) }
  }, [])

  return <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" style={{ opacity: 0.6 }} />
}

function RotatingText() {
  const [index, setIndex] = useState(0)
  const [displayed, setDisplayed] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    const word = ROTATING_WORDS[index]
    let timeout: NodeJS.Timeout

    if (!isDeleting && displayed.length < word.length) {
      timeout = setTimeout(() => setDisplayed(word.slice(0, displayed.length + 1)), 60)
    } else if (!isDeleting && displayed.length === word.length) {
      timeout = setTimeout(() => setIsDeleting(true), 2000)
    } else if (isDeleting && displayed.length > 0) {
      timeout = setTimeout(() => setDisplayed(displayed.slice(0, -1)), 30)
    } else if (isDeleting && displayed.length === 0) {
      setIsDeleting(false)
      setIndex((i) => (i + 1) % ROTATING_WORDS.length)
    }

    return () => clearTimeout(timeout)
  }, [displayed, isDeleting, index])

  return (
    <span className="inline-block min-w-[280px] text-left">
      <span className="text-gradient-blue">{displayed}</span>
      <span className="ml-0.5 inline-block w-[2px] h-[1em] bg-blue-400 align-middle"
        style={{ animation: 'typewriter-cursor 0.8s step-end infinite' }} />
    </span>
  )
}

export function HeroSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: containerRef, offset: ['start start', 'end start'] })
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  const y = useTransform(scrollYProgress, [0, 0.5], [0, -60])

  return (
    <section ref={containerRef} className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden" style={{ background: 'var(--forge-bg)' }}>
      <ParticleField />

      {/* Radial glows */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute top-[-20%] left-1/2 h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-gradient-radial from-blue-600/[0.07] via-indigo-600/[0.03] to-transparent blur-3xl" />
        <div className="absolute bottom-[-10%] right-[-10%] h-[400px] w-[600px] rounded-full bg-gradient-radial from-violet-600/[0.05] to-transparent blur-3xl" />
      </div>

      <div className="pointer-events-none absolute inset-0 bg-dot-grid opacity-40" />

      <motion.div style={{ opacity, y }} className="relative z-10 mx-auto max-w-5xl px-6 text-center">
        {/* Version badge */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}
          className="mb-8 inline-flex items-center gap-2.5 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-2 backdrop-blur-sm">
          <span className="flex h-2 w-2 items-center justify-center relative">
            <span className="absolute h-2 w-2 animate-ping rounded-full bg-emerald-400/60" />
            <span className="relative h-1.5 w-1.5 rounded-full bg-emerald-400" />
          </span>
          <span className="text-xs font-medium text-zinc-400">V5.0 — Agentic RAG Engine</span>
        </motion.div>

        {/* Title — Instrument Serif for drama */}
        <motion.h1 initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="mb-6 font-display text-display-xl font-normal italic tracking-tight">
          <span className="text-gradient-forge">Forge</span>
        </motion.h1>

        {/* Tagline */}
        <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.35 }}
          className="mb-4 text-xl font-medium text-zinc-300 sm:text-2xl">
          The most advanced RAG system you can run<br className="hidden sm:block" /> on a single GPU.
        </motion.p>

        {/* Rotating subtitle */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.5 }}
          className="mb-12 h-8 text-lg text-zinc-500">
          <RotatingText />
        </motion.div>

        {/* CTAs */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.6 }}
          className="flex flex-wrap items-center justify-center gap-4">
          <a href="/getting-started/quick-start"
            className="group relative inline-flex items-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-7 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition-all duration-300 hover:shadow-xl hover:shadow-blue-600/30 active:scale-[0.98]">
            <span className="relative z-10 flex items-center gap-2">
              Get Started
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-indigo-500 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
          </a>
          <a href="https://github.com/zhadyz/tactical-rag-system" target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.02] px-7 py-3.5 text-sm font-semibold text-zinc-300 backdrop-blur-sm transition-all duration-300 hover:border-white/[0.15] hover:bg-white/[0.05] active:scale-[0.98]">
            <Github className="h-4 w-4" />
            View Source
          </a>
        </motion.div>
      </motion.div>

      {/* Stats bar */}
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.8 }}
        className="absolute bottom-12 left-0 right-0 z-10">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-8 px-6 sm:gap-12">
          {STATS.map((stat, i) => (
            <div key={i} className="text-center">
              <div className={`text-2xl font-bold tracking-tight ${stat.color} sm:text-3xl`}>{stat.value}</div>
              <div className="mt-1 text-[11px] font-medium uppercase tracking-widest text-zinc-600">{stat.label}</div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Scroll indicator */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }}
        className="absolute bottom-4 left-1/2 z-10 -translate-x-1/2">
        <motion.div animate={{ y: [0, 6, 0] }} transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          className="h-6 w-4 rounded-full border border-zinc-700 p-0.5">
          <div className="mx-auto h-1.5 w-1 rounded-full bg-zinc-600" />
        </motion.div>
      </motion.div>
    </section>
  )
}
