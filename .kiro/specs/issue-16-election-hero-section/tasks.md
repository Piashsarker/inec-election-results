# Tasks: Election Results Hero Section with Top Contestants

## Task 1: Add demo data aggregation helper
**File:** `frontend/lib/demo-map-data.ts`
**Action:** MODIFY
**Requirements:** REQ-6

Add a `generateDemoElectionTypeAggregation(electionTypeId)` function that:
- Calls `generateDemoData(electionTypeId)` to get per-state data
- Sums party votes across all states
- Calculates percentages and ranks parties by total votes
- Returns an object matching the `ElectionTypeAggregation` type shape

**Done criteria:** Function exported and returns correct aggregated totals from demo data.

---

## Task 2: Create ElectionHero component
**File:** `frontend/components/dashboard/ElectionHero.tsx`
**Action:** CREATE
**Requirements:** REQ-1, REQ-2, REQ-3, REQ-4, REQ-6, REQ-7

Create the `ElectionHero` component with:
- Props: `electionTypeId`, `electionTypeName`, `usingDemoData`
- Internal state: aggregation data, lastUpdated timestamp, loading
- Fetches data from `api.getElectionTypeAggregation()` on mount and every 60s
- Falls back to `generateDemoElectionTypeAggregation()` when API fails
- Renders:
  - Contextual header with election type name
  - Top 3 party cards with color indicator, code, vote count, percentage, progress bar
  - "Leading" badge on rank 1 party
  - Summary stats: total valid votes, polling unit progress, last updated
  - Empty state when no data
- Accessibility: `role="progressbar"`, `aria-valuenow`, `aria-valuemax`, proper headings

**Done criteria:** Component renders correctly with demo data, shows top 3 parties, auto-refreshes, and passes accessibility requirements.

---

## Task 3: Refactor MapSection to accept external election type
**File:** `frontend/components/map/MapSection.tsx`
**Action:** MODIFY
**Requirements:** REQ-5

Add optional props to `MapSection`:
- `externalElectionTypeId?: string | null` — when provided, overrides internal state
- `onElectionTypeChange?: (id: string) => void` — called when user selects a type
- `externalElectionTypes?: ElectionTypeOption[]` — pre-fetched election types
- `externalUsingDemoData?: boolean` — whether demo data mode is active

When external props are provided:
- Skip internal election type fetching
- Use `externalElectionTypeId` for aggregation fetching
- Call `onElectionTypeChange` from the selector callback

Maintain backward compatibility — when no external props are passed, behavior is unchanged.

**Done criteria:** MapSection works both standalone (existing `/map` page) and controlled (home page with shared state).

---

## Task 4: Integrate hero section into home page
**File:** `frontend/app/page.tsx`
**Action:** MODIFY
**Requirements:** REQ-1, REQ-5

Refactor the home page to:
1. Lift election type state to page level (types list, selected ID, demo data flag)
2. Fetch election types on mount (with demo fallback)
3. Render `<ElectionHero>` above the map section
4. Pass shared state to both `ElectionHero` and `MapSection`
5. Handle `onElectionTypeChange` callback to update shared state

**Done criteria:** Home page shows hero section above map, both components stay in sync when election type changes.

---

## Task 5: Lint and verify
**Action:** RUN COMMANDS
**Requirements:** All

1. Run `cd frontend && npx next lint` to check for lint errors
2. Fix any issues found
3. Verify the build compiles: `cd frontend && npx next build`

**Done criteria:** No lint errors, build succeeds.
