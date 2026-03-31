# Implementation Plan: INEC Election Results Agent

## Overview

This implementation plan covers the AI-powered system for extracting Nigerian election results from the INEC IREV portal. The system uses Python (FastAPI, Celery) for backend services, Next.js/TypeScript for the dashboard, PostgreSQL for data storage, and LangGraph for multi-agent orchestration.

## Tasks

- [x] 1. Set up project structure and core configuration
  - [x] 1.1 Initialize backend project with FastAPI and dependencies
    - Create `backend/` directory structure as specified in design
    - Set up `pyproject.toml` with dependencies: FastAPI, SQLAlchemy, Celery, Redis, Playwright, pytesseract, openai, langgraph, hypothesis
    - Create `backend/app/config.py` with environment configuration
    - _Requirements: 6.1, 6.5, 7.6_

  - [x] 1.2 Initialize frontend project with Next.js 14
    - Create `frontend/` directory with App Router structure
    - Set up `package.json` with dependencies: Next.js 14, React, Recharts, TanStack Table, Shadcn/ui
    - Create TypeScript interfaces in `frontend/types/index.ts`
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 1.3 Set up Docker Compose for local development
    - Create `docker-compose.yml` with PostgreSQL, Redis services
    - Configure environment variables for database connections
    - _Requirements: 4.1, 6.4_

- [x] 2. Implement database layer
  - [x] 2.1 Create SQLAlchemy models for geographic hierarchy
    - Implement `State`, `LGA`, `Ward`, `PollingUnit` models in `backend/app/models/`
    - Define relationships and foreign keys as per ERD
    - _Requirements: 4.1, 4.6_

  - [x] 2.2 Create SQLAlchemy models for election data
    - Implement `ElectionType`, `PoliticalParty`, `ElectionResult`, `PartyResult` models
    - Implement `ScrapingJob`, `JobLog`, `FlaggedResult` models
    - Define uniqueness constraints for election_type + polling_unit
    - _Requirements: 4.1, 4.3, 4.5_

  - [x] 2.3 Create Alembic migrations
    - Initialize Alembic in `backend/app/db/migrations/`
    - Generate initial migration for all tables
    - Create indexes for query performance
    - _Requirements: 4.1, 4.6_

  - [x] 2.4 Create aggregation SQL views
    - Implement `ward_aggregation` view
    - Implement `lga_aggregation` view
    - _Requirements: 5.1, 5.2_

  - [ ]* 2.5 Write property test for database upsert behavior
    - **Property 10: Database Upsert Behavior**
    - **Validates: Requirements 4.3, 4.4**

  - [ ]* 2.6 Write property test for query filter correctness
    - **Property 11: Query Filter Correctness**
    - **Validates: Requirements 4.6**

- [x] 3. Checkpoint - Database layer complete
  - Ensure all migrations run successfully, ask the user if questions arise.

- [x] 4. Implement scraping engine
  - [x] 4.1 Implement browser manager with rate limiting
    - Create `backend/app/core/scraper/browser.py`
    - Implement `BrowserManager` class with Playwright
    - Add semaphore-based concurrency control
    - Implement exponential backoff retry logic
    - _Requirements: 1.7, 6.5, 7.3_

  - [x] 4.2 Implement portal navigator
    - Create `backend/app/core/scraper/navigator.py`
    - Implement `PortalNavigator` class with methods for each hierarchy level
    - Handle navigation errors and logging
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8_

  - [x] 4.3 Implement result sheet downloader
    - Create `backend/app/core/scraper/downloader.py`
    - Implement `ResultSheetDownloader` class
    - Support PDF and PNG formats
    - Generate filenames encoding location hierarchy
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 4.4 Write property test for retry with exponential backoff
    - **Property 2: Retry with Exponential Backoff**
    - **Validates: Requirements 1.7, 2.4, 7.3**

  - [ ]* 4.5 Write property test for filename encoding hierarchy
    - **Property 3: Filename Encoding Hierarchy**
    - **Validates: Requirements 2.3**

  - [ ]* 4.6 Write property test for rate limiting enforcement
    - **Property 17: Rate Limiting Enforcement**
    - **Validates: Requirements 6.5**

