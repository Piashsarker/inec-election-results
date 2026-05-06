# Requirements Document

## Introduction

This document specifies the requirements for an interactive SVG map of Nigeria that visualizes election results at the state level. The map renders all 36 states plus the Federal Capital Territory (FCT) as clickable, hoverable regions color-coded by the leading party's vote share. Users can inspect state-level aggregated results via tooltips and detail panels, switch between election types, and export data. A bulk backend endpoint provides efficient data fetching for all states in a single request.

## Glossary

- **Nigeria_Map_Component**: The React component (`NigeriaMap`) that renders an SVG map of Nigeria's 36 states and FCT with interactive features
- **State_Region**: An individual SVG `<path>` element representing a Nigerian state or FCT on the map
- **Tooltip**: A floating UI element displayed near the cursor on hover, showing summary election data for a state
- **Detail_Panel**: A side panel or modal opened on click, showing full aggregated election results for a state
- **Legend**: A visual key mapping party colors and intensity levels displayed alongside the map
- **Election_Type_Selector**: A dropdown control allowing users to switch between election types (Presidential, Gubernatorial, etc.)
- **Bulk_States_Endpoint**: The backend API endpoint `GET /api/v1/aggregation/states` that returns aggregated results for all 37 states in a single response
- **Color_Scale**: A mapping from vote share percentage to color intensity (lighter shades for lower margins, full saturation for dominant wins)
- **Leading_Party**: The political party with the highest vote count in a state's aggregated results
- **Processing_Progress**: The ratio of processed polling units to total polling units for a geographic area

## Requirements

### Requirement 1: SVG Map Rendering

**User Story:** As a dashboard user, I want to see an SVG map of Nigeria with all 36 states and FCT rendered as distinct regions, so that I can visually identify geographic election patterns.

#### Acceptance Criteria

1. THE Nigeria_Map_Component SHALL render all 36 Nigerian states and the FCT as distinct SVG `<path>` elements with accurate geographic boundaries
2. WHEN the viewport is resized, THE Nigeria_Map_Component SHALL scale responsively to fit the available container width while maintaining the correct aspect ratio
3. THE Nigeria_Map_Component SHALL assign a `data-state-code` attribute to each State_Region that matches the `State.code` field from the backend model
4. THE Nigeria_Map_Component SHALL be accessible via the `/map` route in the frontend application

### Requirement 2: State Color Coding by Leading Party

**User Story:** As a dashboard user, I want each state colored by the leading party's brand color with intensity reflecting vote share, so that I can quickly see which party dominates each region and by how much.

#### Acceptance Criteria

1. WHEN aggregated results are available for a state, THE Nigeria_Map_Component SHALL fill the State_Region with the Leading_Party's official brand color (APC: green, PDP: red, LP: light blue, NNPP: orange)
2. WHEN the Leading_Party's vote share percentage is between 50-60%, THE Nigeria_Map_Component SHALL render the State_Region fill at a lighter shade of the party color
3. WHEN the Leading_Party's vote share percentage is above 80%, THE Nigeria_Map_Component SHALL render the State_Region fill at full saturation of the party color
4. WHEN no aggregated results exist for a state, THE Nigeria_Map_Component SHALL render the State_Region fill in neutral gray
5. THE Legend SHALL display all party-to-color mappings and the Color_Scale intensity levels

### Requirement 3: Hover Interaction and Tooltip

**User Story:** As a dashboard user, I want to hover over a state and see a summary of election results in a tooltip, so that I can quickly compare states without clicking.

#### Acceptance Criteria

1. WHEN the user hovers over a State_Region, THE Nigeria_Map_Component SHALL visually highlight the state boundary by increasing stroke width or adding a glow effect
2. WHEN the user hovers over a State_Region, THE Tooltip SHALL display the state name, the Leading_Party name and vote count, the runner-up party name and vote count, and the Processing_Progress as a fraction (e.g., "342 / 1,200 PUs reported")
3. WHEN the Tooltip would overflow the viewport boundary, THE Tooltip SHALL reposition dynamically to remain fully visible within the viewport
4. WHEN the user moves the cursor away from a State_Region, THE Tooltip SHALL be hidden and the state boundary highlight SHALL be removed

### Requirement 4: Click Interaction and State Detail Panel

**User Story:** As a dashboard user, I want to click a state and see a full breakdown of election results, so that I can analyze detailed party performance and navigate to deeper data.

#### Acceptance Criteria

