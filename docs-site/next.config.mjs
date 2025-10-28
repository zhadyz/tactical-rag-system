import nextra from 'nextra'

const withNextra = nextra({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.tsx',
  defaultShowCopyCode: true,
  latex: true,
  search: {
    codeblocks: true
  },
  mdxOptions: {
    remarkPlugins: [],
    rehypePlugins: []
  }
})

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'export',
  images: {
    unoptimized: true
  },
  eslint: {
    ignoreDuringBuilds: true
  },
  typescript: {
    ignoreBuildErrors: true
  },
  // Optimize for static export (GitHub Pages, Vercel, etc.)
  trailingSlash: true,
  // Performance optimizations
  compress: true,
  poweredByHeader: false,
  generateEtags: true
}

export default withNextra(nextConfig)
