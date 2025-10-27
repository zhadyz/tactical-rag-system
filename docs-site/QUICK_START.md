# 🚀 Apollo Documentation - Quick Start

## Installation

```bash
cd docs-site
npm install
```

## Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Build & Deploy

### Build for Production

```bash
npm run build
```

Output is generated in `out/` directory.

### Deploy to Vercel

```bash
npx vercel --prod
```

### Deploy to GitHub Pages

1. Push to `main` branch
2. GitHub Actions automatically builds and deploys
3. Site available at `https://yourusername.github.io/apollo-rag/`

### Deploy to Netlify

```bash
npm run build
npx netlify deploy --prod --dir=out
```

## Project Structure

```
docs-site/
├── components/          # React components
│   ├── Callout.tsx     # Info/warning/error callouts
│   ├── Card.tsx        # Feature cards
│   ├── CodeBlock.tsx   # Syntax highlighted code
│   ├── MetricCard.tsx  # Performance metrics
│   ├── Tabs.tsx        # Tabbed content
│   └── BenchmarkChart.tsx # Interactive charts
│
├── lib/                # Utilities
│   └── utils.ts        # Helper functions
│
├── pages/              # Documentation pages (MDX)
│   ├── getting-started/
│   ├── core-concepts/
│   ├── api-reference/
│   ├── advanced/
│   ├── benchmarks/
│   └── architecture/
│
├── styles/
│   └── globals.css     # Global styles + Tailwind
│
├── public/             # Static assets
│   ├── images/
│   └── icons/
│
├── next.config.mjs     # Next.js configuration
├── theme.config.tsx    # Nextra theme configuration
└── tailwind.config.ts  # Tailwind configuration
```

## Writing Documentation

### Create a New Page

1. Add MDX file in appropriate directory:
```bash
touch pages/getting-started/new-page.mdx
```

2. Update `_meta.json` in that directory:
```json
{
  "new-page": "New Page Title"
}
```

3. Write content in MDX format:
```mdx
---
title: New Page Title
description: Page description for SEO
---

# Heading

Content here...
```

### Use Components

```mdx
import { Callout } from '@/components/Callout'
import { Card } from '@/components/Card'
import { MetricCard } from '@/components/MetricCard'

<Callout type="info">
  Important information here
</Callout>

<MetricCard
  title="Query Latency"
  value="127"
  unit="ms"
  trend={85}
/>
```

## Customization

### Update Branding

Edit `theme.config.tsx`:

```tsx
logo: (
  <div className="flex items-center gap-2">
    <YourLogo />
    <span>Your Project Name</span>
  </div>
)
```

### Change Colors

Edit `tailwind.config.ts`:

```ts
colors: {
  primary: {
    600: '#your-color',
  }
}
```

### Update Navigation

Edit `pages/_meta.json`:

```json
{
  "section-name": {
    "title": "Section Title",
    "type": "page"
  }
}
```

## Performance

Target metrics:
- ✅ Lighthouse Performance: 95+
- ✅ Lighthouse Accessibility: 100
- ✅ First Contentful Paint: < 1.5s
- ✅ Time to Interactive: < 2.5s

## Troubleshooting

### Build Errors

```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

### Type Errors

```bash
# Run type check
npm run type-check
```

### Styling Issues

```bash
# Rebuild Tailwind
npx tailwindcss -i ./styles/globals.css -o ./styles/output.css
```

## Resources

- [Nextra Documentation](https://nextra.site/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [MDX Documentation](https://mdxjs.com/)

## Support

- GitHub Issues: [Report a bug](https://github.com/yourusername/apollo-rag/issues)
- Discord: [Join community](https://discord.gg/apollo-rag)
- Email: support@apollo.onyxlab.ai
