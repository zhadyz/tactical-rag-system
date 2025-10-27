import React from 'react'
import { DocsThemeConfig } from 'nextra-theme-docs'
import { useRouter } from 'next/router'
import { useConfig } from 'nextra-theme-docs'
import { Zap, Github, Twitter } from 'lucide-react'

const config: DocsThemeConfig = {
  logo: (
    <div className="flex items-center gap-2 font-bold">
      <Zap className="h-6 w-6 text-blue-600" />
      <span className="text-xl">Apollo RAG</span>
      <span className="ml-2 rounded-md bg-blue-600 px-2 py-0.5 text-xs font-semibold text-white">
        GPU
      </span>
    </div>
  ),
  project: {
    link: 'https://github.com/yourusername/apollo-rag'
  },
  chat: {
    link: 'https://discord.gg/apollo-rag' // Update with your Discord
  },
  docsRepositoryBase: 'https://github.com/yourusername/apollo-rag/tree/main/docs-site',
  footer: {
    text: (
      <div className="flex w-full flex-col items-center sm:items-start">
        <div className="mb-2 flex items-center gap-2">
          <Zap className="h-5 w-5 text-blue-600" />
          <span className="font-semibold">Apollo RAG</span>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          GPU-Accelerated Document Intelligence © {new Date().getFullYear()}
        </p>
        <p className="mt-1 text-xs text-gray-500">
          Built with Next.js + Nextra • Powered by CUDA
        </p>
      </div>
    )
  },
  head: () => {
    const { asPath, defaultLocale, locale } = useRouter()
    const { frontMatter } = useConfig()
    const url =
      'https://apollo.onyxlab.ai' +
      (defaultLocale === locale ? asPath : `/${locale}${asPath}`)

    return (
      <>
        <meta property="og:url" content={url} />
        <meta property="og:title" content={frontMatter.title || 'Apollo RAG'} />
        <meta
          property="og:description"
          content={frontMatter.description || 'GPU-Accelerated Document Intelligence Platform'}
        />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="theme-color" content="#2563eb" />
        <link rel="icon" href="/favicon.ico" />
      </>
    )
  },
  primaryHue: 215, // Blue
  primarySaturation: 85,
  // Search configuration
  search: {
    placeholder: 'Search documentation...',
    emptyResult: (
      <div className="text-center text-sm text-gray-600">
        No results found. Try different keywords.
      </div>
    ),
    loading: 'Loading...'
  },
  // Navigation
  navbar: {
    extraContent: () => {
      return (
        <div className="flex items-center gap-3">
          <a
            href="https://github.com/yourusername/apollo-rag"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 transition-colors hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            aria-label="GitHub"
          >
            <Github className="h-5 w-5" />
          </a>
        </div>
      )
    }
  },
  sidebar: {
    titleComponent({ title, type }) {
      if (type === 'separator') {
        return <div className="font-bold text-gray-900 dark:text-gray-100">{title}</div>
      }
      return <>{title}</>
    },
    defaultMenuCollapseLevel: 1,
    toggleButton: true
  },
  toc: {
    backToTop: true,
    title: 'On This Page',
    extraContent: () => {
      return (
        <div className="mt-8 border-t border-gray-200 pt-4 text-xs text-gray-600 dark:border-gray-800 dark:text-gray-400">
          <a
            href="https://github.com/yourusername/apollo-rag/issues/new"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-blue-600 dark:hover:text-blue-400"
          >
            Report an issue with this page →
          </a>
        </div>
      )
    }
  },
  editLink: {
    text: 'Edit this page on GitHub →'
  },
  feedback: {
    content: 'Question? Give us feedback →',
    labels: 'feedback'
  },
  // Theming
  darkMode: true,
  nextThemes: {
    defaultTheme: 'dark',
    storageKey: 'apollo-theme'
  },
  // Banner
  banner: {
    key: 'v4.1-release',
    text: (
      <a href="/blog/v4.1-release" target="_blank">
        🚀 Apollo v4.1 is out! GPU acceleration now 10x faster. Read more →
      </a>
    )
  },
  // Git timestamp
  gitTimestamp: ({ timestamp }) => (
    <div className="text-xs text-gray-600 dark:text-gray-400">
      Last updated: {timestamp.toLocaleDateString()}
    </div>
  ),
  // Favicon
  faviconGlyph: '⚡'
}

export default config
