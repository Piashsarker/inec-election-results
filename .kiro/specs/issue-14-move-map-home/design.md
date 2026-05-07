# Technical Design — Issue #14: Move Map to Home Screen

## Overview

Embed the interactive Nigeria election map on the home page (`/`) as the primary visual element. The implementation reuses existing map components (`NigeriaMap`, `StateTooltip`, `MapLegend`, `StateDetailPanel`, `ElectionTypeSelector`) by extracting the map logic into a shared container component that can be used on both the home page and the dedicated `/map` route.

## Architecture

### Component Strategy

Rather than duplicating the map logic in two pages, we'll create a reusable `MapSection` component that encapsulates:
- Election type fetching and selection
- State aggregation data fetching (with demo fallback)
- Hover/click/focus handlers
- Tooltip positioning
- Map + Legend + Detail Panel rendering

Both `app/page.tsx` (home) and `app/map/page.tsx` will use this component.

### Component Hierarchy

```
app/page.tsx (Home)
├── MapSection (new shared component)
│   ├── ElectionTypeSelector
│   ├── NigeriaMap
│   ├── StateTooltip
│   ├── MapLegend
│   └── StateDetailPanel
├── StatCard grid (existing)
├── QuickActionCard grid (existing)
└── JobStatusWidget + Recent Activity (existing)

app/map/page.tsx (Dedicated)
└── MapSection (same component, full-page variant)
```

### New Files

| File | Purpose |
|------|---------|
| `frontend/components/map/MapSection.tsx` | Shared map container with all data fetching and interaction logic |

### Modified Files

| File | Change |
|------|--------|
| `frontend/app/page.tsx` | Import and render `MapSection` above existing dashboard content |
| `frontend/app/map/page.tsx` | Refactor to use `MapSection` instead of inline logic |

## Data Flow

1. `MapSection` mounts → fetches election types from API (falls back to demo data)
2. User selects election type → fetches state aggregations (falls back to demo data)
3. State hover → tooltip appears with position calculation
4. State click → detail panel opens
5. All data stays in `MapSection` local state (no global state needed)

## Props Interface

```typescript
interface MapSectionProps {
  /** Whether to show the header with title and demo data badge */
  showHeader?: boolean;
  /** Optional className for the container */
  className?: string;
  /** Max height constraint for embedded usage */
  compact?: boolean;
}
```

- On the home page: `<MapSection compact showHeader={false} />`
- On the `/map` page: `<MapSection showHeader />`

## Layout Design (Home Page)

```
┌─────────────────────────────────────────────┐
│ Dashboard (h1)                              │
│ AI-powered election results...              │
├─────────────────────────────────────────────┤
│ [Election Type Selector ▼]                  │
│ ┌───────────────────────────┐ ┌───────────┐│
│ │                           │ │  Legend    ││
│ │     Nigeria Map (SVG)     │ │           ││
│ │                           │ │           ││
│ └───────────────────────────┘ └───────────┘│
├─────────────────────────────────────────────┤
│ Stats Grid (4 cards)                        │
├─────────────────────────────────────────────┤
│ Quick Actions (3 cards)                     │
├─────────────────────────────────────────────┤
│ Job Status | Recent Activity                │
└─────────────────────────────────────────────┘
```

## Key Design Decisions

1. **Shared component, not copy-paste** — Avoids code duplication and ensures both pages stay in sync.
2. **`compact` prop** — On the home page, the map has a max-height of ~500px to avoid pushing dashboard content too far down. On `/map`, it fills available space.
3. **No breaking changes to `/map`** — The dedicated map page continues to work identically.
4. **Demo data fallback preserved** — The home page map works without a running backend.
5. **No new dependencies** — Uses existing components and libraries.
