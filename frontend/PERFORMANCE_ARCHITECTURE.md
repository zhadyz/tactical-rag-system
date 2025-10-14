# Performance Dashboard Architecture

## Component Hierarchy

```
App
├── Layout
│   ├── Header
│   ├── Sidebar ◄────────────────────────────┐
│   │   ├── Settings Section                 │
│   │   ├── Performance Section ◄──────┐     │
│   │   │   ├── Session Stats          │     │
│   │   │   ├── PerformanceMetrics     │     │
│   │   │   │   (compact mode)          │     │
│   │   │   └── View Details Button ───┼─────┤
│   │   └── Documents Section           │     │
│   │                                    │     │
│   └── ChatWindow                       │     │
│       └── ChatMessage ◄────────────────┤     │
│           ├── Message Content          │     │
│           ├── Sources                  │     │
│           └── PerformanceBadge ◄───────┤     │
│               (collapsible)            │     │
│                                        │     │
├── PerformanceDashboard (Modal) ◄──────┘     │
│   └── TimingHistory                          │
│       ├── Statistics Grid                    │
│       ├── Cache Comparison                   │
│       ├── Performance Trend Chart            │
│       └── Query Details List                 │
│                                              │
└── PerformanceStore ◄────────────────────────┘
    (Zustand State Management)
```

## Data Flow

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐      ┌──────────────┐
│   ChatInput     │─────▶│   useChat    │
└─────────────────┘      │   Hook       │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │   Backend    │
                         │   API Call   │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │   Response   │
                         │   + Metadata │
                         └──────┬───────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                    ▼                        ▼
          ┌─────────────────┐      ┌──────────────────┐
          │   ChatStore     │      │ PerformanceStore │
          │  (Messages)     │      │  (Metrics)       │
          └────────┬────────┘      └────────┬─────────┘
                   │                        │
       ┌───────────┴───────────┬────────────┴─────────┐
       │                       │                      │
       ▼                       ▼                      ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ ChatMessage  │    │    Sidebar       │    │  Dashboard  │
│   Component  │    │   Performance    │    │   Modal     │
└──────────────┘    │    Section       │    └─────────────┘
                    └──────────────────┘
```

## State Management Flow

```
┌────────────────────────────────────────────────────────┐
│              PerformanceStore (Zustand)                │
├────────────────────────────────────────────────────────┤
│                                                        │
│  State:                                                │
│  ├── queryHistory: PerformanceQuery[]                 │
│  └── maxHistorySize: 50                               │
│                                                        │
│  Actions:                                              │
│  ├── addQuery(query)                                  │
│  ├── getStats() → PerformanceStats                    │
│  ├── getRecentQueries(limit)                          │
│  ├── getLatestQuery()                                 │
│  └── clearHistory()                                   │
│                                                        │
│  Persistence:                                          │
│  └── localStorage (last 20 queries)                   │
└────────────────────────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           │             │             │
           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Badge    │  │ Sidebar  │  │Dashboard │
    │Component │  │Component │  │Component │
    └──────────┘  └──────────┘  └──────────┘
```

## Performance Metrics Component Props Flow

```
┌─────────────────────────────────────────────────┐
│         PerformanceMetrics Component            │
├─────────────────────────────────────────────────┤
│                                                 │
│  Props:                                         │
│  ├── timeMs: number                             │
│  ├── breakdown?: TimingBreakdown                │
│  ├── cacheHit?: boolean                         │
│  ├── strategyUsed?: string                      │
│  ├── queryType?: string                         │
│  ├── mode?: string                              │
│  └── compact?: boolean                          │
│                                                 │
│  Rendering:                                     │
│  ├── Performance Grade Calculation              │
│  ├── Overall Time Badge                         │
│  ├── Cache Hit Indicator                        │
│  ├── Metadata Badges                            │
│  ├── Timing Breakdown Chart                     │
│  └── Performance Tips                           │
│                                                 │
│  Modes:                                         │
│  ├── Compact: Single line badge                │
│  └── Full: Complete breakdown                  │
└─────────────────────────────────────────────────┘
```

## Timing Breakdown Visualization

```
Backend Response:
{
  "metadata": {
    "processing_time_ms": 1234,
    "cache_hit": false,
    "timing_breakdown": {
      "total_ms": 1234,
      "stages": {
        "embedding_generation": {
          "time_ms": 150,
          "percentage": 12.1
        },
        "vector_search": {
          "time_ms": 89,
          "percentage": 7.2
        },
        "llm_generation": {
          "time_ms": 890,
          "percentage": 72.1
        },
        "post_processing": {
          "time_ms": 95,
          "percentage": 7.7
        }
      },
      "unaccounted_ms": 10,
      "unaccounted_percentage": 0.9
    }
  }
}

