'use client'

import React from 'react'
import * as TabsPrimitive from '@radix-ui/react-tabs'
import { cn } from '@/lib/utils'

interface TabsProps {
  items: string[]
  children: React.ReactNode
  defaultValue?: string
}

export function Tabs({ items, children, defaultValue }: TabsProps) {
  return (
    <TabsPrimitive.Root
      defaultValue={defaultValue || items[0]}
      className="my-6 rounded-lg border border-gray-200 dark:border-gray-800"
    >
      <TabsPrimitive.List className="flex border-b border-gray-200 dark:border-gray-800">
        {items.map(item => (
          <TabsPrimitive.Trigger
            key={item}
            value={item}
            className={cn(
              'flex-1 border-b-2 border-transparent px-4 py-3 text-sm font-medium transition-colors',
              'hover:text-blue-600 dark:hover:text-blue-400',
              'data-[state=active]:border-blue-600 data-[state=active]:text-blue-600',
              'dark:data-[state=active]:border-blue-400 dark:data-[state=active]:text-blue-400'
            )}
          >
            {item}
          </TabsPrimitive.Trigger>
        ))}
      </TabsPrimitive.List>
      {children}
    </TabsPrimitive.Root>
  )
}

interface TabsPanelProps {
  value: string
  children: React.ReactNode
}

export function TabsPanel({ value, children }: TabsPanelProps) {
  return (
    <TabsPrimitive.Content value={value} className="p-4">
      {children}
    </TabsPrimitive.Content>
  )
}
