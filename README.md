# INEC Election Results Agent 🇳🇬

AI-powered system for extracting Nigerian election results from the INEC IREV portal.

## Features

- **Web Scraping**: Automated navigation of INEC IREV portal with rate limiting
- **OCR Pipeline**: Dual-engine OCR using Tesseract and GPT-4 Vision
- **Data Extraction**: Intelligent parsing of election result sheets
- **Validation**: Vote sum validation with confidence scoring
- **Aggregation**: Ward, LGA, and State-level result aggregation
- **Multi-Agent System**: LangGraph-based orchestration for parallel processing
- **Dashboard**: Next.js frontend for browsing and exporting results

## Prerequisites

- Docker Desktop (for PostgreSQL and Redis)
- Python 3.11+
- Node.js 18+
- Tesseract OCR (optional, for local OCR)

## Quick Start

### 1. Start Docker Desktop

Make sure Docker Desktop is running on your machine.

### 2. Run the Project

```bash
./run-project.sh
```

This will:
- Start PostgreSQL and Redis containers
- Run database migrations
- Start the FastAPI backend (http://localhost:8000)
- Start the Next.js frontend (http://localhost:3000)

### Manual Setup

If you prefer to run services manually:

```bash
# Start database services
docker compose up -d

# Backend setup
cd backend
source .venv/bin/activate  # or use: .venv/bin/python
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend setup (in another terminal)
cd frontend
npm install
npm run dev
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agents/       # LangGraph multi-agent system
│   │   ├── api/v1/       # FastAPI endpoints
│   │   ├── core/         # Core business logic
│   │   │   ├── aggregator/   # Vote aggregation
│   │   │   ├── extractor/    # Data extraction
│   │   │   ├── ocr/          # OCR engines
│   │   │   └── scraper/      # Web scraping
│   │   ├── db/           # Database migrations
│   │   ├── models/       # SQLAlchemy models
│   │   └── workers/      # Celery background tasks
│   └── tests/
├── frontend/
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   ├── lib/              # Utilities and API client
│   └── types/            # TypeScript types
└── docker-compose.yml
```

## API Endpoints

- `GET /api/v1/elections/types` - List election types
- `GET /api/v1/elections/states` - List states
- `GET /api/v1/results` - List election results
- `GET /api/v1/aggregation/ward/{id}` - Ward aggregation
- `GET /api/v1/aggregation/lga/{id}` - LGA aggregation
- `POST /api/v1/jobs` - Start scraping job
- `POST /api/v1/export/csv` - Export to CSV
- `POST /api/v1/export/json` - Export to JSON

Full API documentation: http://localhost:8000/docs

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/inec_elections
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-api-key  # Required for GPT-4 Vision OCR
```

## License

MIT
