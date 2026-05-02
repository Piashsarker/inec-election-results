---
inclusion: fileMatch
fileMatchPattern: "backend/app/api/**,backend/app/main.py,backend/app/config.py,backend/app/workers/**"
---

# Backend Layer - FastAPI Application

## Architecture
- **Framework**: FastAPI 0.111 with Uvicorn
- **Language**: Python 3.11
- **Config**: Pydantic Settings (env vars + .env file)
- **Task Queue**: Celery with Redis broker
- **Async**: Full async/await with asyncpg

## Project Structure
```
backend/
├── app/
│   ├── main.py             # FastAPI app factory (create_app)
│   ├── config.py           # Pydantic Settings (all config sections)
│   ├── api/
│   │   ├── deps.py         # Dependency injection (DB session)
│   │   └── v1/             # API v1 routes
│   │       ├── elections.py    # Election type/geography browsing
│   │       ├── results.py      # CRUD for election results
│   │       ├── aggregation.py  # Aggregated results endpoints
│   │       ├── jobs.py         # Scraping job management
│   │       └── export.py       # CSV/JSON export
│   ├── workers/
│   │   ├── celery_app.py   # Celery configuration
│   │   └── tasks.py        # Background tasks (scraping, export)
│   └── core/               # Business logic (see other skills)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Production container
└── pyproject.toml          # Package metadata
```

## Configuration (config.py)
Settings are organized into nested Pydantic models:
- `DatabaseSettings` (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DATABASE_URL)
- `RedisSettings` (REDIS_HOST, REDIS_PORT, REDIS_PASSWORD)
- `ScrapingSettings` (rate limits, retries, timeouts)
- `OCRSettings` (tesseract config, confidence thresholds)
- `OpenAISettings` (API key, model, temperature)
- `CelerySettings` (broker URL, concurrency)
- `LoggingSettings` (level, format, file path)

Access via: `from app.config import settings`

## API Routes (prefix: /api/v1)
- `GET /elections/types` - List election types
- `GET /elections/{type}/states` - States for election type
- `GET /results` - Paginated results with filters
- `GET /results/{id}` - Single result detail
- `POST /results/flag/{id}` - Flag result for review
- `GET /aggregation/ward/{id}` - Ward-level aggregation
- `GET /aggregation/lga/{id}` - LGA-level aggregation
- `POST /jobs/scrape` - Start scraping job
- `GET /jobs/{id}` - Job status
- `POST /export/csv` - Generate CSV export

## Key Patterns
- App factory pattern in `main.py` (`create_app()`)
- Lifespan context manager for startup/shutdown
- CORS configured from `settings.cors_origins`
- Health check at `GET /health`
- Dependency injection via FastAPI `Depends()`

## Environment Variables
- `ENVIRONMENT` - development/staging/production
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`
- `CORS_ORIGINS` - JSON array of allowed origins
- `OPENAI_API_KEY` - For Vision OCR

## Running
- Dev: `uvicorn app.main:app --reload --port 8000`
- Prod: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Docker: Uses python:3.11-slim with tesseract-ocr installed
