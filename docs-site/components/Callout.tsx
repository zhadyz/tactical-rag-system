import React from 'react'
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

type CalloutType = 'info' | 'warning' | 'error' | 'success'

interface CalloutProps {
  type?: CalloutType
  emoji?: string
  children: React.ReactNode
  title?: string
}

const icons: Record<CalloutType, React.ReactNode> = {
  info: <Info className="h-5 w-5" />,
  warning: <AlertTriangle className="h-5 w-5" />,
  error: <AlertCircle className="h-5 w-5" />,
  success: <CheckCircle2 className="h-5 w-5" />
}

const styles: Record<CalloutType, string> = {
  info: 'border-blue-200/50 bg-gradient-to-br from-blue-50 to-blue-100/30 text-blue-900 dark:border-blue-800/30 dark:from-blue-950/30 dark:to-blue-900/20 dark:text-blue-100',
  warning:
    'border-yellow-200/50 bg-gradient-to-br from-yellow-50 to-yellow-100/30 text-yellow-900 dark:border-yellow-800/30 dark:from-yellow-950/30 dark:to-yellow-900/20 dark:text-yellow-100',
  error:
    'border-red-200/50 bg-gradient-to-br from-red-50 to-red-100/30 text-red-900 dark:border-red-800/30 dark:from-red-950/30 dark:to-red-900/20 dark:text-red-100',
  success:
    'border-green-200/50 bg-gradient-to-br from-green-50 to-green-100/30 text-green-900 dark:border-green-800/30 dark:from-green-950/30 dark:to-green-900/20 dark:text-green-100'
}

const iconStyles: Record<CalloutType, string> = {
  info: 'text-blue-600 dark:text-blue-400',
  warning: 'text-yellow-600 dark:text-yellow-400',
  error: 'text-red-600 dark:text-red-400',
  success: 'text-green-600 dark:text-green-400'
}

export function Callout({ type = 'info', emoji, children, title }: CalloutProps) {
  return (
    <div className="mx-auto my-12 max-w-4xl">
      <div className={cn('flex gap-4 rounded-xl border p-6 shadow-sm', styles[type])}>
        <div className="flex-shrink-0">
          <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg', iconStyles[type])}>
            {emoji ? <span className="text-2xl">{emoji}</span> : <div className={iconStyles[type]}>{icons[type]}</div>}
          </div>
        </div>
        <div className="flex-1">
          {title && <div className="mb-2 text-lg font-bold">{title}</div>}
          <div className="leading-relaxed">{children}</div>
        </div>
      </div>
    </div>
  )
}
