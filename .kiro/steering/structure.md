# Project Structure

## Top-Level Layout

```
├── backend/          # Python FastAPI backend
├── frontend/         # Next.js TypeScript frontend
├── docker-compose.yml        # Dev infrastructure (Postgres + Redis)
├── docker-compose.prod.yml   # Production deployment
└── .kiro/            # Kiro configuration and specs
```

## Backend (`backend/`)

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory (create_app)
│   ├── config.py            # Pydantic Settings (centralized config)
│   ├── agents/              # LangGraph multi-agent system
│   │   ├── graph.py         # Workflow state & StateGraph definition
│   │   ├── orchestrator.py  # Job coordination, checkpointing, pause/resume
│   │   ├── navigator.py     # Portal navigation agent
│   │   ├── processor.py     # OCR + extraction agent
│   │   ├── validator.py     # Data validation agent
│   │   └── pool.py          # Agent pool management
│   ├── api/
│   │   ├── deps.py          # Shared FastAPI dependencies
│   │   └── v1/              # Versioned API endpoints
│   │       ├── elections.py # Election type/state listing
│   │       ├── results.py   # Result queries
│   │       ├── aggregation.py # Ward/LGA/State aggregation
│   │       ├── jobs.py      # Scraping job management
│   │       └── export.py    # CSV/JSON export
│   ├── core/                # Business logic (no framework deps)
│   │   ├── aggregator/      # Vote aggregation service
│   │   ├── extractor/       # Data extraction (parser + validator)
│   │   ├── ocr/             # OCR engines (tesseract, vision, preprocessing)
│   │   ├── scraper/         # Web scraping (browser, navigator, downloader)
│   │   ├── errors.py        # Custom exception hierarchy
│   │   └── logging.py       # Structured logging setup
│   ├── db/
│   │   ├── session.py       # Async SQLAlchemy session factory
│   │   └── migrations/      # Alembic migrations
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── base.py          # Base model (UUID PK + timestamps)
│   │   ├── election.py      # ElectionType, PoliticalParty, ElectionResult, PartyResult
│   │   ├── geography.py     # State, LGA, Ward, PollingUnit
│   │   └── job.py           # ScrapingJob, JobLog, FlaggedResult
│   └── workers/             # Celery background tasks
│       ├── celery_app.py    # Celery app configuration
│       └── tasks.py         # Task definitions
├── tests/                   # pytest test suite
├── data/result_sheets/      # Downloaded result sheet images
├── logs/                    # Application logs
├── pyproject.toml           # Project metadata + tool config
├── requirements.txt         # Pinned dependencies
├── alembic.ini              # Alembic configuration
└── Dockerfile               # Backend container image
```

## Frontend (`frontend/`)

```
frontend/
├── app/                     # Next.js App Router pages
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home/dashboard page
│   ├── elections/           # Election browsing pages
│   ├── results/             # Result detail pages
│   └── aggregation/         # Aggregation views
├── components/
│   ├── ui/                  # Reusable UI primitives (shadcn/ui pattern)
│   ├── charts/              # Recharts visualization components
│   ├── tables/              # Data table components
│   └── forms/               # Form components
├── lib/
│   ├── api.ts               # Backend API client
│   ├── utils.ts             # Utility functions (cn helper, etc.)
│   └── theme.tsx            # Theme provider
├── types/
│   └── index.ts             # Shared TypeScript type definitions
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── Dockerfile
```

## Key Architectural Patterns

- **Backend**: App factory pattern (`create_app()`), dependency injection via FastAPI `Depends`, async-first database access
- **Models**: All models inherit from `BaseModel` which provides UUID primary key + `created_at` timestamp
- **Config**: Single `Settings` class aggregates sub-configs (database, redis, scraping, ocr, openai, celery, logging) — all driven by env vars
- **API versioning**: Routes under `/api/v1/` prefix
- **Agent workflow**: LangGraph `StateGraph` with typed `AgentState` dict flowing through nodes (navigate → download → preprocess → ocr → extract → validate → store/flag)
- **Frontend**: Path alias `@/*` maps to project root; CSS variables for theming; component composition with Radix primitives
