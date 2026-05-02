---
inclusion: fileMatch
fileMatchPattern: "backend/app/core/scraper/**,backend/local_poller.py"
---

# Scraping Layer - INEC IREV Portal

## Architecture
- **Browser Automation**: Playwright (headless Chromium)
- **Rate Limiting**: Configurable delays + exponential backoff
- **Download**: Async HTTP with retry logic
- **Target**: https://www.inecelectionresults.ng/elections/types

## Project Structure
```
backend/app/core/scraper/
├── __init__.py         # Exports: BrowserManager, INECNavigator, ResultDownloader
├── browser.py          # Playwright browser lifecycle management
├── navigator.py        # INEC portal page navigation (election types → results)
└── downloader.py       # Result sheet image downloading

backend/
└── local_poller.py     # Standalone local scraping script (runs outside Docker)
```

## Browser Management (browser.py)
- `BrowserManager` class:
  - Manages Playwright browser instance lifecycle
  - Headless Chromium with stealth settings
  - Context isolation per scraping session
  - Automatic cleanup on errors
  - Configurable viewport, user-agent

## Navigation (navigator.py)
- `INECNavigator` class:
  - Navigates INEC IREV portal hierarchy:
    Election Types → States → LGAs → Wards → Polling Units → Result Sheets
  - Handles dynamic page loading (waits for elements)
  - Extracts links and metadata from each level
  - Pagination handling for large result sets

## Downloading (downloader.py)
- `ResultDownloader` class:
  - Downloads result sheet images (PNG/JPEG)
  - Async HTTP with configurable timeout
  - Retry with exponential backoff
  - Saves to `data/result_sheets/{election_type}/{state}/{lga}/{ward}/`
  - Deduplication via filename hashing

## Rate Limiting Configuration
```python
# From settings.scraping
max_concurrent_requests: 5      # Parallel browser tabs
request_delay_seconds: 1.0      # Delay between requests
max_retries: 5                  # Retry attempts
backoff_factor: 2.0             # Exponential backoff multiplier
download_timeout_seconds: 30    # Per-download timeout
```

## Local Poller (local_poller.py)
- Standalone script for running scraping from local machine
- Connects to remote database (production)
- Useful when VPS resources are limited
- Run: `python local_poller.py`

## INEC Portal Structure
```
Election Types (presidential, governorship, etc.)
  └── States (36 + FCT)
      └── LGAs (774 total)
          └── Wards (~8,000+)
              └── Polling Units (~176,000+)
                  └── Result Sheet (image)
```

## Key Patterns
- Async context managers for browser lifecycle
- Playwright selectors for dynamic content
- Storage path: `./data/result_sheets/`
- Error handling: retry on network errors, skip on 404
- Progress tracking via database job records

## Environment Variables
- `SCRAPING_MAX_CONCURRENT_REQUESTS` (5)
- `SCRAPING_REQUEST_DELAY_SECONDS` (1.0)
- `SCRAPING_MAX_RETRIES` (5)
- `SCRAPING_DOWNLOAD_TIMEOUT_SECONDS` (30)
- `SCRAPING_STORAGE_PATH` (./data/result_sheets)
- `INEC_PORTAL_URL` (https://www.inecelectionresults.ng/elections/types)