1. WHEN the user clicks a State_Region, THE Detail_Panel SHALL open displaying the full aggregated result for that state
2. THE Detail_Panel SHALL display all party results with vote counts, percentages, and a horizontal bar chart visualization
3. THE Detail_Panel SHALL display total valid votes, rejected votes, and accredited voters for the state
4. THE Detail_Panel SHALL display the Processing_Progress showing processed polling units versus total polling units
5. THE Detail_Panel SHALL display the number of flagged results for the state
6. THE Detail_Panel SHALL include a "View LGA Breakdown" link that navigates to `/aggregation?state={stateId}`
7. THE Detail_Panel SHALL include an "Export" button that downloads the state's results as CSV or JSON
8. WHEN the user clicks outside the Detail_Panel or clicks a close button, THE Detail_Panel SHALL close

### Requirement 5: Election Type Selector

**User Story:** As a dashboard user, I want to switch between election types (Presidential, Gubernatorial, etc.) and see the map update accordingly, so that I can compare geographic patterns across different races.

#### Acceptance Criteria

1. THE Election_Type_Selector SHALL be rendered above the map as a dropdown control listing all available election types
2. WHEN the user selects a different election type, THE Nigeria_Map_Component SHALL fetch new state aggregation data for the selected election type and update all State_Region colors accordingly
3. WHEN no election type is explicitly selected, THE Election_Type_Selector SHALL default to the Presidential election type if available
4. WHILE the Nigeria_Map_Component is fetching new aggregation data after an election type change, THE Nigeria_Map_Component SHALL display a loading indicator

### Requirement 6: Bulk States Aggregation Endpoint

**User Story:** As a frontend developer, I want a single API endpoint that returns aggregated results for all states, so that the map can load efficiently without making 37 individual requests.

#### Acceptance Criteria

1. THE Bulk_States_Endpoint SHALL accept an `election_type_id` query parameter and return a list of aggregation responses, one per state that has results
2. THE Bulk_States_Endpoint SHALL reuse the existing `AggregationService.aggregate_state()` logic for each state
3. THE Bulk_States_Endpoint SHALL return the response within a reasonable time by executing state aggregations efficiently
4. IF the provided `election_type_id` does not match any existing election type, THEN THE Bulk_States_Endpoint SHALL return a 404 error with a descriptive message
5. WHEN a state has no election results for the given election type, THE Bulk_States_Endpoint SHALL omit that state from the response list or include it with zero values

### Requirement 7: Graceful Handling of Missing Data

**User Story:** As a dashboard user, I want the map to handle missing or partial data gracefully, so that I can still use the visualization even when not all results have been processed.

#### Acceptance Criteria

1. WHEN a state has no aggregated results, THE Nigeria_Map_Component SHALL render the State_Region in neutral gray with a "No data" indicator in the Tooltip
2. WHEN only partial polling unit results are available for a state, THE Nigeria_Map_Component SHALL still color-code the state based on available data and display the Processing_Progress fraction
3. IF the Bulk_States_Endpoint returns an error, THEN THE Nigeria_Map_Component SHALL display an error message to the user and render all states in neutral gray

### Requirement 8: Accessibility

**User Story:** As a user who relies on assistive technology, I want the map to be keyboard navigable with proper ARIA labels, so that I can access election result information without a mouse.

#### Acceptance Criteria

1. THE Nigeria_Map_Component SHALL allow keyboard navigation between State_Regions using Tab and arrow keys
2. WHEN a State_Region receives keyboard focus, THE Nigeria_Map_Component SHALL apply the same visual highlight as hover and display the Tooltip
3. WHEN the user presses Enter or Space on a focused State_Region, THE Detail_Panel SHALL open for that state
4. THE Nigeria_Map_Component SHALL assign `role="img"` to the SVG element and provide an `aria-label` describing the map's purpose
5. Each State_Region SHALL have an `aria-label` containing the state name and the Leading_Party name with vote percentage

### Requirement 9: Responsive Layout

**User Story:** As a user on different devices, I want the map to display correctly on both desktop and tablet viewports, so that I can access election data regardless of screen size.

#### Acceptance Criteria

1. WHEN the viewport width is 1024px or greater, THE Nigeria_Map_Component SHALL render at full size with the Legend displayed alongside the map
2. WHEN the viewport width is between 768px and 1023px, THE Nigeria_Map_Component SHALL scale down proportionally and reposition the Legend below the map
3. THE Nigeria_Map_Component SHALL maintain readable state boundaries and interactive targets at tablet viewport sizes (minimum touch target of 44x44 CSS pixels for interactive regions where feasible)
