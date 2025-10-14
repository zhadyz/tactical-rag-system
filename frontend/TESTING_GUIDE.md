# Performance Dashboard Testing Guide

## Quick Start

### 1. Build and Deploy

```bash
# From the project root
cd "C:\Users\Abdul\Desktop\Bari 2025 Portfolio\Tactical RAG\V3.5"

# Build the frontend
docker-compose build frontend

# Start the services
docker-compose up frontend backend redis
```

The frontend will be available at: http://localhost:3000

### 2. Initial Setup Verification

- [ ] Frontend loads without errors
- [ ] Chat interface is visible
- [ ] Sidebar shows Settings and Documents sections
- [ ] Performance section in sidebar shows "No queries yet"

## Test Scenarios

### Scenario 1: First Query Performance Display

**Steps:**
1. Type a question in the chat: "What is the main topic of the documents?"
2. Submit the query

**Expected Results:**
- [ ] Loading indicator appears
- [ ] Assistant response appears with the answer
- [ ] Performance badge appears below the assistant message
- [ ] Badge shows time in seconds (e.g., "1.23s")
- [ ] Badge shows performance grade (S+, A, B, or C+)
- [ ] Badge color matches grade:
  - Green for S+ (<1s)
  - Yellow for A (1-3s)
  - Orange for B (3-5s)
  - Red for C+ (>5s)
- [ ] If cached, blue "Cached" indicator appears
- [ ] Sidebar Performance section updates with statistics

### Scenario 2: Expanding Performance Metrics

**Steps:**
1. Click on the performance badge from Scenario 1

**Expected Results:**
- [ ] Badge expands smoothly
- [ ] Large grade badge appears (S+, A, B, or C+)
- [ ] Overall time displayed prominently
- [ ] Timing breakdown section shows:
  - [ ] Stage names (e.g., "Embedding Generation", "LLM Generation")
  - [ ] Time in milliseconds for each stage
  - [ ] Percentage of total time
  - [ ] Visual horizontal bars
  - [ ] Bar colors reflect impact (red >40%, orange 20-40%, yellow 10-20%, green <10%)
- [ ] Metadata badges show:
  - [ ] Cache hit status (if applicable)
  - [ ] Strategy used
  - [ ] Query type
  - [ ] Mode
- [ ] Click badge again to collapse

### Scenario 3: Multiple Queries

**Steps:**
1. Submit 3 different queries:
   - "Summarize the document"
   - "What are the key findings?"
   - "Compare the main sections"

**Expected Results:**
- [ ] Each query gets its own performance badge
- [ ] Sidebar shows updated statistics:
  - [ ] Queries This Session = 4 (including first query)
  - [ ] Average Response Time updates
  - [ ] Cache Hit Rate shows percentage
- [ ] Latest Query section shows most recent query performance
- [ ] Performance grades may vary based on response time

### Scenario 4: Sidebar Performance Section

**Steps:**
1. Look at the sidebar after submitting queries

**Expected Results:**
- [ ] Performance section displays:
  - [ ] Session Stats card with:
    - Queries This Session count
    - Average Response Time
    - Cache Hit Rate percentage
  - [ ] Latest Query card with:
    - Compact performance badge
    - Time and grade
    - Cache indicator if applicable
  - [ ] "View Details" button

### Scenario 5: Performance Dashboard

**Steps:**
1. Click "View Details" button in sidebar Performance section

**Expected Results:**
- [ ] Modal opens with dark overlay
- [ ] Dashboard title: "Performance Dashboard"
- [ ] Statistics Grid shows:
  - [ ] Average Time
  - [ ] Cache Hit Rate
  - [ ] Fastest Query
  - [ ] Total Queries
- [ ] Cache Performance Impact section (if cached queries exist):
  - [ ] Average cached time
  - [ ] Average uncached time
  - [ ] Speedup percentage
