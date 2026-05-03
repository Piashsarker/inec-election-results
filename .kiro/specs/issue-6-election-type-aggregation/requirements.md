# Requirements: Election Type Aggregation Dashboard (Issue #6)

## Introduction

This document specifies the requirements for the election type aggregation dashboard feature. When a user selects an election type on the `/elections` page, the system should display total vote summaries and aggregate counts per political party for that election type.

**GitHub Issue:** [#6 - Visualization - Dashboard - Browse election by Election Type](https://github.com/Piashsarker/inec-election-results/issues/6)

## Glossary

- **Election_Type_Summary**: Aggregated vote totals across all states for a given election type
- **Party_Aggregation**: Total votes and percentage for a single political party within an election type

## Requirements

### Requirement 1: Backend — Election Type Aggregation Endpoint

**User Story:** As a frontend developer, I need a backend API endpoint that returns aggregated vote totals per party for a given election type, so that the dashboard can display summary data.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/v1/aggregation/election-type/{election_type_id}`, THE API SHALL return aggregated vote totals across all polling units for that election type.
2. THE response SHALL include for each party: party_name, party_code, total_votes, percentage, and rank.
3. THE response SHALL include summary totals: total_valid_votes, total_accredited_voters, total_rejected_votes.
4. THE response SHALL include polling unit counts: total_polling_units, processed_polling_units, flagged_polling_units.
5. IF the election_type_id does not exist, THEN THE API SHALL return a 404 error.

### Requirement 2: Frontend — Election Type Detail Page

**User Story:** As a data analyst, I want to see aggregated vote totals when I select an election type, so that I can understand overall election outcomes.

#### Acceptance Criteria

1. WHEN a user clicks an election type card on `/elections`, THE system SHALL navigate to `/elections/[type]`.
2. THE page SHALL display a summary card showing total valid votes, accredited voters, and rejected votes.
3. THE page SHALL display a bar chart showing vote counts per political party, ranked by votes descending.
4. THE page SHALL display a data table listing each party with vote count, percentage, and rank.
5. THE page SHALL show the count of processed vs total polling units.
6. IF no results exist for the election type, THE page SHALL display an appropriate empty state message.

### Requirement 3: Frontend — API Client Updates

**User Story:** As a frontend developer, I need the API client to support the new aggregation endpoint, so that the dashboard can fetch election type summary data.

#### Acceptance Criteria

1. THE API client SHALL include a function `getElectionTypeAggregation(electionTypeId)` that calls the new backend endpoint.
2. THE TypeScript types SHALL include an `ElectionTypeAggregationResponse` interface matching the backend response schema.
