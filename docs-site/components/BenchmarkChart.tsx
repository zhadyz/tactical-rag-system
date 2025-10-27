'use client'

import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

interface BenchmarkData {
  name: string
  latency: number
  throughput: number
  accuracy: number
  gpu: number
}

const data: BenchmarkData[] = [
  {
    name: 'Apollo',
    latency: 127,
    throughput: 450,
    accuracy: 94.2,
    gpu: 88
  },
  {
    name: 'LangChain',
    latency: 892,
    throughput: 67,
    accuracy: 89.1,
    gpu: 23
  },
  {
    name: 'LlamaIndex',
    latency: 654,
    throughput: 102,
    accuracy: 91.3,
    gpu: 41
  },
  {
    name: 'Haystack',
    latency: 543,
    throughput: 134,
    accuracy: 90.7,
    gpu: 35
  }
]

export function LatencyChart() {
  return (
    <div className="my-8">
      <h3 className="mb-4 text-lg font-semibold">Query Latency (P95) - Lower is Better</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="latency" fill="#2563eb" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function ThroughputChart() {
  return (
    <div className="my-8">
      <h3 className="mb-4 text-lg font-semibold">Throughput (q/s) - Higher is Better</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis label={{ value: 'Queries/sec', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="throughput" fill="#10b981" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function AccuracyChart() {
  return (
    <div className="my-8">
      <h3 className="mb-4 text-lg font-semibold">Context Accuracy - Higher is Better</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis
            domain={[85, 95]}
            label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip />
          <Legend />
          <Bar dataKey="accuracy" fill="#f59e0b" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function GpuUtilizationChart() {
  return (
    <div className="my-8">
      <h3 className="mb-4 text-lg font-semibold">GPU Utilization - Higher is Better</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis label={{ value: 'GPU Usage (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="gpu" fill="#8b5cf6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
