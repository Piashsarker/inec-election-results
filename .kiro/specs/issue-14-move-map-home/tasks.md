# Implementation Tasks — Issue #14: Move Map to Home Screen

## Task 1: Create MapSection shared component

**File:** `frontend/components/map/MapSection.tsx`

**Description:** Extract the map logic from `app/map/page.tsx` into a reusable `MapSection` component. This component encapsulates election type fetching, state aggregation data fetching (with demo fallback), hover/click/focus handlers, tooltip positioning, and renders the NigeriaMap, StateTooltip, MapLegend, ElectionTypeSelector, and StateDetailPanel.

**Props:**
- `showHeader?: boolean` — Whether to show the "Election Results Map" title and demo badge
- `className?: string` — Additional CSS classes for the container
- `compact?: boolean` — When true, constrains map height for embedded usage

**Done Criteria:**
- [ ] Component renders the full interactive map with all interactions working
- [ ] Accepts `showHeader`, `className`, and `compact` props
- [ ] When `compact=true`, map container has `max-h-[500px]` constraint
- [ ] Demo data fallback works when API is unavailable
- [ ] TypeScript compiles without errors

**References:** REQ-1, REQ-3, REQ-4

---

## Task 2: Update home page to include MapSection

**File:** `frontend/app/page.tsx`

**Description:** Import and render `<MapSection compact showHeader={false} />` on the home page between the page header and the stats grid. Add a small section header "Election Results Map" with a "View Full Map →" link to `/map`.

**Done Criteria:**
- [ ] Map renders on the home page above the stats grid
- [ ] Election type selector is visible and functional
- [ ] State hover tooltips work
- [ ] State click opens detail panel
- [ ] "View Full Map →" link navigates to `/map`
- [ ] Existing dashboard content (stats, quick actions, jobs) remains below the map
- [ ] Page is responsive on desktop and tablet

**References:** REQ-1, REQ-2, REQ-4

---

## Task 3: Refactor /map page to use MapSection

**File:** `frontend/app/map/page.tsx`

**Description:** Replace the inline map logic in the `/map` page with `<MapSection showHeader />`. This removes code duplication while preserving the exact same behavior and appearance.

**Done Criteria:**
- [ ] `/map` page renders identically to before the refactor
- [ ] All interactions (hover, click, election type switch) work
- [ ] Demo data fallback works
- [ ] No duplicate code between home page and map page

**References:** REQ-3

---

## Task 4: Verify responsive layout and lint

**Description:** Test the layout on different viewport sizes and run linting to ensure code quality.

**Done Criteria:**
- [ ] Desktop (≥1024px): Map displays with legend beside it
- [ ] Tablet (<1024px): Map and legend stack vertically
- [ ] Home page map doesn't push all content below the fold
- [ ] `npx next lint` passes with no errors on modified files
- [ ] No TypeScript compilation errors

**References:** REQ-4