- [x] 5. Implement OCR and data extraction
  - [x] 5.1 Implement image preprocessor
    - Create `backend/app/core/ocr/preprocessing.py`
    - Implement grayscale conversion, deskew, noise removal, contrast enhancement
    - Implement quality assessment for OCR engine selection
    - _Requirements: 3.1_

  - [x] 5.2 Implement Tesseract OCR engine
    - Create `backend/app/core/ocr/tesseract.py`
    - Implement `TesseractEngine` class with text and table extraction
    - Return confidence scores with results
    - _Requirements: 3.1_

  - [x] 5.3 Implement GPT-4 Vision integration
    - Create `backend/app/core/ocr/vision.py`
    - Implement `GPT4VisionEngine` class with extraction prompt
    - Handle API responses and parse JSON output
    - _Requirements: 3.1, 3.2_

  - [x] 5.4 Implement OCR orchestration engine
    - Create `backend/app/core/ocr/engine.py`
    - Implement engine selection based on image quality
    - Coordinate between Tesseract and GPT-4 Vision
    - _Requirements: 3.1_

  - [x] 5.5 Implement election data extractor
    - Create `backend/app/core/extractor/parser.py`
    - Implement `ElectionDataExtractor` with party pattern matching
    - Extract party votes, accredited voters, valid votes, rejected votes
    - _Requirements: 3.2, 3.3, 3.4, 3.5_

  - [x] 5.6 Implement data validator
    - Create `backend/app/core/extractor/validator.py`
    - Implement `DataValidator` with vote sum validation (±2 tolerance)
    - Calculate confidence scores
    - Flag invalid results for manual review
    - _Requirements: 3.6, 3.7, 3.8_

  - [ ]* 5.7 Write property test for OCR text extraction
    - **Property 5: OCR Text Extraction**
    - **Validates: Requirements 3.1**

  - [ ]* 5.8 Write property test for data extraction completeness
    - **Property 6: Data Extraction Completeness**
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5**

  - [ ]* 5.9 Write property test for vote sum validation
    - **Property 7: Vote Sum Validation**
    - **Validates: Requirements 3.8**

  - [ ]* 5.10 Write property test for flagging for manual review
    - **Property 8: Flagging for Manual Review**
    - **Validates: Requirements 3.6, 3.7**

- [x] 6. Checkpoint - OCR pipeline complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement aggregation service
  - [x] 7.1 Implement aggregation service
    - Create `backend/app/core/aggregator/service.py`
    - Implement ward-level aggregation
    - Implement LGA-level aggregation
    - Calculate percentages and party rankings
    - Track polling unit counts and flagged results
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 7.2 Write property test for aggregation sum correctness
    - **Property 12: Aggregation Sum Correctness**
    - **Validates: Requirements 5.1, 5.2**

  - [ ]* 7.3 Write property test for percentage calculation
    - **Property 13: Percentage Calculation**
    - **Validates: Requirements 5.3**

  - [ ]* 7.4 Write property test for party ranking order
    - **Property 14: Party Ranking Order**
    - **Validates: Requirements 5.4**

  - [ ]* 7.5 Write property test for aggregation count accuracy
    - **Property 15: Aggregation Count Accuracy**
    - **Validates: Requirements 5.5, 5.6**

- [x] 8. Implement LangGraph agent system
  - [x] 8.1 Implement agent state and graph definition
    - Create `backend/app/agents/graph.py`
    - Define `AgentState` TypedDict
    - Create LangGraph workflow with nodes: navigate, download, preprocess, ocr, extract, validate, store, flag
    - Add conditional edges for validation routing
    - _Requirements: 1.1, 2.1, 3.1, 4.2_

  - [x] 8.2 Implement orchestrator agent
    - Create `backend/app/agents/orchestrator.py`
    - Implement `OrchestratorAgent` class
    - Handle work distribution, progress monitoring, failure handling
    - Manage job state and checkpoints
    - _Requirements: 6.3, 6.4, 7.4_

  - [x] 8.3 Implement navigator agent
    - Create `backend/app/agents/navigator.py`
    - Implement `NavigatorAgent` class
    - Integrate with portal navigator and downloader
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1_

  - [x] 8.4 Implement processor agent
    - Create `backend/app/agents/processor.py`
    - Implement `ProcessorAgent` class
    - Integrate with OCR engine and data extractor
    - _Requirements: 3.1, 3.2_

  - [x] 8.5 Implement validator agent
    - Create `backend/app/agents/validator.py`
    - Implement `ValidatorAgent` class
    - Integrate with data validator
    - Handle flagging for manual review
    - _Requirements: 3.6, 3.7, 3.8_

  - [x] 8.6 Implement agent pool for parallel processing
    - Create `backend/app/agents/pool.py`
    - Implement `AgentPool` class with semaphore-based concurrency
    - Support batch processing
    - _Requirements: 6.5_

  - [ ]* 8.7 Write property test for pause/resume round trip
    - **Property 16: Pause/Resume Round Trip**
    - **Validates: Requirements 6.3, 6.4**

- [x] 9. Implement Celery workers and tasks
  - [x] 9.1 Configure Celery application
    - Create `backend/app/workers/celery_app.py`
    - Configure Redis as broker and result backend
    - Set up task routing and concurrency
    - _Requirements: 6.3, 6.4_

  - [x] 9.2 Implement background tasks
    - Create `backend/app/workers/tasks.py`
    - Implement scraping task with job state management
    - Implement export generation tasks
    - _Requirements: 6.3, 6.4, 8.1, 8.2_

