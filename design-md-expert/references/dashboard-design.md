# Information-Dense Dashboard Design

Patterns for building professional, data-rich interfaces.

## Core Principles

**Challenge**: Balance data density with visual clarity  
**Goal**: Maximum information, minimum cognitive load  
**Approach**: Intelligent hierarchy + reactive interactivity

## Typography for Density

### Scale Construction

**Base Value**: 16px (1rem) for body text

**Modular Scales**:
- **Major Second** (1.125): Subtle progression, high density
- **Minor Third** (1.2): Balanced, most common
- **Major Third** (1.25): Moderate contrast
- **Perfect Fourth** (1.333): Strong hierarchy

**Grid Alignment**:
- Calculate with modular scale
- Adjust to 4px/8px grid
- Example: 25px → 24px (nearest 4px increment)

### Dashboard Type Scale

| Scale | Size | Weight | Line Height | Use Case |
|-------|------|--------|-------------|----------|
| **KPI Large** | 48px | Bold | 1.0 | Primary metric numbers |
| **KPI Medium** | 32px | Bold | 1.1 | Secondary metric numbers |
| **KPI Small** | 24px | Semibold | 1.2 | Tertiary metric numbers |
| **Label Large** | 16px | Medium | 1.3 | Section headers, chart titles |
| **Label Medium** | 14px | Medium | 1.4 | Axis labels, legends |
| **Label Small** | 12px | Regular | 1.4 | Metadata, timestamps, captions |
| **Body** | 14px | Regular | 1.5 | Descriptions, tooltips |

### Weight Strategy

**Minimum 3 weights**:
- **Regular (400)**: Body text, labels
- **Medium (500)**: Emphasis, section headers
- **Bold (700)**: KPI numbers, critical data

**Avoid**: Light weights (<400) in dashboards (readability issues)

### Hierarchy Through Weight

```
KPI Number: Bold (700) + Large size
KPI Label: Medium (500) + Small size
Supporting Text: Regular (400) + Small size
```

**Visual Rhythm**: Weight contrast > size contrast for density

## Grid Systems

### Column Structure

| Viewport | Columns | Gutter | Margin | Card Columns |
|----------|---------|--------|--------|--------------|
| **Desktop (1440px+)** | 12-16 | 24px | 32px | 3-4 columns |
| **Laptop (1024-1439px)** | 12 | 20px | 24px | 2-3 columns |
| **Tablet (768-1023px)** | 8 | 16px | 16px | 2 columns |
| **Mobile (<768px)** | 4 | 12px | 16px | 1 column |

### Layout Patterns

**F-Pattern** (most common):
```
┌─────────────────────────────────┐
│ [KPI] [KPI] [KPI] [KPI]        │ ← Top row: Critical metrics
├─────────────────────────────────┤
│ [Chart────────] [Chart────]    │ ← Primary visualizations
├─────────────────────────────────┤
│ [Table──────────────────────]  │ ← Detailed data
└─────────────────────────────────┘
```

**Z-Pattern** (narrative flow):
```
┌─────────────────────────────────┐
│ [Hero KPI──────────────────]   │ ← Primary metric
├─────────────────────────────────┤
│ [Chart] [Chart] [Chart]        │ ← Supporting visualizations
├─────────────────────────────────┤
│ [Detail Table──────────────]   │ ← Drill-down data
└─────────────────────────────────┘
```

**Dashboard Grid** (modular):
```
┌───────┬───────┬───────┬───────┐
│ KPI   │ KPI   │ KPI   │ KPI   │
├───────┴───────┼───────┴───────┤
│ Chart         │ Chart         │
│               │               │
├───────────────┴───────────────┤
│ Table                         │
└───────────────────────────────┘
```

## Visual Hierarchy

### Priority Levels

**Level 1 (Critical)**: Top-left, largest, boldest
- Primary KPIs
- Status indicators
- Critical alerts

**Level 2 (Important)**: Top row, prominent
- Secondary metrics
- Key charts
- Action buttons

**Level 3 (Supporting)**: Middle section, moderate
- Detailed visualizations
- Comparison data
- Filters

**Level 4 (Contextual)**: Bottom, smallest
- Tables
- Historical data
- Footnotes

### Gestalt Principles

**Proximity**: Group related metrics
```
┌─────────────┐  ┌─────────────┐
│ Revenue     │  │ Users       │
│ $1.2M       │  │ 45.2K       │
│ ↑ 12%       │  │ ↑ 8%        │
└─────────────┘  └─────────────┘
  Financial        Engagement
```

**Similarity**: Consistent styling for same data types
- All KPIs: Same card style
- All charts: Same color palette
- All tables: Same row styling

