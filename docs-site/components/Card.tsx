import React from 'react'
import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface CardProps {
  title: string
  description?: string
  icon?: LucideIcon
  href?: string
  children?: React.ReactNode
  className?: string
  hover?: boolean
}

export function Card({
  title,
  description,
  icon: Icon,
  href,
  children,
  className,
  hover = true
}: CardProps) {
  const Component = href ? 'a' : 'div'

  return (
    <Component
      href={href}
      className={cn(
        'group rounded-lg border border-gray-200 bg-white p-6 transition-all dark:border-gray-800 dark:bg-gray-900',
        hover && 'hover:shadow-lg hover:border-blue-500 dark:hover:border-blue-500',
        href && 'cursor-pointer',
        className
      )}
    >
      {Icon && (
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-950/30 dark:text-blue-400">
          <Icon className="h-6 w-6" />
        </div>
      )}
      <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
      {description && <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>}
      {children}
    </Component>
  )
}

interface FeatureCardProps {
  title: string
  description: string
  icon?: LucideIcon
}

export function FeatureCard({ title, description, icon: Icon }: FeatureCardProps) {
  return (
    <div className="flex gap-4">
      {Icon && (
        <div className="flex-shrink-0">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-950/30 dark:text-blue-400">
            <Icon className="h-5 w-5" />
          </div>
        </div>
      )}
      <div>
        <h3 className="mb-1 font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
      </div>
    </div>
  )
}
