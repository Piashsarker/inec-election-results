# INEC Election Results Agent - Backend

AI-powered backend service for extracting Nigerian election results from the INEC IREV portal.

## Features

- Web scraping with Playwright for dynamic content
- OCR processing with Tesseract and GPT-4 Vision
- Async task processing with Celery and Redis
- PostgreSQL database with SQLAlchemy ORM
- LangGraph-based multi-agent orchestration
- RESTful API with FastAPI

## Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Tesseract OCR

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

4. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

5. Update `.env` with your configuration values.

## Running the Application

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Celery Worker

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── v1/
│   │   │   ├── elections.py    # Election endpoints
│   │   │   ├── results.py      # Results endpoints
│   │   │   ├── aggregation.py  # Aggregation endpoints
│   │   │   ├── jobs.py         # Job management endpoints
│   │   │   └── export.py       # Export endpoints
│   │   └── deps.py             # Dependency injection
│   ├── core/
│   │   ├── scraper/            # Web scraping components
│   │   ├── ocr/                # OCR processing
│   │   ├── extractor/          # Data extraction
│   │   └── aggregator/         # Vote aggregation
│   ├── models/                 # SQLAlchemy models
│   ├── db/
│   │   └── migrations/         # Alembic migrations
│   └── workers/                # Celery tasks
└── tests/                      # Test suite
```

## Testing

```bash
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=html
```

## License

MIT
