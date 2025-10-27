# Apollo RAG Documentation

World-class documentation for Apollo RAG - GPU-Accelerated Document Intelligence Platform.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 📁 Project Structure

```
docs-site/
├── pages/              # MDX documentation pages
│   ├── getting-started/
│   ├── core-concepts/
│   ├── api-reference/
│   ├── advanced/
│   ├── benchmarks/
│   └── architecture/
├── components/         # React components
│   ├── Callout.tsx
│   ├── Card.tsx
│   ├── CodeBlock.tsx
│   ├── MetricCard.tsx
│   └── Tabs.tsx
├── lib/               # Utility functions
├── styles/            # Global styles
├── public/            # Static assets
└── theme.config.tsx   # Nextra configuration
```

## 🎨 Design System

### Colors

- **Primary**: `#2563eb` (Blue 600)
- **Accent**: `#10b981` (Green 600)
- **Neutrals**: Gray 50-950

### Typography

- **Sans**: Inter
- **Mono**: JetBrains Mono

### Spacing Scale

`4, 8, 16, 24, 32, 48, 64, 96`

## 📝 Writing Documentation

### MDX Format

All documentation is written in MDX (Markdown + JSX):

```mdx
---
title: Page Title
description: Page description for SEO
---

import { Callout } from '@/components/Callout'

# Heading

Regular markdown content...

<Callout type="info">
  This is a callout with JSX components
</Callout>
```

### Components

Use custom components for enhanced formatting:

```mdx
<Callout type="info|warning|error|success">
  Content here
</Callout>

<Card title="Title" description="Description" icon={Icon} href="/link" />

<MetricCard
  title="Metric Name"
  value="123"
  unit="ms"
  trend={15}
/>

<Tabs items={['Tab 1', 'Tab 2']}>
  <TabsPanel value="Tab 1">Content 1</TabsPanel>
  <TabsPanel value="Tab 2">Content 2</TabsPanel>
</Tabs>
```

## 🔧 Configuration

### Theme Configuration

Edit `theme.config.tsx` to customize:

- Logo and branding
- Navigation
- Footer
- Search
- Social links

### Navigation

Update `pages/_meta.json` to control sidebar navigation:

```json
{
  "page-name": "Display Title",
  "-- Separator": {
    "type": "separator",
    "title": "Section Name"
  }
}
```

## 🚢 Deployment

### Static Export

The site is configured for static export:

```bash
npm run build
```

Output is generated in `out/` directory.

### Deploy to Vercel

```bash
vercel --prod
```

### Deploy to GitHub Pages

```bash
npm run build
# Copy out/ to gh-pages branch
```

### Deploy to Netlify

```bash
netlify deploy --prod --dir=out
```

## 📊 Performance

### Lighthouse Targets

- Performance: 95+
- Accessibility: 100
- Best Practices: 100
- SEO: 100

### Optimizations

- Static generation
- Image optimization
- Code splitting
- Font optimization
- CSS minification

## 🧪 Testing

```bash
# Type check
npm run type-check

# Lint
npm run lint

# Format
npm run format
```

## 📦 Dependencies

### Core

- Next.js 14.2
- Nextra 3.0
- React 19
- TypeScript 5.9

### UI

- Tailwind CSS 3.4
- Radix UI
- Lucide Icons
- Recharts

### Development

- Prettier
- ESLint
- TypeScript

## 🤝 Contributing

1. Create a new branch for your changes
2. Write/update documentation in MDX
3. Test locally with `npm run dev`
4. Submit a pull request

### Style Guide

- Use sentence case for headings
- Keep paragraphs concise (3-4 sentences)
- Include code examples
- Add callouts for important information
- Use tables for comparison data

## 📄 License

MIT License - see LICENSE file for details

---

Built with ❤️ using Next.js + Nextra
