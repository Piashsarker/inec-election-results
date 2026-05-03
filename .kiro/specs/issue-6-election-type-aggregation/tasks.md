# Implementation Tasks: Election Type Aggregation Dashboard (Issue #6)

## Overview

Implementation plan for adding election-type-level aggregation to the dashboard.
Backend tasks first, then frontend.

## Tasks

- [x] 1. Backend — Add `aggregate_election_type` method to AggregationService
  - [x] 1.1 Add `aggregate_election_type(election_type_id)` method to `backend/app/core/aggregator/service.py`
    - Query all election results for the given election_type_id
    - Sum votes by party across all polling units
    - Calculate percentages and rank parties descending
    - Count total, processed, and flagged polling units
    - Return `AggregationResult` with level="election_type"
    - Return None if election type not found
    - _Requirement 2_

- [x] 2. Backend — Add election-type aggregation API endpoint
  - [x] 2.1 Add `GET /api/v1/aggregation/election-type/{election_type_id}` endpoint to `backend/app/api/v1/aggregation.py`
    - Call `AggregationService.aggregate_election_type()`
    - Return `AggregationResponse` with party results, totals, and polling unit counts
    - Return 404 if election type not found
    - _Requirement 1_

- [x] 3. Frontend — Update TypeScript types and API client
  - [x] 3.1 Add `ElectionTypeAggregation` interface to `frontend/types/index.ts`
    - Include party results array, vote totals, and polling unit counts
    - _Requirement 4_
  - [x] 3.2 Add `getElectionTypeAggregation(electionTypeId)` to `frontend/lib/api.ts`
    - Call `GET /api/v1/aggregation/election-type/{electionTypeId}`
    - _Requirement 4_

- [x] 4. Frontend — Enhance elections/[type] page with aggregation dashboard
  - [x] 4.1 Update `frontend/app/elections/[type]/page.tsx` to fetch and display aggregation data
    - Fetch election type aggregation on page load
    - Display summary cards (total valid votes, accredited voters, rejected votes)
    - Display PartyBarChart with party vote data
    - Display party results data table with vote count, percentage, and rank
    - Show processed vs total polling unit counts
    - Show empty state when no results exist
    - Retain existing state list below the aggregation section
    - _Requirement 3_
