---
inclusion: fileMatch
fileMatchPattern: "backend/app/models/**,backend/app/db/**,backend/alembic.ini"
---

# Database Layer - PostgreSQL + SQLAlchemy

## Architecture
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0 (async with asyncpg)
- **Migrations**: Alembic 1.13
- **Pattern**: Repository pattern with async sessions

## Project Structure
```
backend/app/
├── models/
│   ├── __init__.py         # Exports all models
│   ├── base.py             # BaseModel with UUID pk + created_at
│   ├── election.py         # ElectionType, PoliticalParty, ElectionResult, PartyResult
│   ├── geography.py        # State, LGA, Ward, PollingUnit
│   └── job.py              # ScrapingJob, JobLog, FlaggedResult
├── db/
│   ├── __init__.py
│   ├── session.py          # Async engine + session factory
│   └── migrations/
│       ├── env.py          # Alembic environment (async)
│       ├── script.py.mako  # Migration template
│       └── versions/
│           ├── 001_initial_schema.py       # All tables
│           └── 002_aggregation_views.py    # SQL views for aggregation
└── alembic.ini             # Alembic configuration
```

## Data Model

### Geographic Hierarchy
```
State (36 + FCT)
  └── LGA (774)
      └── Ward (~8,000)
          └── PollingUnit (~176,000)
```

### Election Data
```
ElectionType ──┐
               ├── ElectionResult ── PartyResult[] ── PoliticalParty
PollingUnit ───┘         │
                         └── FlaggedResult
```

### Job Tracking
```
ScrapingJob ── JobLog[]
```

## Base Model (base.py)
```python
class BaseModel(DeclarativeBase):
    id: UUID (primary key, auto-generated)
    created_at: DateTime (server_default=now())
```

## Key Models

### Geography
- `State`: name, code, total_lgas
- `LGA`: state_id (FK), name, code, total_wards
- `Ward`: lga_id (FK), name, code, total_polling_units
- `PollingUnit`: ward_id (FK), name, code, delimitation

### Elections
- `ElectionType`: name, code (presidential, governorship, etc.)
- `PoliticalParty`: name, code (APC, PDP, LP, etc.)
- `ElectionResult`: election_type_id, polling_unit_id, accredited_voters, valid_votes, rejected_votes, confidence_score, source_image_path
- `PartyResult`: election_result_id, party_id, vote_count, percentage

### Jobs
- `ScrapingJob`: status, target scope, progress counters, timestamps
- `JobLog`: job_id, level, message, details (JSONB)
- `FlaggedResult`: election_result_id, reason, status, review_notes

## Session Management (session.py)
```python
from app.db.session import get_async_session

# Usage in FastAPI dependency:
async def get_db():
    async with get_async_session() as session:
        yield session
```

## Migrations
- Run: `alembic upgrade head`
- Create: `alembic revision --autogenerate -m "description"`
- Async engine configured in `migrations/env.py`
- Connection URL from `settings.database.async_url`

## Aggregation Views (002_aggregation_views.py)
- `ward_vote_aggregation` - Aggregates votes by ward
- `lga_vote_aggregation` - Aggregates votes by LGA
- Uses SQL views for efficient read queries

## Connection Configuration
- Sync URL: `postgresql://user:pass@host:port/db`
- Async URL: `postgresql+asyncpg://user:pass@host:port/db`
- Supports `DATABASE_URL` env var for cloud deployments
- Pool settings managed by SQLAlchemy defaults

## Constraints & Indexes
- Unique: election_type + polling_unit per result
- Unique: party + election_result per party_result
- Indexes on all foreign keys
- Geographic codes unique within parent scope
