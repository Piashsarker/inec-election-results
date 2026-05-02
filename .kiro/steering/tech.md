# Tech Stack & Build System

## Backend (Python)

- **Runtime**: Python 3.11+
- **Framework**: FastAPI with Uvicorn
- **Database**: PostgreSQL 15 (async via asyncpg + SQLAlchemy 2.0)
- **Migrations**: Alembic
- **Task Queue**: Celery with Redis broker
- **Cache/Broker**: Redis 7
- **Web Scraping**: Playwright (browser automation)
- **OCR**: Tesseract (pytesseract) + OpenAI GPT-4 Vision
- **Image Processing**: OpenCV, Pillow, NumPy
- **AI/Agent Framework**: LangGraph, LangChain, langchain-openai
- **Configuration**: Pydantic Settings with .env files
- **HTTP Client**: httpx
- **Data Export**: Pandas

### Dev Dependencies
- **Testing**: pytest, pytest-asyncio, pytest-cov, hypothesis (property-based testing)
- **Linting**: ruff (line-length=100, target py311)
- **Formatting**: black (line-length=100, target py311)
- **Type Checking**: mypy (strict mode)

## Frontend (TypeScript)

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS 3.4 with CSS variables for theming
- **UI Components**: Radix UI primitives + custom components (shadcn/ui pattern)
- **Charts**: Recharts
- **Tables**: TanStack React Table
- **Icons**: Lucide React
- **Utilities**: clsx, tailwind-merge, class-variance-authority

## Infrastructure

- **Containerization**: Docker + Docker Compose
- **Database**: PostgreSQL 15 Alpine
- **Cache**: Redis 7 Alpine
- **Frontend Hosting**: Vercel
- **Backend Hosting**: Render (or VPS)

## Common Commands

### Backend
```bash
cd backend

# Activate virtual environment
source .venv/bin/activate

# Start dev server
uvicorn app.main:app --reload --port 8000

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Lint
ruff check .

# Format
black .

# Type check
mypy app/
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

### Docker
```bash
# Start infrastructure (PostgreSQL + Redis)
docker compose up -d

# Start full production stack
docker compose -f docker-compose.prod.yml up -d

# Stop all services
docker compose down
```

### Playwright
```bash
# Install browsers (required once)
playwright install
```
