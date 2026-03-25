import React from 'react'
import { DocsThemeConfig } from 'nextra-theme-docs'
import { useRouter } from 'next/router'
import { useConfig } from 'nextra-theme-docs'
import { Callout } from './components/Callout'

const config: DocsThemeConfig = {
  logo: (
    <div className="flex items-center gap-2 font-extrabold text-xl">
      <span className="bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-600 bg-clip-text text-transparent">
        Forge
      </span>
      <span className="rounded-md bg-gradient-to-r from-blue-600 to-indigo-600 px-1.5 py-0.5 text-[10px] font-bold leading-none text-white">
        V5
      </span>
    </div>
  ),
  project: {
    link: 'https://github.com/zhadyz/tactical-rag-system/tree/v4.2-production'
  },
  docsRepositoryBase: 'https://github.com/zhadyz/tactical-rag-system/tree/v4.2-production/docs-site',
  footer: {
    text: (
      <div className="flex w-full flex-col items-center gap-2 text-sm text-gray-500 dark:text-gray-400 sm:flex-row sm:justify-between">
        <span>Forge V5 — Agentic RAG with 14 cutting-edge techniques</span>
        <span>&copy; {new Date().getFullYear()} Forge. Built with Next.js &amp; Nextra.</span>
      </div>
    )
  },
  head: () => {
    const { asPath, defaultLocale, locale } = useRouter()
    const { frontMatter } = useConfig()
    const url =
      'https://forge.onyxlab.ai' +
      (defaultLocale === locale ? asPath : `/${locale}${asPath}`)

    return (
      <>
        <meta property="og:url" content={url} />
        <meta property="og:title" content={frontMatter.title || 'Forge V5'} />
        <meta
          property="og:description"
          content={frontMatter.description || 'The most advanced RAG system you can run on a single GPU'}
        />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="theme-color" content="#2563eb" />
        <link rel="icon" type="image/png" sizes="32x32" href="/forge-logo.png" />
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
  // Sidebar
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
            Report an issue with this page &rarr;
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
    storageKey: 'forge-theme'
  },
  // Banner
  banner: {
    key: 'forge-v5-banner',
    text: (
      <span className="flex items-center justify-center gap-2 text-sm">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-600 px-2 py-0.5 text-[10px] font-semibold text-white">
          V5
        </span>
        Forge V5 &mdash; 14 cutting-edge RAG techniques in one system
      </span>
    )
  },
  // Git timestamp - disabled
  gitTimestamp: null,
  // Favicon
  faviconGlyph: '\u26A1',
  // MDX Components
  components: {
    Callout
  }
}

export default config