**Enclosure**: Cards/borders for logical grouping
```
┌─────────────────────────────┐
│ Sales Performance           │
│ ┌─────┐ ┌─────┐ ┌─────┐   │
│ │ KPI │ │ KPI │ │ KPI │   │
│ └─────┘ └─────┘ └─────┘   │
└─────────────────────────────┘
```

**Continuity**: Alignment creates visual flow
```
[KPI────] [KPI────] [KPI────]
[Chart──────────────────────]
[Table──────────────────────]
```

## Color Strategy

### Functional Color Palette

**Data Visualization** (8-color palette):
```
Primary:   #1A73E8 (blue)
Secondary: #34A853 (green)
Tertiary:  #FBBC04 (yellow)
Accent 1:  #EA4335 (red)
Accent 2:  #9334E6 (purple)
Accent 3:  #FF6D00 (orange)
Accent 4:  #00ACC1 (cyan)
Accent 5:  #7CB342 (lime)
```

**Semantic Colors**:
```
Success:  #137333 (dark green)
Warning:  #B06000 (dark yellow)
Error:    #C5221F (dark red)
Info:     #1A73E8 (blue)
Neutral:  #5F6368 (gray)
```

**Surface Colors** (light mode):
```
Background:  #FFFFFF
Elevated:    #F8F9FA
Sunken:      #F1F3F4
Border:      #DADCE0
```

### Color Usage Rules

**KPI Cards**:
- Background: Elevated surface
- Number: High-contrast text
- Trend: Semantic color (green ↑, red ↓)
- Label: Secondary text

**Charts**:
- Use data visualization palette
- Maintain 3:1 contrast with background
- Colorblind-safe combinations
- Add patterns for accessibility

**Status Indicators**:
- Never color alone (add icon/text)
- High contrast (3:1 minimum)
- Consistent across dashboard

## Component Patterns

### KPI Card

```
┌─────────────────────┐
│ Revenue             │ ← Label (14px, Medium)
│ $1.2M               │ ← Value (32px, Bold)
│ ↑ 12% vs last month │ ← Trend (12px, Regular, Green)
└─────────────────────┘
```

**Anatomy**:
- Padding: 16px (compact) or 24px (comfortable)
- Background: Elevated surface
- Border: 1px subtle or none
- Border-radius: 8px
- Min-height: 120px

**States**:
- Default: Elevated surface
- Hover: Slight elevation increase (if interactive)
- Loading: Skeleton or spinner

### Chart Container

```
┌─────────────────────────────┐
│ Sales Trend          [⋮]    │ ← Header + menu
├─────────────────────────────┤
│                             │
│     [Chart Visualization]   │ ← Chart area
│                             │
├─────────────────────────────┤
│ ■ Product A  ■ Product B   │ ← Legend
└─────────────────────────────┘
```

**Anatomy**:
- Header: 48px height, title + actions
- Chart area: Min 300px height
- Legend: Below or right side
- Padding: 16px

### Data Table

```
┌─────────────────────────────────────┐
│ Name          Status    Revenue     │ ← Header (sticky)
├─────────────────────────────────────┤
│ Product A     ● Active   $450K      │ ← Row (hover state)
│ Product B     ● Active   $320K      │
│ Product C     ○ Inactive $180K      │
└─────────────────────────────────────┘
```

**Anatomy**:
- Row height: 48px (comfortable) or 40px (compact)
- Header: Bold, sticky on scroll
- Zebra striping: Optional (subtle)
- Hover: Background change
- Borders: Horizontal only (reduces noise)

## Responsive Strategies

### Breakpoint Behavior

**Desktop (1024px+)**:
- Full grid (3-4 columns)
- All metrics visible
- Detailed labels + legends
- Hover interactions

**Tablet (768-1023px)**:
- 2-column grid
- Abbreviated labels
- Simplified legends
- Secondary metrics hidden

**Mobile (<768px)**:
- Single column
- Critical metrics only
- Stacked charts
- Horizontal scroll for tables
- Large touch targets (44px min)

### Adaptive Patterns

**KPI Cards**:
- Desktop: 4 columns
- Tablet: 2 columns
- Mobile: 1 column, swipeable carousel

**Charts**:
- Desktop: Side-by-side
- Tablet: Stacked
- Mobile: Full-width, swipeable

**Tables**:
- Desktop: Full table
- Tablet: Horizontal scroll
- Mobile: Card view (each row = card)

## Interactivity Patterns

### Filters & Controls

**Placement**: Top-left or top-right, above content

**Types**:
- Date range picker
- Dropdown selects
- Search input
- Toggle buttons

**Behavior**:
- Instant feedback (no "Apply" button if possible)
- Loading states during data fetch
- Persist selections in URL

### Drill-Down

**Pattern**: Click metric → detailed view

**Implementation**:
- Modal overlay (quick view)
- Slide-out panel (contextual)
- New page (deep dive)

