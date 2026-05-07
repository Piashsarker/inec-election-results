# Requirements — Issue #14: Move Map to Home Screen

## Introduction

When users first land on the application, they should immediately see the interactive Nigeria election results map as the primary visual element on the home page (`/`). Currently the map is only accessible via the `/map` route. This change makes the map the centerpiece of the landing experience while preserving the existing dashboard stats and quick actions below it.

## Requirements

### REQ-1: Display Nigeria Map on Home Page

**User Story:** As a user, I want to see the interactive Nigeria election map when I first land on the home page, so that I can immediately visualize election results geographically.

#### Acceptance Criteria

1. The home page (`/`) SHALL display the full interactive Nigeria map component above the existing dashboard content.
2. The map SHALL include the election type selector dropdown.
3. The map SHALL include the map legend.
4. The map SHALL support hover tooltips showing state name, top parties, and processing progress.
5. The map SHALL support click-to-open state detail panel with full party breakdown.
6. The map SHALL use demo data fallback when the backend API is unavailable.

### REQ-2: Preserve Existing Dashboard Content

**User Story:** As a user, I want to still access the dashboard stats, quick actions, and job status widgets below the map, so that I don't lose any existing functionality.

#### Acceptance Criteria

1. The stats grid (Total Results, Polling Units, Processed Today, Flagged for Review) SHALL remain visible below the map section.
2. The Quick Actions cards (Browse Elections, View Results, Aggregation) SHALL remain visible below the stats.
3. The Job Status and Recent Activity widgets SHALL remain at the bottom of the page.
4. The page layout SHALL not break on any viewport size (desktop, tablet).

### REQ-3: Maintain Dedicated Map Route

**User Story:** As a user, I want the `/map` route to continue working as a standalone full-page map view, so that bookmarks and shared links remain valid.

#### Acceptance Criteria

1. The `/map` route SHALL continue to render the full-page map experience unchanged.
2. Navigation links to `/map` from other pages SHALL continue to work.
3. The map on the home page and the `/map` page MAY share the same underlying components.

### REQ-4: Responsive Layout

**User Story:** As a user on different devices, I want the home page map to scale appropriately, so that it's usable on both desktop and tablet viewports.

#### Acceptance Criteria

1. On desktop (≥1024px), the map SHALL display at full container width with the legend beside it.
2. On tablet/mobile (<1024px), the map SHALL stack vertically with the legend below.
3. The map section SHALL have a reasonable max-height to avoid pushing all dashboard content below the fold on smaller screens.
