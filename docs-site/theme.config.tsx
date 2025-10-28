import React from 'react'
import { DocsThemeConfig } from 'nextra-theme-docs'
import { useRouter } from 'next/router'
import { useConfig } from 'nextra-theme-docs'
import { Zap, Github, Twitter } from 'lucide-react'
import { CustomNavbar } from './components/CustomNavbar'
import { Callout } from './components/Callout'

const config: DocsThemeConfig = {
  logo: (
    <div className="flex items-center gap-3 font-bold">
      <img src="/apollo-logo.png" alt="Apollo" className="h-16 w-16" />
      <span className="text-xl">Apollo</span>
      <span className="ml-2 rounded-md bg-red-600 px-2 py-0.5 text-xs font-semibold text-white">
        GPU
      </span>
    </div>
  ),
  project: {
    link: 'https://github.com/zhadyz/tactical-rag-system/tree/v4.2-production'
  },
  docsRepositoryBase: 'https://github.com/zhadyz/tactical-rag-system/tree/v4.2-production/docs-site',
  footer: {
    text: null
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
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon.png" />
        <link rel="icon" type="image/x-icon" href="/favicon.ico" />
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
    extraContent: () => <CustomNavbar />
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
            href="https://github.com/zhadyz/tactical-rag-system/issues/new"
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
    key: 'v4.2-release',
    text: (
      <a href="/blog/v4.2-release" target="_blank" className="flex items-center justify-center gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-600 px-2 py-0.5 text-xs font-semibold text-white">
          NEW
        </span>
        <span>Apollo v4.2 is out! GPU acceleration now 10x faster. Read more →</span>
      </a>
    )
  },
  // Git timestamp - disabled
  gitTimestamp: null,
  // Favicon
  faviconGlyph: '⚡',
  // MDX Components
  components: {
    Callout
  }
}

export default config
