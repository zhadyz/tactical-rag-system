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
  info: 'border-blue-500 bg-blue-50 text-blue-900 dark:border-blue-500/50 dark:bg-blue-950/30 dark:text-blue-100',
  warning:
    'border-yellow-500 bg-yellow-50 text-yellow-900 dark:border-yellow-500/50 dark:bg-yellow-950/30 dark:text-yellow-100',
  error:
    'border-red-500 bg-red-50 text-red-900 dark:border-red-500/50 dark:bg-red-950/30 dark:text-red-100',
  success:
    'border-green-500 bg-green-50 text-green-900 dark:border-green-500/50 dark:bg-green-950/30 dark:text-green-100'
}

export function Callout({ type = 'info', emoji, children, title }: CalloutProps) {
  return (
    <div className={cn('my-6 flex gap-3 rounded-lg border p-4', styles[type])}>
      <div className="flex-shrink-0 pt-0.5">
        {emoji ? <span className="text-xl">{emoji}</span> : icons[type]}
      </div>
      <div className="flex-1">
        {title && <div className="mb-1 font-semibold">{title}</div>}
        <div className="prose prose-sm dark:prose-invert">{children}</div>
      </div>
    </div>
  )
}
