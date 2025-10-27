# Apollo RAG - Interactive Demonstrations

> **"The documentation that makes developers think: 'I need to use this just to see these demos.'"**

## Overview

Six revolutionary interactive components that showcase Apollo's GPU-accelerated RAG capabilities in ways NO other documentation does. Built with React, TypeScript, and cutting-edge web technologies.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Components will be available at:
# http://localhost:5173
```

## The Six Components

### 1. 🏁 GPU vs CPU Performance Race
**The KILLER feature** - Watch both pipelines race side-by-side with real-time metrics.

**File**: `src/components/Demo/PerformanceRace.tsx`

**Features**:
- Split-screen visualization
- Upload your document or use samples
- Real-time progress for 8 pipeline stages
- Final metrics: speedup, time saved, winner
- Export results as JSON

**Showcase Value**: Instant visual proof of 3x+ GPU speedup

---

### 2. 🎛️ Interactive Benchmark Explorer
Live performance tuning with interactive sliders.

**File**: `src/components/Demo/BenchmarkExplorer.tsx`

**Features**:
- 4 adjustable parameters (document size, chunk size, top_k, model)
- Live updating charts (latency, cost over time)
- Cost calculator: GPU vs CPU savings
- Export benchmark report
- Real interpolated data

**Showcase Value**: Explore performance across all configurations

---

### 3. 🔄 RAG Pipeline Visualizer
Animated flow diagram with step-by-step breakdown.

**File**: `src/components/Demo/RAGPipelineVisualizer.tsx`

**Features**:
- 8 pipeline stages with animations
- Click each step for deep-dive
- Real GPU vs CPU timings per stage
- Input/output visualization
- Progress tracking

**Showcase Value**: Understand exactly how RAG works under the hood

---

### 4. 💻 Live Code Playground
Ready-to-run code examples across frameworks.

**File**: `src/components/Demo/CodePlayground.tsx`

**Features**:
- Python, Node.js, curl examples
- 4+ examples per framework
- Syntax highlighting
- Copy code functionality
- Mock response output
- Link to API docs

**Showcase Value**: Get started in seconds with working code

---

### 5. 🌌 3D Embedding Visualizer
Visualize semantic similarity in 3D space.

**File**: `src/components/Demo/EmbeddingVisualizer.tsx`

**Features**:
- 3D scatter plot (Three.js)
- Adjustable similarity threshold
- 3 color schemes (similarity, source, cluster)
- Nearest neighbors list
- Interactive orbit controls
- Connection lines to query

**Showcase Value**: See how embeddings cluster in vector space

---

### 6. 📊 Performance Metrics Dashboard
Real-time system monitoring with live charts.

**File**: `src/components/Demo/MetricsDashboard.tsx`

**Features**:
- 8 key metrics (latency, throughput, cache, GPU, etc.)
- 4 real-time charts
- Performance alerts
- Live/pause toggle
- Trend indicators
- 30-second history

**Showcase Value**: Monitor system health in production

---

## File Structure

```
src/
├── components/
│   └── Demo/
│       ├── PerformanceRace.tsx          # GPU vs CPU race
│       ├── BenchmarkExplorer.tsx        # Interactive benchmarks
│       ├── RAGPipelineVisualizer.tsx    # Pipeline animation
│       ├── CodePlayground.tsx           # Code examples
│       ├── EmbeddingVisualizer.tsx      # 3D embeddings
│       ├── MetricsDashboard.tsx         # Real-time metrics
│       └── index.ts                     # Exports
├── types/
│   └── demo.ts                          # TypeScript definitions
├── data/
│   └── benchmarks.json                  # Real benchmark data
└── styles/
    └── demo.css                         # Custom styles
```

## Technologies

- **Framework**: React 19 + TypeScript
- **Charts**: Recharts
- **Animations**: Framer Motion
- **3D Graphics**: Three.js / React Three Fiber
- **Code Editor**: Sandpack
- **Styling**: Tailwind CSS
- **Build**: Vite

## Dependencies

```json
{
  "recharts": "^2.x",
  "framer-motion": "^11.x",
  "three": "^0.160.x",
  "@react-three/fiber": "^8.x",
  "@react-three/drei": "^9.x",
  "@codesandbox/sandpack-react": "^2.x",
  "d3": "^7.x"
}
```

## Usage

### Import All Components
```tsx
import {
  PerformanceRace,
  BenchmarkExplorer,
  RAGPipelineVisualizer,
  CodePlayground,
  EmbeddingVisualizer,
  MetricsDashboard
} from '@/components/Demo';

