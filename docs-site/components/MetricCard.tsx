import React from 'react'
import { cn } from '@/lib/utils'
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  unit?: string
  icon?: LucideIcon
  trend?: number
  description?: string
  className?: string
}

export function MetricCard({
  title,
  value,
  unit,
  icon: Icon,
  trend,
  description,
  className
}: MetricCardProps) {
  const isPositive = trend !== undefined && trend > 0

  return (
    <div
      className={cn(
        'rounded-lg border border-gray-200 bg-gradient-to-br from-white to-gray-50 p-6 dark:border-gray-800 dark:from-gray-900 dark:to-gray-950',
        className
      )}
    >
      <div className="mb-3 flex items-start justify-between">
        <div className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</div>
        {Icon && <Icon className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
      </div>
      <div className="mb-2 flex items-baseline gap-2">
        <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{value}</div>
        {unit && <div className="text-lg text-gray-600 dark:text-gray-400">{unit}</div>}
      </div>
      {trend !== undefined && (
        <div className="flex items-center gap-1 text-sm">
          {isPositive ? (
            <TrendingUp className="h-4 w-4 text-green-600" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-600" />
          )}
          <span className={isPositive ? 'text-green-600' : 'text-red-600'}>
            {Math.abs(trend)}%
          </span>
          <span className="text-gray-600 dark:text-gray-400">vs baseline</span>
        </div>
      )}
      {description && (
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{description}</p>
      )}
    </div>
  )
}
