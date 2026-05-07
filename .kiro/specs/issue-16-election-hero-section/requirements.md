# Requirements: Election Results Hero Section with Top Contestants

**Issue**: [#16](https://github.com/Piashsarker/inec-election-results/issues/16)

## REQ-1: Hero Section Placement & Layout

The home page (`/`) SHALL display a hero banner **above** the existing map section that:
- Has a contextual header derived from the active election type (e.g., "Presidential Election — Live Results")
- Uses a visually distinct background (gradient or card elevation) to separate it from the dashboard
- Does not exceed ~200px in height on desktop
- Is responsive on desktop and tablet viewports

**Acceptance Criteria:**
1. Hero section renders above the `MapSection` component in `page.tsx`
2. Header text dynamically reflects the selected election type name
3. Section has a distinct visual treatment (gradient background or elevated card)
4. Section height is compact (max ~200px on desktop)

## REQ-2: Top Contestants Display

The hero section SHALL display the **top 3 parties** ranked by total vote count for the selected election type. For each party:
- Party color indicator (colored circle or bar using party brand color from `PARTY_COLORS`)
- Party code (e.g., "APC", "PDP", "LP")
- Total vote count formatted with commas (e.g., "4,532,109")
- Percentage of total valid votes (e.g., "37.2%")
- A visual progress bar showing relative vote share

The leading party (rank 1) SHALL be visually distinguished with a "Leading" badge or larger styling.

**Acceptance Criteria:**
1. Top 3 parties are displayed sorted by vote count descending
2. Each party shows color indicator, code, formatted vote count, and percentage
3. Progress bars reflect proportional vote share
4. Leading party has a visual distinction (badge, larger font, or highlight)

## REQ-3: Summary Statistics

The hero section SHALL display summary statistics:
- Total valid votes counted so far (formatted with commas)
- Polling units reported as fraction (e.g., "12,450 / 176,846 PUs")
- Percentage of results in (as a progress indicator)

**Acceptance Criteria:**
1. Total valid votes are displayed with comma formatting
2. Polling unit progress shows processed/total format
3. A percentage or progress bar indicates overall completion

## REQ-4: Dynamic Updates

The hero section SHALL refresh data automatically:
- Re-fetch aggregation data every 60 seconds via `setInterval`
- Show a "Last updated: X minutes ago" timestamp
- When no data is available, show a graceful empty state ("Awaiting results...")

**Acceptance Criteria:**
1. Data refreshes automatically every 60 seconds
2. "Last updated" timestamp is visible and updates on each refresh
3. Empty state is shown when no aggregation data exists

## REQ-5: Election Type Awareness

The hero section SHALL reflect the **same election type** selected in the map's election type dropdown:
- When the user switches election types, the hero section updates accordingly
- If no election type is selected, default to Presidential

**Acceptance Criteria:**
1. Hero section data changes when election type dropdown changes
2. Default election type is Presidential on initial load
3. State is shared between hero section and map section

## REQ-6: Demo Data Fallback

When the backend API is unavailable, the hero section SHALL use demo data (from `generateDemoData`) to display realistic preview content.

**Acceptance Criteria:**
1. Hero section renders with demo data when API calls fail
2. Demo data badge is shown when using fallback data
3. No error state is shown to the user when gracefully falling back

## REQ-7: Accessibility

The hero section SHALL be accessible:
- Proper heading hierarchy (h2 for section title)
- ARIA labels on progress bars and indicators
- Sufficient color contrast for text and indicators
- Keyboard-navigable elements

**Acceptance Criteria:**
1. Progress bars have `role="progressbar"` and `aria-valuenow`/`aria-valuemax`
2. Section uses semantic HTML with proper heading levels
3. Color indicators are not the sole means of conveying information
