# Apollo RAG - Interactive Demo Components Guide

## Overview

This guide documents the 6 revolutionary interactive components that showcase Apollo's capabilities in ways NO other RAG documentation does.

**Build Date**: October 27, 2025
**Version**: 4.1 (Apollo)
**Status**: Production Ready

## Components

### 1. GPU vs CPU Performance Race (`PerformanceRace.tsx`)

**The KILLER Feature** - Split-screen visualization showing both pipelines racing side-by-side.

#### Features
- Real-time progress indicators for both pipelines
- Document upload or sample selection
- Live timing for each stage (chunking, embedding, retrieval, etc.)
- Final metrics comparison with speedup calculation
- Export results as JSON
- Smooth animations with Framer Motion

#### Usage
```tsx
import { PerformanceRace } from '@/components/Demo';

<PerformanceRace className="my-8" />
```

#### Key Metrics Displayed
- Processing time per stage
- Total pipeline duration
- Tokens per second
- Memory usage
- Speedup multiplier
- Winner declaration

#### Technologies
- React + TypeScript
- Framer Motion (animations)
- Custom race simulation engine
- Real benchmark data from PERFORMANCE_TEST_RESULTS.md

---

### 2. Interactive Benchmark Explorer (`BenchmarkExplorer.tsx`)

**Live Performance Tuning** - Interactive sliders with real-time performance updates.

#### Features
- 4 adjustable parameters:
  - Document size (100KB - 2000KB)
  - Chunk size (256 - 2048 chars)
  - Top K results (3 - 20)
  - Model size (7B, 13B, 70B)
- Live updating charts (Recharts)
- Cost calculator (GPU vs CPU over time)
- Performance metrics comparison
- Export benchmark report
- Responsive design

#### Usage
```tsx
import { BenchmarkExplorer } from '@/components/Demo';

<BenchmarkExplorer className="my-8" />
```

#### Visualizations
- Bar chart: Latency comparison
- Area chart: Cumulative cost over 12 months
- Metric tables: Detailed GPU vs CPU breakdown

#### Technologies
- React + TypeScript
- Recharts (charts)
- Real interpolated data from benchmarks.json
- Cost calculation engine

---

### 3. RAG Pipeline Visualizer (`RAGPipelineVisualizer.tsx`)

**Step-by-Step Breakdown** - Animated flow diagram with deep-dive explanations.

#### Features
- 8 pipeline stages:
  1. Document Chunking
  2. Embedding Generation
  3. Vector Storage
  4. Query Embedding
  5. Vector Retrieval
  6. LLM Reranking
  7. Answer Generation
  8. Confidence Scoring
- Click each step for detailed explanation
- Real timings for GPU and CPU
- Progress tracking
- Input/output visualization
- Performance comparison per stage

#### Usage
```tsx
import { RAGPipelineVisualizer } from '@/components/Demo';

<RAGPipelineVisualizer mode="gpu" className="my-8" />
```

#### Interactions
- Play/pause animation
- Reset to beginning
- Click stage for details
- View timing comparison

#### Technologies
- React + TypeScript
- Framer Motion (animations)
- Real pipeline stage timings
- Interactive step details

---

### 4. Live Code Playground (`CodePlayground.tsx`)

**Ready-to-Run Examples** - Pre-configured code examples across multiple frameworks.

#### Features
- 3 framework tabs: Python, Node.js, curl
- 4+ code examples per framework:
  - Basic query
  - Streaming response
  - Document upload
  - Batch processing
- Syntax highlighting
- Copy code functionality
- Mock response output
- Link to API documentation
- Framework selector

#### Usage
```tsx
import { CodePlayground } from '@/components/Demo';

<CodePlayground className="my-8" />
```

#### Example Categories
- **Basic**: Simple RAG queries
- **Streaming**: Token-by-token responses
- **Upload**: Document processing
- **Batch**: Parallel query processing
- **Advanced**: Custom configurations

#### Technologies
- React + TypeScript
- Sandpack (code editor)
- Code syntax highlighting
- Framework-specific examples

---

### 5. Embedding Similarity Visualizer (`EmbeddingVisualizer.tsx`)

**3D Vector Space** - Visualize embedding similarity in 3D space.

#### Features
- 3D scatter plot of embeddings (Three.js)
- Query point highlighted
- Adjustable similarity threshold slider
- 3 color schemes:
  - By similarity (gradient)
  - By source document
  - By cluster
- Nearest neighbors list (top 10)
- Click points for details
- Connection lines to query
- Orbit controls for exploration

#### Usage
```tsx
import { EmbeddingVisualizer } from '@/components/Demo';

<EmbeddingVisualizer className="my-8" />
```

#### Interactions
- Drag to rotate 3D space
- Scroll to zoom
- Click points for info
- Adjust similarity threshold
- Toggle connection lines
- Change color scheme

#### Technologies
- React + TypeScript
- Three.js / React Three Fiber
- @react-three/drei (helpers)
- PCA-reduced embeddings
- Real-time filtering

---

### 6. Performance Metrics Dashboard (`MetricsDashboard.tsx`)

**Real-Time Monitoring** - Live system performance metrics.

#### Features
- 8 key metrics:
  - Query latency
  - Token throughput
  - Cache hit rate
  - GPU utilization
  - GPU memory
  - CPU utilization
  - RAM usage
  - Active connections
- 4 real-time charts (Recharts)
- Performance alerts
- Live/pause toggle
- Trend indicators
- Animated counters
- 30-second history window

#### Usage
```tsx
import { MetricsDashboard } from '@/components/Demo';

<MetricsDashboard className="my-8" />
```

