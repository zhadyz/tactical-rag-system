'use client'

import React, { useEffect, useRef, useState } from 'react'
import { motion, useAnimation, useInView } from 'motion/react'
import { Zap, Cpu } from 'lucide-react'

interface RaceMetrics {
  gpu: {
    latency: number
    throughput: number
    progress: number
  }
  cpu: {
    latency: number
    throughput: number
    progress: number
  }
}

// Particle system using Canvas API for GPU-accelerated rendering
function ParticleCanvas({ active, color }: { active: boolean; color: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Array<{
    x: number
    y: number
    vx: number
    vy: number
    alpha: number
    size: number
  }>>([])
  const animationFrameRef = useRef<number>()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d', { alpha: true })
    if (!ctx) return

    // Set canvas size
    const updateSize = () => {
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width * window.devicePixelRatio
      canvas.height = rect.height * window.devicePixelRatio
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
    }
    updateSize()

    // Initialize particles - fewer, slower, more faded
    const initParticles = () => {
      particlesRef.current = Array.from({ length: active ? 30 : 8 }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * (active ? 0.8 : 0.3),
        vy: (Math.random() - 0.5) * (active ? 0.8 : 0.3),
        alpha: Math.random() * 0.3 + 0.1,
        size: Math.random() * 2 + 0.5
      }))
    }
    initParticles()

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      particlesRef.current.forEach((particle) => {
        // Update position
        particle.x += particle.vx
        particle.y += particle.vy

        // Bounce off edges
        if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1
        if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1

        // Draw particle with glow effect
        const gradient = ctx.createRadialGradient(
          particle.x, particle.y, 0,
          particle.x, particle.y, particle.size * 3
        )
        gradient.addColorStop(0, `${color}${Math.floor(particle.alpha * 255).toString(16).padStart(2, '0')}`)
        gradient.addColorStop(1, `${color}00`)

        ctx.fillStyle = gradient
        ctx.fillRect(
          particle.x - particle.size * 3,
          particle.y - particle.size * 3,
          particle.size * 6,
          particle.size * 6
        )
      })

      animationFrameRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [active, color])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ width: '100%', height: '100%' }}
    />
  )
}

