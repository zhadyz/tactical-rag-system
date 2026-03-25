'use client'

import React, { useState } from 'react'
import { cn } from '@/lib/utils'

interface MemoryItem {
  label: string
  size: string
  sizeGB: number
  color: string
  bgColor: string
  textColor: string
}

const gpuItems: MemoryItem[] = [
  {
    label: 'LLM (Qwen 3 14B Q4_K_M)',
    size: '10-12 GB',
    sizeGB: 11,
    color: 'bg-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-950/30',
    textColor: 'text-blue-700 dark:text-blue-300',
  },
  {
    label: 'KV Cache',
    size: '2-4 GB',
    sizeGB: 3,
    color: 'bg-indigo-500',
    bgColor: 'bg-indigo-50 dark:bg-indigo-950/30',
    textColor: 'text-indigo-700 dark:text-indigo-300',
  },
]

const cpuItems: MemoryItem[] = [
  {
    label: 'BGE-M3 Embeddings',
    size: '2.3 GB',
    sizeGB: 2.3,
    color: 'bg-emerald-500',
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/30',
    textColor: 'text-emerald-700 dark:text-emerald-300',
  },
  {
    label: 'ColBERT Reranker',
    size: '1 GB',
    sizeGB: 1,
    color: 'bg-purple-500',
    bgColor: 'bg-purple-50 dark:bg-purple-950/30',
    textColor: 'text-purple-700 dark:text-purple-300',
  },
  {
    label: 'Cross-Encoder',
    size: '400 MB',
    sizeGB: 0.4,
    color: 'bg-amber-500',
    bgColor: 'bg-amber-50 dark:bg-amber-950/30',
    textColor: 'text-amber-700 dark:text-amber-300',
  },
  {
    label: 'Qdrant Vector DB',
    size: 'Variable',
    sizeGB: 2,
    color: 'bg-cyan-500',
    bgColor: 'bg-cyan-50 dark:bg-cyan-950/30',
    textColor: 'text-cyan-700 dark:text-cyan-300',
  },
  {
    label: 'Redis Cache',
    size: '500 MB',
    sizeGB: 0.5,
    color: 'bg-red-500',
    bgColor: 'bg-red-50 dark:bg-red-950/30',
    textColor: 'text-red-700 dark:text-red-300',
  },
]

const GPU_TOTAL = 16
const CPU_TOTAL_DISPLAY = 8 // display scale for CPU bar

function BarSegment({
  item,
  total,
  isHovered,
  onHover,
  onLeave,
}: {
  item: MemoryItem
  total: number
  isHovered: boolean
  onHover: () => void
  onLeave: () => void
}) {
  const widthPercent = (item.sizeGB / total) * 100
  return (
    <div
      className={cn(
        'relative h-10 cursor-pointer transition-all duration-300 first:rounded-l-lg last:rounded-r-lg sm:h-12',
        item.color,
        isHovered ? 'opacity-100 scale-y-110 z-10' : 'opacity-85 hover:opacity-100'
      )}
      style={{ width: `${widthPercent}%`, minWidth: widthPercent > 5 ? undefined : '20px' }}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
    >
      {/* Label inside the bar if wide enough */}
      {widthPercent > 15 && (
        <div className="absolute inset-0 flex items-center justify-center px-1 text-[10px] font-semibold text-white sm:text-xs">
          {item.size}
        </div>
      )}
    </div>
  )
}

