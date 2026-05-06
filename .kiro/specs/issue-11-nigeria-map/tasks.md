# Implementation Plan: Interactive Nigeria Map with State-Level Election Results

## Overview

This plan implements an interactive SVG map of Nigeria visualizing state-level election results. The implementation proceeds bottom-up: backend bulk endpoint first, then frontend utilities and data modules, then individual UI components, and finally the orchestrating page with navigation integration. Property-based tests validate pure logic functions (color scale, tooltip positioning).

## Tasks

- [x] 1. Backend: Bulk states aggregation endpoint
  - [x] 1.1 Add `GET /api/v1/aggregation/states` endpoint to `backend/app/api/v1/aggregation.py`
    - Accept `election_type_id` as a required query parameter (UUID)
    - Validate that the election type exists; return 404 if not found
    - Fetch all states from the database
    - Run `AggregationService.aggregate_state()` for each state in parallel using `asyncio.gather`
    - Filter out `None` results (states with no data)
    - Return `list[AggregationResponse]` using the existing response model
    - Handle per-task exceptions gracefully (log error, omit state from results)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 1.2 Write unit tests for the bulk states endpoint
    - Test successful response with mocked `AggregationService`
    - Test 404 when election type ID does not exist
    - Test empty list when no states have data
    - Test partial success when one state aggregation fails
    - Add tests to `backend/tests/test_aggregation_api.py`
    - _Requirements: 6.1, 6.4, 6.5_

- [x] 2. Frontend: Static data modules and utilities
  - [x] 2.1 Create Nigeria SVG path data module at `frontend/lib/nigeria-map-data.ts`
    - Export `NigeriaStatePathData` interface with `code`, `name`, and `path` fields
    - Export `NIGERIA_STATES` array with all 36 states + FCT (37 entries total)
    - Export `STATES_BY_CODE` lookup map for O(1) access by state code
    - Use pre-projected SVG paths fitting `viewBox="0 0 800 900"`
    - State codes must match the backend `State.code` field
    - _Requirements: 1.1, 1.3_

  - [x] 2.2 Create party color constants at `frontend/lib/party-colors.ts`
    - Export `PARTY_COLORS` record mapping party codes to hex colors (APC, PDP, LP, NNPP, APGA, ADC, SDP, YPP)
    - Export `DEFAULT_PARTY_COLOR` (gray-500) and `NO_DATA_COLOR` (gray-300)
    - _Requirements: 2.1, 2.5_

  - [x] 2.3 Create color scale utility at `frontend/lib/color-scale.ts`
    - Implement `getStateFillColor(aggregation: StateAggregationData | null): string`
    - Implement `applyIntensity(hexColor: string, intensity: number): string`
    - Intensity formula: `clamp((voteSharePercent - 30) / 50, 0.3, 1.0)`
    - Return `NO_DATA_COLOR` when aggregation is null
    - Convert hex + intensity to HSL string with adjusted lightness
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 2.4 Create tooltip position utility at `frontend/lib/tooltip-position.ts`
    - Implement `calculateTooltipPosition(cursorX, cursorY, tooltipWidth, tooltipHeight, viewportWidth, viewportHeight, offset?): TooltipPosition`
    - Default offset: 12px right and below cursor
    - Flip to left of cursor if tooltip would overflow right edge
    - Flip above cursor if tooltip would overflow bottom edge
    - Ensure result always keeps tooltip within viewport bounds
    - _Requirements: 3.3_

- [x] 3. Frontend: Types and API client
  - [x] 3.1 Add map-related types to `frontend/types/index.ts`
    - Add `StateAggregationData` interface (camelCase fields: stateCode, stateName, locationId, electionTypeId, electionTypeCode, partyResults, totalValidVotes, totalAccreditedVoters, totalRejectedVotes, totalPollingUnits, processedPollingUnits, flaggedPollingUnits)
    - Add `ElectionTypeOption` interface (id, name, code)
    - _Requirements: 6.1_

  - [x] 3.2 Add bulk states API method to `frontend/lib/api.ts`
    - Add `getStatesAggregation(electionTypeId: string)` to the `api` object
    - Call `GET /aggregation/states?election_type_id=${electionTypeId}`
    - Transform snake_case response to camelCase `StateAggregationData[]`
    - _Requirements: 6.1_