- [x] 10. Checkpoint - Agent system complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement FastAPI endpoints
  - [x] 11.1 Implement elections API endpoints
    - Create `backend/app/api/v1/elections.py`
    - Implement GET endpoints for election types, states, LGAs, wards, polling units
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 11.2 Implement results API endpoints
    - Create `backend/app/api/v1/results.py`
    - Implement GET endpoints for results listing and detail
    - Implement POST endpoint for flagging results
    - _Requirements: 4.6, 3.6_

  - [x] 11.3 Implement aggregation API endpoints
    - Create `backend/app/api/v1/aggregation.py`
    - Implement GET endpoints for ward, LGA, state aggregation
    - _Requirements: 5.1, 5.2_

  - [x] 11.4 Implement jobs API endpoints
    - Create `backend/app/api/v1/jobs.py`
    - Implement POST endpoint for starting scraping jobs
    - Implement GET endpoint for job status
    - Implement POST endpoints for pause/resume
    - Implement DELETE endpoint for cancellation
    - _Requirements: 6.1, 6.2, 6.3, 6.6_

  - [x] 11.5 Implement export API endpoints
    - Create `backend/app/api/v1/export.py`
    - Implement POST endpoints for CSV and JSON export
    - Implement GET endpoint for download
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 11.6 Write property test for CSV export validity
    - **Property 21: CSV Export Validity**
    - **Validates: Requirements 8.1, 8.3**

  - [ ]* 11.7 Write property test for JSON export round trip
    - **Property 22: JSON Export Round Trip**
    - **Validates: Requirements 8.2, 8.4**

  - [ ]* 11.8 Write property test for export filter correctness
    - **Property 23: Export Filter Correctness**
    - **Validates: Requirements 8.3**

- [x] 12. Implement logging and error handling
  - [x] 12.1 Configure logging system
    - Create `backend/app/config/logging.py`
    - Set up JSON formatter for structured logging
    - Configure rotating file handler
    - _Requirements: 7.1, 7.2, 7.6_

  - [x] 12.2 Implement error handlers and retry queue
    - Create error categorization (network, parsing, validation)
    - Implement failed items queue for retry/review
    - _Requirements: 7.2, 7.3, 7.5_

  - [ ]* 12.3 Write property test for log entry completeness
    - **Property 18: Log Entry Completeness**
    - **Validates: Requirements 7.1, 7.2**

  - [ ]* 12.4 Write property test for session summary accuracy
    - **Property 19: Session Summary Accuracy**
    - **Validates: Requirements 7.4**

  - [ ]* 12.5 Write property test for failed items queue
    - **Property 20: Failed Items Queue**
    - **Validates: Requirements 7.5**

- [x] 13. Checkpoint - Backend complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Implement frontend dashboard
  - [x] 14.1 Create root layout and providers
    - Create `frontend/app/layout.tsx` with theme provider
    - Set up API client in `frontend/lib/api.ts`
    - _Requirements: 5.1_

  - [x] 14.2 Implement home dashboard page
    - Create `frontend/app/page.tsx`
    - Display overview statistics and quick actions
    - _Requirements: 5.1_

  - [x] 14.3 Implement election browser pages
    - Create `frontend/app/elections/page.tsx` for election types
    - Create `frontend/app/elections/[type]/page.tsx` for states
    - Create `frontend/app/elections/[type]/[state]/page.tsx` for drill-down
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 14.4 Implement results viewer pages
    - Create `frontend/app/results/page.tsx` for results list
    - Create `frontend/app/results/[id]/page.tsx` for result detail
    - Implement data table with sorting and filtering
    - _Requirements: 4.6_

  - [x] 14.5 Implement aggregation view page
    - Create `frontend/app/aggregation/page.tsx`
    - Display ward and LGA aggregation with party rankings
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 14.6 Implement chart components
    - Create `frontend/components/charts/PartyBarChart.tsx`
    - Create `frontend/components/charts/VoteDistributionPie.tsx`
    - Create `frontend/components/charts/TrendLineChart.tsx`
    - _Requirements: 5.3, 5.4_

  - [x] 14.7 Implement job monitor component
    - Create job status display with progress tracking
    - Implement pause/resume/cancel controls
    - _Requirements: 2.6, 6.3, 6.6_

  - [x] 14.8 Implement export center
    - Create export form with filter options
    - Support CSV and JSON format selection
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 15. Final checkpoint - All components integrated
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests use Hypothesis library with minimum 100 iterations
- Backend uses Python 3.11+ with FastAPI, frontend uses TypeScript with Next.js 14
