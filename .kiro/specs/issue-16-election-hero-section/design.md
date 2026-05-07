# Design: Election Results Hero Section with Top Contestants

## Overview

This feature adds a hero banner component to the home page that displays a live summary of election results — the top 3 leading parties with vote counts, percentages, and progress indicators. It reuses the existing aggregation API and shares election type state with the map section.

## Architecture Decision: Lift State Up

Currently, `MapSection` manages its own election type state internally. To share the selected election type between the hero section and the map, we'll **lift the election type state up** to the home page (`page.tsx`). Both `ElectionHero` and `MapSection` will receive the selected election type as a prop.

This requires a minor refactor of `MapSection` to accept an optional `selectedElectionTypeId` prop and `onElectionTypeChange` callback.

## Component Design

### New Component: `frontend/components/dashboard/ElectionHero.tsx`

```
ElectionHero
├── Header (election type name + "Live Results")
├── ContestantCards (top 3 parties)
│   ├── PartyColorIndicator
│   ├── PartyCode + VoteCount + Percentage
│   ├── ProgressBar (proportional)
│   └── "Leading" badge (rank 1 only)
└── SummaryStats
    ├── Total Valid Votes
    ├── Polling Units Progress (processed/total)
    └── Last Updated timestamp
```

**Props:**
```typescript
interface ElectionHeroProps {
  electionTypeId: string | null;
  electionTypeName: string;
  usingDemoData: boolean;
}
```

The component internally fetches aggregation data using `api.getElectionTypeAggregation()` or generates demo data via `generateDemoData()` when the API is unavailable.

### Modified Component: `frontend/app/page.tsx`

- Lifts election type state (types list, selected ID) to page level
- Passes `selectedElectionTypeId` and `onElectionTypeChange` to `MapSection`
- Renders `ElectionHero` above `MapSection`

### Modified Component: `frontend/components/map/MapSection.tsx`

- Accepts optional `externalElectionTypeId` and `onElectionTypeChange` props
- When `externalElectionTypeId` is provided, uses it instead of internal state
- Calls `onElectionTypeChange` when user selects a different election type

## Data Flow

```
page.tsx (state owner)
  ├── selectedElectionTypeId (state)
  ├── electionTypes[] (state)
  │
  ├── <ElectionHero electionTypeId={...} />
  │     └── fetches /aggregation/election-type/{id}
  │         OR generates demo data
  │
  └── <MapSection externalElectionTypeId={...} onElectionTypeChange={...} />
        └── fetches /aggregation/states?election_type_id={id}
```

## API Usage

**Existing endpoint (no backend changes needed):**
```
GET /api/v1/aggregation/election-type/{election_type_id}
```

Response shape:
```json
{
  "level": "election_type",
  "location_name": "Presidential",
  "party_results": [
    { "party_code": "APC", "total_votes": 4532109, "percentage": 37.2, "rank": 1 },
    ...
  ],
  "total_valid_votes": 12190000,
  "processed_polling_units": 12450,
  "total_polling_units": 176846
}
```

## Demo Data Strategy

When the API is unavailable, the hero section will:
1. Aggregate all state-level demo data from `generateDemoData()` to produce election-type-level totals
2. Sum party votes across all states
3. Calculate percentages and rank parties

This reuses the existing demo data infrastructure without new data generation.

## Styling

- Background: subtle gradient (`from-slate-50 to-white` light / `from-slate-900 to-slate-800` dark)
- Party progress bars use colors from `PARTY_COLORS` map
- Leading party gets a green "Leading" badge with a trophy icon from Lucide
- Responsive: 3-column grid on desktop, stacked on mobile
- Max height ~200px on desktop via padding constraints

## Refresh Strategy

- `useEffect` with `setInterval(60000)` to re-fetch data
- Stores `lastUpdated` timestamp in component state
- Displays relative time ("Updated X min ago") using simple date math
- Clears interval on unmount

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `frontend/components/dashboard/ElectionHero.tsx` | CREATE | New hero section component |
| `frontend/app/page.tsx` | MODIFY | Lift election type state, add hero section |
| `frontend/components/map/MapSection.tsx` | MODIFY | Accept external election type props |
| `frontend/lib/demo-map-data.ts` | MODIFY | Add helper to aggregate demo data for hero |