**Navigation**: Breadcrumbs for hierarchy

### Tooltips

**Trigger**: Hover (desktop) or tap (mobile)

**Content**:
- Detailed metric breakdown
- Calculation formula
- Timestamp
- Comparison data

**Styling**:
- Dark background (high contrast)
- 12-14px text
- Max-width: 300px
- Arrow pointing to target

### Real-Time Updates

**Strategies**:
- Polling (every 30-60s)
- WebSocket (instant)
- Server-sent events (one-way)

**Visual Feedback**:
- Subtle flash on update
- "Updated X seconds ago" timestamp
- Loading indicator during fetch

## Performance Optimization

### Data Loading

**Strategies**:
- Lazy load below-fold content
- Paginate tables (50-100 rows)
- Virtualize long lists
- Cache API responses

**Loading States**:
- Skeleton screens (preferred)
- Spinners (fallback)
- Progressive rendering (show data as it loads)

### Chart Performance

**Optimization**:
- Limit data points (1000 max for line charts)
- Aggregate data server-side
- Use canvas for >500 points (not SVG)
- Debounce interactions (zoom, pan)

### Image Optimization

**Icons**:
- SVG (scalable, small)
- Icon font (if many icons)
- Inline critical icons

**Charts**:
- Render server-side for static charts
- Use WebGL for complex visualizations

## Accessibility

### Screen Reader Support

**KPI Cards**:
```html
<div role="region" aria-labelledby="revenue-label">
  <h3 id="revenue-label">Revenue</h3>
  <p aria-label="1.2 million dollars">$1.2M</p>
  <p aria-label="Up 12% compared to last month">↑ 12%</p>
</div>
```

**Charts**:
- Provide data table alternative
- Use `<figure>` + `<figcaption>`
- Add `aria-label` with summary

**Tables**:
- Use `<th scope="col">` for headers
- Use `<caption>` for table title
- Sortable columns: announce sort state

### Keyboard Navigation

**Requirements**:
- Tab through interactive elements
- Enter/Space to activate
- Arrow keys for chart navigation (optional)
- Escape to close modals/tooltips

### Color Contrast

**Requirements**:
- Text: 4.5:1 minimum
- UI components: 3:1 minimum
- Chart colors: 3:1 against background

**Testing**: Use contrast checker on all text/UI elements

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Too much data** | Cognitive overload | Prioritize; hide secondary metrics |
| **Inconsistent styling** | Confusing, unprofessional | Use design system tokens |
| **Poor hierarchy** | Can't find critical info | F-pattern layout, size/weight contrast |
| **Color-only status** | Inaccessible | Add icons + text labels |
| **Tiny text** | Unreadable | 12px minimum, 14px preferred |
| **No loading states** | Feels broken | Skeleton screens or spinners |
| **Fixed layouts** | Breaks on mobile | Responsive grid, adaptive patterns |
| **Cluttered charts** | Hard to read | Simplify, remove chart junk |
| **No empty states** | Confusing when no data | Provide helpful empty state message |

## Checklist

### Layout
- [ ] F-pattern or Z-pattern hierarchy
- [ ] Critical metrics top-left
- [ ] Consistent spacing (4px/8px grid)
- [ ] Responsive breakpoints (desktop, tablet, mobile)

### Typography
- [ ] 12px minimum font size
- [ ] 3 weights minimum (Regular, Medium, Bold)
- [ ] Clear hierarchy (size + weight)
- [ ] Aligned to 4px/8px grid

### Color
- [ ] 8-color data visualization palette
- [ ] Semantic colors (success, warning, error)
- [ ] 4.5:1 text contrast
- [ ] 3:1 UI component contrast
- [ ] Never color alone (add icons/text)

### Components
- [ ] KPI cards: Label, value, trend
- [ ] Charts: Title, visualization, legend
- [ ] Tables: Sticky header, hover states
- [ ] Filters: Top placement, instant feedback

### Interactivity
- [ ] Loading states (skeleton or spinner)
- [ ] Hover states on interactive elements
- [ ] Tooltips for detailed info
- [ ] Drill-down for deeper analysis

### Accessibility
- [ ] Keyboard navigation
- [ ] Screen reader support (ARIA labels)
- [ ] Color contrast compliance
- [ ] Focus indicators visible
- [ ] Alternative data table for charts

### Performance
- [ ] Lazy load below-fold content
- [ ] Paginate tables
- [ ] Limit chart data points
- [ ] Cache API responses

## Resources

- **Dashboard Design Best Practices**: https://5of10.com/articles/dashboard-design-best-practices/
- **Gestalt Principles**: https://www.interaction-design.org/literature/topics/gestalt-principles
- **Data Visualization**: https://www.storytellingwithdata.com/
- **Chart Types**: https://www.data-to-viz.com/
