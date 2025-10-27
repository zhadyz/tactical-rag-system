'use client'

import React, { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { cn } from '@/lib/utils'
import { copyToClipboard } from '@/lib/utils'

interface CodeBlockProps {
  children: string
  language?: string
  filename?: string
  showLineNumbers?: boolean
  highlightLines?: number[]
}

export function CodeBlock({
  children,
  language = 'typescript',
  filename,
  showLineNumbers = false,
  highlightLines = []
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const success = await copyToClipboard(children)
    if (success) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const lines = children.split('\n')

  return (
    <div className="group relative my-6">
      {filename && (
        <div className="rounded-t-lg border border-b-0 border-gray-200 bg-gray-50 px-4 py-2 font-mono text-sm text-gray-700 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300">
          {filename}
        </div>
      )}
      <div className="relative overflow-hidden rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950">
        <button
          onClick={handleCopy}
          className="absolute right-2 top-2 rounded-md bg-gray-200 p-2 opacity-0 transition-opacity hover:bg-gray-300 group-hover:opacity-100 dark:bg-gray-800 dark:hover:bg-gray-700"
          aria-label="Copy code"
        >
          {copied ? (
            <Check className="h-4 w-4 text-green-600" />
          ) : (
            <Copy className="h-4 w-4 text-gray-600 dark:text-gray-400" />
          )}
        </button>
        <pre className="overflow-x-auto p-4">
          <code className="font-mono text-sm">
            {lines.map((line, i) => (
              <div
                key={i}
                className={cn(
                  'leading-relaxed',
                  highlightLines.includes(i + 1) && 'bg-blue-100 dark:bg-blue-950/50'
                )}
              >
                {showLineNumbers && (
                  <span className="mr-4 inline-block w-8 select-none text-right text-gray-500">
                    {i + 1}
                  </span>
                )}
                {line}
              </div>
            ))}
          </code>
        </pre>
      </div>
      {language && (
        <div className="absolute right-14 top-2 rounded-md bg-gray-700 px-2 py-1 text-xs font-semibold text-white opacity-0 transition-opacity group-hover:opacity-100">
          {language}
        </div>
      )}
    </div>
  )
}