import '@/styles/demo.css';
```

### Use Individual Components
```tsx
function DemoPage() {
  return (
    <div className="space-y-8">
      <PerformanceRace />
      <BenchmarkExplorer />
      <RAGPipelineVisualizer mode="gpu" />
      <CodePlayground />
      <EmbeddingVisualizer />
      <MetricsDashboard />
    </div>
  );
}
```

## Data Sources

### Real Benchmark Data
All performance metrics come from actual Apollo RAG optimization results:
- `PERFORMANCE_TEST_RESULTS.md` - Quick Wins #1-6 results
- `benchmarks.json` - Structured benchmark data
- Pipeline stage timings (GPU vs CPU)
- Cost analysis (10k queries/month)

### Type Safety
Comprehensive TypeScript definitions in `demo.ts`:
- `RaceResult`, `RaceStage`, `RaceConfig`
- `BenchmarkConfig`, `BenchmarkMetrics`
- `PipelineStep`, `RAGPipelineData`
- `EmbeddingPoint`, `EmbeddingSpace`
- `RealtimeMetrics`, `PerformanceAlert`

## Design System

### Color Palette
- **GPU**: Purple-Blue gradient `#8b5cf6 → #3b82f6`
- **CPU**: Orange-Red gradient `#f97316 → #ef4444`
- **Success**: Green `#10b981`
- **Warning**: Yellow `#f59e0b`
- **Error**: Red `#ef4444`

### Responsive Breakpoints
- Mobile: < 768px (1 column)
- Tablet: 768-1024px (2 columns)
- Desktop: > 1024px (3-4 columns)

### Accessibility
- WCAG AA compliant
- Keyboard navigation
- ARIA labels
- Focus indicators
- Screen reader support

## Performance

### Optimizations
- Code splitting with lazy loading
- Memoization (`useMemo`, `React.memo`)
- Throttled chart updates (2s)
- Limited data points (30 max)
- Disabled animations for real-time data
- GPU-accelerated CSS

### Target Metrics
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- 60fps animations
- Lighthouse Score: 95+

## Browser Support

- Chrome 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅
- Edge 90+ ✅

**Required**: WebGL, ES6 modules, CSS Grid

## Testing

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Storybook (future)
npm run storybook
```

## Export Functionality

All components support data export:

### JSON Export
```typescript
// Performance Race
exportResults() → apollo-performance-race-{timestamp}.json

// Benchmark Explorer
exportReport() → apollo-benchmark-report-{timestamp}.json
```

**Export includes**:
- Configuration parameters
- Results/metrics
- Timestamp metadata
- Comparison statistics

## Future Enhancements

### Phase 2
- [ ] Storybook integration
- [ ] Jest unit tests (100% coverage)
- [ ] Screenshot/PDF export
- [ ] WebSocket real-time data
- [ ] User session persistence

### Phase 3
- [ ] A/B testing framework
- [ ] Analytics integration
- [ ] Customizable themes
- [ ] Component marketplace
- [ ] Sandbox environment

## Documentation

See `DEMO_COMPONENTS_GUIDE.md` for:
- Detailed component documentation
- API reference
- Code examples
- Design patterns
- Best practices

## Contributing

### Component Checklist
- [x] TypeScript strict mode
- [x] Prop validation
- [x] Responsive design
- [x] Dark mode support
- [x] Accessibility (ARIA)
- [x] Loading states
- [x] Error handling
- [ ] Unit tests
- [ ] Storybook story
- [x] Documentation

### Code Style
- ESLint + Prettier
- Conventional commits
- 100% type coverage
- No prop-drilling
- Composition over inheritance

## Credits

**Built by**: HOLLOWED_EYES
**Date**: October 27, 2025
**Version**: Apollo 4.1
**License**: MIT

**Technologies**:
- React 19 + TypeScript
- Tailwind CSS
- Framer Motion
- Recharts
- Three.js
- Sandpack

**Data Source**: Real benchmark results from Apollo's Quick Wins #1-6 performance optimization cycle.

---

## Quick Links

- [Component Guide](./DEMO_COMPONENTS_GUIDE.md) - Detailed documentation
- [Performance Results](./PERFORMANCE_TEST_RESULTS.md) - Real benchmark data
- [API Documentation](http://localhost:8000/docs) - Backend API
- [Apollo Website](https://apollo.onyxlab.ai) - Production site

---

**The demos that prove Apollo isn't just fast—it's revolutionary.**

> *"These components showcase Apollo's capabilities in ways that NO other RAG documentation does. Developers will want to use Apollo just to see these demos."*