Visual Display:
┌─────────────────────────────────────────────┐
│ Performance: 1.23s [A]                      │
├─────────────────────────────────────────────┤
│                                             │
│ LLM Generation    890ms  72.1%              │
│ ████████████████████████████████ 72.1%      │
│                                             │
│ Embedding Gen     150ms  12.1%              │
│ █████ 12.1%                                 │
│                                             │
│ Post Processing    95ms   7.7%              │
│ ███ 7.7%                                    │
│                                             │
│ Vector Search      89ms   7.2%              │
│ ███ 7.2%                                    │
└─────────────────────────────────────────────┘
```

## Performance Grade Calculation Logic

```typescript
function getPerformanceGrade(timeMs: number) {
  if (timeMs < 1000)  return { grade: 'S+', color: 'green'  };
  if (timeMs < 3000)  return { grade: 'A',  color: 'yellow' };
  if (timeMs < 5000)  return { grade: 'B',  color: 'orange' };
  return                     { grade: 'C+', color: 'red'    };
}
```

## Cache Performance Impact Calculation

```typescript
const cachedQueries = queryHistory.filter(q => q.cache_hit);
const uncachedQueries = queryHistory.filter(q => !q.cache_hit);

const avgCachedTime = average(cachedQueries.map(q => q.time_ms));
const avgUncachedTime = average(uncachedQueries.map(q => q.time_ms));

const speedupPercentage =
  ((avgUncachedTime - avgCachedTime) / avgUncachedTime) * 100;
```

## Component Reusability

```
PerformanceMetrics
├── Used in: PerformanceBadge (expanded view)
├── Used in: Sidebar (compact mode)
└── Used in: TimingHistory (optional)

PerformanceBadge
└── Used in: ChatMessage (inline display)

TimingHistory
└── Used in: PerformanceDashboard (full view)

PerformanceDashboard
└── Triggered from: Sidebar "View Details" button
```

## Responsive Design Breakpoints

```
Mobile (<640px):
- Single column layout
- Compact metrics only
- Simplified bar charts
- Modal full-screen

Tablet (640px-1024px):
- Two column grid for stats
- Full metrics available
- Standard bar charts
- Modal 90% width

Desktop (>1024px):
- Multi-column layouts
- Full dashboard view
- Detailed visualizations
- Modal max-width 4xl
```

## Performance Optimization Strategies

1. **Memoization:**
   - Stats calculations cached
   - Component renders optimized
   - Zustand selective subscriptions

2. **Lazy Loading:**
   - Dashboard modal loaded on demand
   - History limited to recent queries
   - Progressive data fetching

3. **State Updates:**
   - Batched updates in Zustand
   - Minimal re-renders
   - Efficient selectors

4. **Visual Performance:**
   - CSS transitions (not JS animations)
   - GPU-accelerated transforms
   - Optimized SVG icons from Lucide

## Integration Points Summary

```
External APIs:
└── Backend /query endpoint
    └── Returns QueryResponse with metadata

Internal Stores:
├── useStore (Chat messages)
└── usePerformanceStore (Metrics)

Custom Hooks:
├── useChat (API calls + tracking)
└── usePerformanceStore selectors

UI Components:
├── Lucide React (Icons)
├── ReactMarkdown (Content)
└── Tailwind CSS (Styling)
```

## File Structure

```
frontend/src/
├── components/
│   ├── Chat/
│   │   └── ChatMessage.tsx (Modified)
│   ├── Layout/
│   │   └── Sidebar.tsx (Modified)
│   └── Performance/ (New)
│       ├── PerformanceMetrics.tsx
│       ├── PerformanceBadge.tsx
│       ├── TimingHistory.tsx
│       ├── PerformanceDashboard.tsx
│       └── index.ts
├── hooks/
│   └── useChat.ts (Modified)
├── store/
│   ├── useStore.ts (Existing)
│   └── performanceStore.ts (New)
└── types/
    └── index.ts (Existing - already had types)
```

## Build Process

```
Development:
npm run dev → Vite dev server → Hot reload

Production:
npm run build → TypeScript compile → Vite build → dist/

Docker:
docker-compose build frontend → npm run build → nginx serve
```

## Testing Strategy

```
Manual Testing:
├── Query submission and tracking
├── Performance badge display
├── Metrics expansion/collapse
├── Sidebar integration
├── Dashboard modal
├── Dark mode compatibility
└── Mobile responsiveness

Integration Testing:
├── Backend metadata parsing
├── State persistence
├── Multi-query tracking
└── Cache hit detection

Visual Testing:
├── Color grades
├── Chart rendering
├── Responsive layouts
└── Animation smoothness
```

This architecture provides a scalable, maintainable foundation for the S+ Performance Monitoring Dashboard with clear separation of concerns and optimal data flow.