- [x] 4. Checkpoint - Ensure backend endpoint and frontend utilities compile
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Frontend: Map UI components
  - [x] 5.1 Create `NigeriaMap` component at `frontend/components/map/NigeriaMap.tsx`
    - Render `<svg>` with `viewBox="0 0 800 900"`, `role="img"`, and descriptive `aria-label`
    - Render each state as a `<path>` with `d` from static path data
    - Compute `fill` using `getStateFillColor()` for each state
    - Add `data-state-code` attribute to each path
    - Add `tabIndex={0}` for keyboard navigation
    - Add `aria-label` with state name and leading party info per state
    - Handle `onMouseEnter`, `onMouseLeave`, `onClick`, `onFocus`, `onKeyDown` (Enter/Space)
    - Apply hover highlight (increased stroke width) on hovered/focused state
    - Scale responsively within container
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 5.2 Create `StateTooltip` component at `frontend/components/map/StateTooltip.tsx`
    - Accept props: stateCode, stateName, aggregation, position, visible
    - Display state name (bold), leading party name + vote count, runner-up party name + vote count, processing progress fraction
    - Position using `calculateTooltipPosition` result
    - Show "No data available" when aggregation is null
    - Use `pointer-events-none` to avoid interfering with hover
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 7.1_

  - [x] 5.3 Create `MapLegend` component at `frontend/components/map/MapLegend.tsx`
    - Display party color swatches with labels (APC, PDP, LP, NNPP, Others)
    - Display color intensity gradient scale (lighter → full saturation)
    - Display "No data" gray indicator
    - Accept optional `className` prop for layout positioning
    - _Requirements: 2.5_

  - [x] 5.4 Create `StateDetailPanel` component at `frontend/components/map/StateDetailPanel.tsx`
    - Build on `@radix-ui/react-dialog` (already installed)
    - Accept props: open, onClose, stateCode, stateName, aggregation
    - Display header with state name
    - Display summary stats: valid votes, rejected votes, accredited voters
    - Display processing progress bar (processed / total PUs)
    - Display party results using existing `PartyBarChart` component
    - Display flagged results count
    - Include "View LGA Breakdown" link navigating to `/aggregation?state={locationId}`
    - Include "Export" dropdown (CSV/JSON) using existing export API
    - Handle close on outside click and close button
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [x] 5.5 Create `ElectionTypeSelector` component at `frontend/components/map/ElectionTypeSelector.tsx`
    - Build on `@radix-ui/react-select` (already installed)
    - Accept props: electionTypes, selectedId, onSelect, loading
    - Render dropdown listing all election types
    - Show loading state while fetching
    - _Requirements: 5.1, 5.4_

- [x] 6. Frontend: Map page and navigation
  - [x] 6.1 Create `/map` page at `frontend/app/map/page.tsx`
    - Manage state: selectedElectionTypeId, hoveredStateCode, selectedStateCode, stateAggregations (Map), loading, error
    - Fetch election types on mount, default to presidential
    - Fetch bulk state aggregations when election type changes
    - Render `ElectionTypeSelector`, `NigeriaMap`, `MapLegend`, `StateTooltip`, `StateDetailPanel`
    - Handle loading indicator while fetching
    - Handle error state: show error message, render states gray
    - Responsive layout: legend beside map on desktop (≥1024px), below map on tablet
    - _Requirements: 1.4, 5.2, 5.3, 7.2, 7.3, 9.1, 9.2, 9.3_

  - [x] 6.2 Add navigation link to `/map` in `frontend/app/layout.tsx`
    - Add `{ href: '/map', label: 'Map', icon: '🗺️' }` to the `navItems` array
    - _Requirements: 1.4_

- [x] 7. Checkpoint - Ensure frontend builds and all components render
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Frontend: Property-based tests
  - [ ]* 8.1 Install `fast-check` as a dev dependency
    - Run `npm install --save-dev fast-check` in the frontend directory
    - _Requirements: N/A (test infrastructure)_

  - [ ]* 8.2 Write property test for color scale monotonicity
    - **Property 2: Color Scale Monotonicity**
    - For any two vote share percentages a < b, intensity for b >= intensity for a
    - For any percentage >= 80%, intensity equals 1.0
    - For any percentage in [50%, 60%], intensity < 1.0
    - Create test file at `frontend/__tests__/color-scale.property.test.ts`
    - **Validates: Requirements 2.1, 2.2, 2.3**

  - [ ]* 8.3 Write property test for tooltip viewport containment
    - **Property 4: Tooltip Viewport Containment**
    - For any cursor position (x, y) within viewport (width, height) and any tooltip dimensions (tw, th), the returned position satisfies: resultX >= 0, resultX + tw <= width, resultY >= 0, resultY + th <= height
    - Create test file at `frontend/__tests__/tooltip-position.property.test.ts`
    - **Validates: Requirements 3.3**

  - [ ]* 8.4 Write property test for state code mapping completeness
    - **Property 1: State Code Mapping Completeness**
    - NIGERIA_STATES array has exactly 37 entries
    - All codes are unique, all names are unique
    - Create test file at `frontend/__tests__/nigeria-map-data.property.test.ts`
    - **Validates: Requirements 1.1, 1.3**

- [x] 9. Final checkpoint - Ensure all tests pass and app builds
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The backend uses Python (FastAPI, pytest, hypothesis) and the frontend uses TypeScript (Next.js, fast-check)
- Checkpoints ensure incremental validation between major phases
- Property tests validate universal correctness properties from the design document
- The existing `PartyBarChart` component is reused in the detail panel
- Radix UI Dialog and Select are already installed as dependencies