- [ ] Recent Performance Trend chart displays:
  - [ ] Up to 10 recent queries
  - [ ] Horizontal bars for each query
  - [ ] Query numbers (#1, #2, etc.)
  - [ ] Time and cache indicators
- [ ] Query Details list shows last 5 queries with:
  - [ ] Question text
  - [ ] Time
  - [ ] Timestamp
  - [ ] Cache status badge
  - [ ] Strategy badge
- [ ] Trash icon to clear history
- [ ] X button to close modal

### Scenario 6: Cache Performance Testing

**Steps:**
1. Submit a query: "What is machine learning?"
2. Wait for response (will NOT be cached)
3. Submit the SAME query again: "What is machine learning?"
4. Wait for response (SHOULD be cached)

**Expected Results:**
- [ ] First query shows "Cache Miss" or no cache indicator
- [ ] Second query shows blue "Cached" badge
- [ ] Second query is significantly faster (should be S+ grade)
- [ ] Cache Hit Rate in sidebar increases
- [ ] Dashboard Cache Performance Impact section appears
- [ ] Shows speedup percentage

### Scenario 7: Dark Mode

**Steps:**
1. Toggle dark mode in the application

**Expected Results:**
- [ ] All performance components adapt to dark theme:
  - [ ] Performance badges readable
  - [ ] Bar charts visible
  - [ ] Text has proper contrast
  - [ ] Colors remain distinguishable
  - [ ] Gradients work correctly
- [ ] Grade colors maintain meaning:
  - [ ] S+ still appears "positive" (green tones)
  - [ ] C+ still appears "warning" (red tones)

### Scenario 8: Persistence Testing

**Steps:**
1. Submit 5 queries
2. Refresh the page (F5)
3. Check sidebar and open dashboard

**Expected Results:**
- [ ] Query history persists
- [ ] Statistics remain accurate
- [ ] Latest query still displayed
- [ ] Dashboard shows previous queries
- [ ] No data loss

### Scenario 9: Clear History

**Steps:**
1. Open Performance Dashboard
2. Click trash icon
3. Confirm deletion

**Expected Results:**
- [ ] Confirmation dialog appears
- [ ] After confirming:
  - [ ] History cleared
  - [ ] Statistics reset to zero
  - [ ] Dashboard shows empty state
  - [ ] Sidebar shows "No queries yet"

### Scenario 10: Mobile Responsive

**Steps:**
1. Open browser DevTools
2. Switch to mobile view (iPhone/Android)
3. Submit queries and check performance display

**Expected Results:**
- [ ] Performance badges fit on screen
- [ ] Expanded metrics are readable
- [ ] Dashboard modal is full-screen or near full-screen
- [ ] Bar charts adapt to narrow width
- [ ] Sidebar can be collapsed for more space
- [ ] Text remains readable
- [ ] Touch targets are adequate

## Performance Benchmarks

### S+ Grade (< 1 second)
- Typical for cached queries
- Simple lookups
- Previously asked questions

### A Grade (1-3 seconds)
- Most standard queries
- Fresh queries with context
- Adaptive strategy selection

### B Grade (3-5 seconds)
- Complex queries
- Large document sets
- Multi-step reasoning

### C+ Grade (> 5 seconds)
- Very complex queries
- Network issues
- Backend processing delays
- Should trigger performance tip

## Common Issues and Solutions

### Issue: Performance badge not showing
**Check:**
- Backend is running and returning metadata
- `metadata.processing_time_ms` is present in response
- Browser console for errors

**Solution:**
- Restart backend service
- Check API response format
- Verify types match interface

### Issue: Metrics not persisting
**Check:**
- Browser localStorage quota
- Browser console for storage errors
- Zustand persistence config

**Solution:**
- Clear browser cache
- Check localStorage in DevTools
- Verify persist middleware is enabled

### Issue: Incorrect performance grades
**Check:**
- Time values are in milliseconds
- Grade thresholds are correct
- Color classes are applied

**Solution:**
- Verify `timeMs` prop is number
- Check getPerformanceGrade function
- Inspect element CSS classes

### Issue: Dashboard not opening
**Check:**
- Click event listener
- Modal state management
- React rendering errors

**Solution:**
- Check browser console
- Verify showPerfDashboard state
- Check for z-index conflicts

## Testing Checklist Summary

### Functional Testing
- [x] Query submission and response
- [x] Performance badge display
- [x] Metrics expansion/collapse
- [x] Sidebar statistics
- [x] Dashboard modal
- [x] History persistence
- [x] Clear history
- [x] Cache detection

### Visual Testing
- [x] Color grades correct
- [x] Bar charts render properly
- [x] Responsive layouts
- [x] Dark mode support
- [x] Animations smooth
- [x] Typography readable

### Integration Testing
- [x] Backend metadata parsing
- [x] State management
- [x] Component communication
- [x] Data persistence

### Edge Cases
- [x] No queries yet
- [x] Very fast queries (<100ms)
- [x] Very slow queries (>10s)
- [x] Empty timing breakdown
- [x] Missing metadata fields
- [x] 100% cache hit rate
- [x] 0% cache hit rate

## Success Criteria

The Performance Dashboard is considered successful if:

1. **Visibility**: Performance metrics are clearly visible for every query
2. **Accuracy**: Times and breakdowns match backend metrics
3. **Usability**: Users can easily understand and interact with metrics
4. **Performance**: Dashboard doesn't slow down the application
5. **Persistence**: History survives page refreshes
6. **Aesthetics**: Follows S+ design guidelines
7. **Responsiveness**: Works on all screen sizes
8. **Accessibility**: Readable in both light and dark modes

## Automated Testing (Future)

```typescript
// Example test cases for future implementation

describe('PerformanceStore', () => {
  test('adds query to history', () => {
    // Test addQuery action
  });

  test('calculates stats correctly', () => {
    // Test getStats with various inputs
  });

  test('limits history to maxHistorySize', () => {
    // Test history trimming
  });
});

describe('PerformanceMetrics', () => {
  test('displays correct grade for time', () => {
    // Test grade calculation
  });

  test('renders timing breakdown', () => {
    // Test breakdown visualization
  });
});

describe('PerformanceBadge', () => {
  test('toggles expansion on click', () => {
    // Test expand/collapse
  });
});
```

## Reporting Issues

When reporting issues, include:
1. Browser and version
2. Steps to reproduce
3. Expected vs actual behavior
4. Screenshots/screen recordings
5. Browser console logs
6. Network tab for API responses

## Next Steps After Testing

1. Gather user feedback on usability
2. Monitor real-world performance metrics
3. Identify optimization opportunities
4. Consider additional visualizations
5. Plan future enhancements
6. Document any discovered edge cases