export function PerformanceRace() {
  const [metrics, setMetrics] = useState<RaceMetrics>({
    gpu: { latency: 0, throughput: 0, progress: 0 },
    cpu: { latency: 0, throughput: 0, progress: 0 }
  })
  const [racing, setRacing] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, amount: 0.3 })
  const controls = useAnimation()

  // Start race animation when in view
  useEffect(() => {
    if (isInView && !racing) {
      setRacing(true)
      simulateRace()
    }
  }, [isInView])

  const simulateRace = () => {
    const startTime = Date.now()
    const gpuDuration = 4000 // GPU finishes in 4 seconds
    const cpuDuration = 12000 // CPU takes 12 seconds (3x slower)

    const animate = () => {
      const elapsed = Date.now() - startTime

      // GPU: Fast, linear acceleration
      const gpuProgress = Math.min(elapsed / gpuDuration, 1)
      const gpuLatency = Math.floor(127 + (1 - gpuProgress) * 50)
      const gpuThroughput = Math.floor(gpuProgress * 450)

      // CPU: Much slower, continues after GPU finishes
      const cpuProgress = Math.min(elapsed / cpuDuration, 1)
      const cpuLatency = Math.floor(650 + cpuProgress * 242)
      const cpuThroughput = Math.floor(cpuProgress * 67)

      setMetrics({
        gpu: { latency: gpuLatency, throughput: gpuThroughput, progress: gpuProgress * 100 },
        cpu: { latency: cpuLatency, throughput: cpuThroughput, progress: cpuProgress * 100 }
      })

      // Continue animating until CPU finishes
      if (cpuProgress < 1) {
        requestAnimationFrame(animate)
      } else {
        // Final values
        setMetrics({
          gpu: { latency: 127, throughput: 450, progress: 100 },
          cpu: { latency: 892, throughput: 67, progress: 100 }
        })
      }
    }

    animate()
  }

  const resetRace = () => {
    setMetrics({
      gpu: { latency: 0, throughput: 0, progress: 0 },
      cpu: { latency: 0, throughput: 0, progress: 0 }
    })
    setRacing(false)
    setTimeout(() => {
      setRacing(true)
      simulateRace()
    }, 100)
  }

  return (
    <div ref={ref} className="mx-auto my-32 max-w-7xl px-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.6 }}
        className="mb-16 text-center"
      >
        <h2 className="mb-4 text-4xl font-bold text-gray-900 dark:text-white md:text-5xl">
          GPU vs CPU: Live Performance Race
        </h2>
        <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Watch Apollo's GPU acceleration process 100,000 documents in real-time
        </p>
      </motion.div>

      {/* Race Container */}
      <div className="relative overflow-hidden rounded-3xl border border-gray-200/50 bg-gradient-to-br from-gray-50 to-gray-100/50 p-8 shadow-2xl dark:border-gray-800/50 dark:from-gray-900 dark:to-gray-800/50 md:p-12">
        {/* GPU Lane */}
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="relative mb-12 overflow-hidden rounded-2xl border-2 border-blue-500/30 bg-blue-50/50 p-8 dark:bg-blue-950/30"
        >
          <ParticleCanvas active={racing && metrics.gpu.progress > 0} color="#3b82f6" />

          <div className="relative z-10 mb-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-blue-600 p-3 shadow-lg shadow-blue-600/50">
                <Zap className="h-8 w-8 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                  GPU Acceleration
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">CUDA-Optimized Pipeline</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {metrics.gpu.latency}ms
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {metrics.gpu.throughput} q/s
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="relative h-12 overflow-hidden rounded-xl bg-white/50 dark:bg-gray-900/50">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 shadow-lg shadow-blue-500/50"
              initial={{ width: '0%' }}
              animate={{ width: `${metrics.gpu.progress}%` }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
            </motion.div>
            <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-900 dark:text-white">
              {Math.floor(metrics.gpu.progress)}%
            </div>
          </div>
        </motion.div>

        {/* VS Divider */}
        <div className="relative my-8 flex items-center justify-center">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t-2 border-gray-300 dark:border-gray-700" />
          </div>
          <div className="relative rounded-full bg-gradient-to-r from-blue-600 to-gray-600 px-8 py-3 text-xl font-bold text-white shadow-lg">
            VS
          </div>
        </div>

        {/* CPU Lane */}
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="relative overflow-hidden rounded-2xl border-2 border-gray-500/30 bg-gray-50/50 p-8 dark:bg-gray-800/30"
        >
          <ParticleCanvas active={racing && metrics.cpu.progress > 0} color="#6b7280" />

          <div className="relative z-10 mb-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-gray-600 p-3 shadow-lg shadow-gray-600/50">
                <Cpu className="h-8 w-8 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                  CPU Processing
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Traditional Framework</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-gray-600 dark:text-gray-400">
                {metrics.cpu.latency}ms
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {metrics.cpu.throughput} q/s
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="relative h-12 overflow-hidden rounded-xl bg-white/50 dark:bg-gray-900/50">
            <motion.div
              className="h-full bg-gradient-to-r from-gray-400 via-gray-500 to-gray-600"
              initial={{ width: '0%' }}
              animate={{ width: `${metrics.cpu.progress}%` }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            />
            <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-900 dark:text-white">
              {Math.floor(metrics.cpu.progress)}%
            </div>
          </div>
        </motion.div>

      </div>

      {/* Stats Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.6, delay: 0.8 }}
        className="mt-12 grid gap-6 md:grid-cols-3"
      >
        <div className="rounded-xl border border-gray-200 bg-white p-6 text-center shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">7x</div>
          <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">Faster Latency</div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-6 text-center shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">6.7x</div>
          <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">Higher Throughput</div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-6 text-center shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="text-3xl font-bold text-green-600 dark:text-green-400">100K</div>
          <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">Documents Processed</div>
        </div>
      </motion.div>
    </div>
  )
}