export function VRAMBudget() {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null)

  const gpuUsed = gpuItems.reduce((acc, item) => acc + item.sizeGB, 0)
  const gpuFree = GPU_TOTAL - gpuUsed

  return (
    <section className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
      <div className="mb-10 text-center">
        <h2 className="mb-3 text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
          Memory Budget
        </h2>
        <p className="mx-auto max-w-2xl text-gray-600 dark:text-gray-400">
          Forge runs the full 14-technique pipeline on a single 16GB GPU. Here is how memory is allocated.
        </p>
      </div>

      <div className="space-y-10">
        {/* GPU Section */}
        <div>
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-md bg-blue-100 px-2.5 py-1 text-xs font-bold text-blue-800 dark:bg-blue-950/50 dark:text-blue-300">
                GPU VRAM
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">16 GB Total</span>
            </div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {gpuUsed} GB used / {gpuFree} GB free
            </span>
          </div>

          {/* GPU Bar */}
          <div className="flex overflow-hidden rounded-lg bg-gray-200 dark:bg-gray-800">
            {gpuItems.map((item) => (
              <BarSegment
                key={item.label}
                item={item}
                total={GPU_TOTAL}
                isHovered={hoveredItem === item.label}
                onHover={() => setHoveredItem(item.label)}
                onLeave={() => setHoveredItem(null)}
              />
            ))}
            {/* Free space */}
            <div
              className="flex h-10 items-center justify-center rounded-r-lg bg-gray-300/50 text-[10px] font-medium text-gray-500 dark:bg-gray-700/50 dark:text-gray-400 sm:h-12 sm:text-xs"
              style={{ width: `${(gpuFree / GPU_TOTAL) * 100}%` }}
            >
              Free
            </div>
          </div>

          {/* GPU Legend */}
          <div className="mt-3 flex flex-wrap gap-4">
            {gpuItems.map((item) => (
              <div
                key={item.label}
                className={cn(
                  'flex items-center gap-2 rounded-lg px-3 py-1.5 transition-all',
                  hoveredItem === item.label ? item.bgColor : ''
                )}
                onMouseEnter={() => setHoveredItem(item.label)}
                onMouseLeave={() => setHoveredItem(null)}
              >
                <div className={cn('h-3 w-3 rounded-sm', item.color)} />
                <span className={cn('text-sm font-medium', item.textColor)}>{item.label}</span>
                <span className="text-xs text-gray-500 dark:text-gray-400">{item.size}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200 dark:border-gray-800" />
          </div>
          <div className="relative flex justify-center">
            <span className="bg-white px-4 text-sm font-medium text-gray-500 dark:bg-gray-950 dark:text-gray-400">
              Everything else on CPU / System RAM
            </span>
          </div>
        </div>

        {/* CPU Section */}
        <div>
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-md bg-emerald-100 px-2.5 py-1 text-xs font-bold text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300">
                CPU RAM
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">System memory</span>
            </div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              ~{cpuItems.reduce((a, i) => a + i.sizeGB, 0).toFixed(1)} GB typical
            </span>
          </div>

          {/* CPU Bar */}
          <div className="flex overflow-hidden rounded-lg bg-gray-200 dark:bg-gray-800">
            {cpuItems.map((item) => (
              <BarSegment
                key={item.label}
                item={item}
                total={CPU_TOTAL_DISPLAY}
                isHovered={hoveredItem === item.label}
                onHover={() => setHoveredItem(item.label)}
                onLeave={() => setHoveredItem(null)}
              />
            ))}
          </div>

          {/* CPU Legend */}
          <div className="mt-3 flex flex-wrap gap-4">
            {cpuItems.map((item) => (
              <div
                key={item.label}
                className={cn(
                  'flex items-center gap-2 rounded-lg px-3 py-1.5 transition-all',
                  hoveredItem === item.label ? item.bgColor : ''
                )}
                onMouseEnter={() => setHoveredItem(item.label)}
                onMouseLeave={() => setHoveredItem(null)}
              >
                <div className={cn('h-3 w-3 rounded-sm', item.color)} />
                <span className={cn('text-sm font-medium', item.textColor)}>{item.label}</span>
                <span className="text-xs text-gray-500 dark:text-gray-400">{item.size}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Callout */}
        <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-4 dark:border-blue-800 dark:bg-blue-950/20">
          <div className="flex items-start gap-3">
            <span className="text-lg">{'\u{1F4A1}'}</span>
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <span className="font-semibold">Key insight:</span> By offloading embedding models, rerankers, and databases to CPU, the entire 16GB GPU budget
              is dedicated to the LLM. This enables running a full 14B parameter model with generous KV cache for long-context reasoning.
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