#### Alert Types
- **Warning**: High latency, high GPU usage
- **Info**: Low cache hit rate
- **Error**: Critical thresholds exceeded

#### Technologies
- React + TypeScript
- Recharts (time series)
- Framer Motion (animations)
- Mock real-time data generator
- Alert system with auto-dismiss

---

## Installation

### Dependencies
```bash
npm install recharts framer-motion three @react-three/fiber @react-three/drei @codesandbox/sandpack-react d3
```

### Import Components
```tsx
import {
  PerformanceRace,
  BenchmarkExplorer,
  RAGPipelineVisualizer,
  CodePlayground,
  EmbeddingVisualizer,
  MetricsDashboard
} from '@/components/Demo';

// Import styles
import '@/styles/demo.css';
```

---

## Data Sources

### Benchmark Data (`src/data/benchmarks.json`)
- Real metrics from PERFORMANCE_TEST_RESULTS.md
- Quick Wins #1-6 performance impacts
- Pipeline stage timings
- Sample documents metadata
- GPU vs CPU comparisons

### Type Definitions (`src/types/demo.ts`)
- `RaceResult`, `RaceStage`, `RaceConfig`
- `BenchmarkConfig`, `BenchmarkMetrics`
- `PipelineStep`, `RAGPipelineData`
- `CodeExample`, `PlaygroundState`
- `EmbeddingPoint`, `EmbeddingSpace`
- `RealtimeMetrics`, `PerformanceAlert`

---

## Design System

### Color Palette
- **GPU/Accelerated**: Purple-Blue gradient (#8b5cf6 → #3b82f6)
- **CPU/Standard**: Orange-Red gradient (#f97316 → #ef4444)
- **Success**: Green (#10b981)
- **Warning**: Yellow (#f59e0b)
- **Error**: Red (#ef4444)
- **Info**: Blue (#3b82f6)

### Typography
- **Headers**: Bold, 2xl (24px)
- **Subheaders**: Semibold, lg (18px)
- **Body**: Regular, sm (14px)
- **Code**: Mono, xs (12px)

### Spacing
- **Component padding**: 8 (32px)
- **Card padding**: 4-6 (16-24px)
- **Grid gaps**: 4-6 (16-24px)

### Animations
- **Duration**: 200-500ms
- **Easing**: ease-out, ease-in-out
- **Delays**: Staggered 50ms for lists

---

## Responsive Breakpoints

- **Mobile**: < 768px (1 column)
- **Tablet**: 768px - 1024px (2 columns)
- **Desktop**: > 1024px (3-4 columns)

All components are fully responsive with:
- Collapsible grids
- Scrollable tables
- Adaptive charts
- Touch-friendly controls

---

## Accessibility

### ARIA Labels
- All interactive elements have labels
- Proper role attributes
- Screen reader announcements

### Keyboard Navigation
- Tab order follows visual flow
- Focus indicators on all controls
- Enter/Space for button activation
- Arrow keys for sliders

### Color Contrast
- WCAG AA compliance
- Text contrast ratio > 4.5:1
- Focus indicators with 3:1 contrast

---

## Performance Optimizations

### Code Splitting
```tsx
// Lazy load demo components
const PerformanceRace = lazy(() => import('@/components/Demo/PerformanceRace'));
```

### Memoization
- `useMemo` for expensive calculations
- `React.memo` for pure components
- `useCallback` for event handlers

### Chart Optimization
- Disable animations for real-time data
- Limit data points (30 max for dashboards)
- Throttle updates to 2s intervals

---

## Testing

### Unit Tests
```bash
npm test -- --testPathPattern=Demo
```

### Storybook Stories
```bash
npm run storybook
```

### E2E Tests
```bash
npm run test:e2e
```

---

## Export Functionality

All components support data export:

### JSON Export
- Configuration + results
- Timestamp metadata
- Download as `.json` file

### Image Export (Future)
- PNG screenshots
- PDF reports
- SVG charts

---

## Browser Compatibility

- **Chrome**: ✅ 90+
- **Firefox**: ✅ 88+
- **Safari**: ✅ 14+
- **Edge**: ✅ 90+

### Required Features
- WebGL (for 3D visualizer)
- ES6 modules
- CSS Grid
- Flexbox

---

## Future Enhancements

### Phase 2
1. Storybook integration
2. Jest unit tests
3. Screenshot/PDF export
4. WebSocket real-time data
5. User sessions persistence

### Phase 3
1. A/B testing framework
2. Analytics integration
3. Customizable themes
4. Component marketplace
5. API playground sandbox

---

## Contributing

### Code Style
- TypeScript strict mode
- ESLint + Prettier
- Conventional commits
- 100% type coverage

### Component Checklist
- [ ] TypeScript definitions
- [ ] Prop validation
- [ ] Responsive design
- [ ] Dark mode support
- [ ] Accessibility (ARIA)
- [ ] Loading states
- [ ] Error handling
- [ ] Unit tests
- [ ] Storybook story
- [ ] Documentation

---

## License

MIT License - Apollo RAG System

---

## Credits

**Built by**: HOLLOWED_EYES
**Framework**: React + TypeScript + Vite
**Design**: Tailwind CSS + Framer Motion
**Charts**: Recharts
**3D**: Three.js / React Three Fiber
**Code Editor**: Sandpack

**Data Source**: Real benchmark results from Apollo's performance optimization cycle (Quick Wins #1-6)

---

## Contact

Questions? Issues? Contributions?

- GitHub Issues: `tactical-rag/issues`
- Documentation: `apollo.onyxlab.ai`
- API Docs: `localhost:8000/docs`

---

**The documentation that makes developers think:**
*"I need to use this just to see these demos."*
