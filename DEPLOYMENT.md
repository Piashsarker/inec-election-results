# INEC Election Results Agent - Deployment Roadmap

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION SETUP                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Frontend   │     │   Backend    │     │   Database   │    │
│  │  Deno Deploy │────▶│    Render    │────▶│   Neon/      │    │
│  │  (Next.js)   │     │  (FastAPI)   │     │   Supabase   │    │
│  │  + Prisma    │     │              │     │  PostgreSQL  │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                              │                                   │
│                              │                                   │
│  ┌──────────────┐           │                                   │
│  │ Local Poller │───────────┘                                   │
│  │  (Your Mac)  │  Scraping + OCR                               │
│  │  Playwright  │  Jobs via API                                 │
│  └──────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Database Setup (Neon or Supabase)

### Option A: Neon PostgreSQL (Recommended)

1. Go to https://neon.tech and create account
2. Create new project → Get connection string
3. Connection string format:
   ```
   postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
   ```

### Option B: Supabase PostgreSQL

1. Go to https://supabase.com and create project
2. Go to Settings → Database → Connection string
3. Use the "URI" connection string

### Database Migration

Run migrations from your local machine:
```bash
cd backend
DATABASE_URL="postgresql://..." .venv/bin/alembic upgrade head
```

---

## Phase 2: Backend Deployment on Render

### 2.1 Prepare Backend for Render

Create `backend/render.yaml`:
```yaml
services:
  - type: web
    name: inec-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        sync: false
      - key: OPENAI_API_KEY
        sync: false
```

Create `backend/requirements.txt` (if not exists):
```bash
cd backend
.venv/bin/pip freeze > requirements.txt
```

### 2.2 Deploy to Render

1. Go to https://render.com → New → Web Service
2. Connect your GitHub repo
3. Configure:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   - `DATABASE_URL` = Your Neon/Supabase connection string
   - `ENVIRONMENT` = production
   - `OPENAI_API_KEY` = (optional, for GPT-4 Vision OCR)
   - `REDIS_URL` = (optional, use Upstash Redis if needed)

### 2.3 Update Backend Config

Update `backend/app/config.py` to support `DATABASE_URL`:
```python
import os
from urllib.parse import urlparse

# Support DATABASE_URL for cloud deployments
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Parse DATABASE_URL
    parsed = urlparse(DATABASE_URL)
    DB_HOST = parsed.hostname
    DB_PORT = parsed.port or 5432
    DB_NAME = parsed.path[1:]  # Remove leading /
    DB_USER = parsed.username
    DB_PASSWORD = parsed.password
```

---

## Phase 3: Frontend Migration to Deno Deploy + Prisma

### 3.1 Important: Architecture Decision

**Current frontend is Next.js (React)**. Deno Deploy works best with:
- Fresh framework (Deno-native)
- Or static sites

**Recommended approach**: Keep Next.js but deploy to Vercel (free tier) instead, OR migrate to Fresh.

If you want Deno Deploy specifically:

### 3.2 Option A: Deploy Next.js to Vercel (Easier)

1. Go to https://vercel.com
2. Import your GitHub repo
3. Set root directory to `frontend`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-render-backend.onrender.com`
5. Deploy

### 3.3 Option B: Migrate to Fresh + Prisma (Deno Deploy)

This requires rewriting the frontend. Create new Fresh project:

```bash
deno run -A -r https://fresh.deno.dev frontend-deno
```

Add Prisma for Deno:
```typescript
// frontend-deno/prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
  previewFeatures = ["deno"]
  output = "../generated/client"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
```

### 3.4 Prisma with Deno Deploy

```bash
# Install Prisma CLI
npm install prisma --save-dev

# Generate Prisma client for Deno
npx prisma generate --generator client
```

In your Deno code:
```typescript
import { PrismaClient } from "./generated/client/deno/edge.ts";

const prisma = new PrismaClient();

// Use in API routes
const results = await prisma.pollingUnitResult.findMany();
```

---

## Phase 4: Local Poller Setup

The scraping/OCR agent runs on your local machine and pushes data to the cloud backend.

### 4.1 Create Local Poller Script

Create `backend/local_poller.py`:
```python
#!/usr/bin/env python3
"""Local poller that scrapes INEC and pushes to cloud backend."""

import asyncio
import httpx
import os
from pathlib import Path

# Cloud backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "https://your-app.onrender.com")
API_KEY = os.getenv("API_KEY", "your-secret-key")

async def submit_result(result: dict):
    """Submit scraped result to cloud backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/v1/results",
            json=result,
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        return response.json()

async def run_scraping_job():
    """Run local scraping job."""
    from app.core.scraper.browser import BrowserManager
    from app.core.scraper.navigator import PortalNavigator
    from app.core.ocr.engine import OCREngine
    
    # Initialize components
    browser = BrowserManager()
    navigator = PortalNavigator(browser)
    ocr = OCREngine()
    
    # Scrape and process
    # ... your scraping logic ...
    
    # Submit results to cloud
    for result in results:
        await submit_result(result)

if __name__ == "__main__":
    asyncio.run(run_scraping_job())
```

### 4.2 Run Local Poller

```bash
cd backend
export BACKEND_URL="https://your-app.onrender.com"
export API_KEY="your-secret-key"
.venv/bin/python local_poller.py
```

---

## Phase 5: Environment Variables Summary

### Render (Backend)
```
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
ENVIRONMENT=production
OPENAI_API_KEY=sk-xxx (optional)
API_KEY=your-secret-for-local-poller
```

### Vercel/Deno Deploy (Frontend)
```
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
DATABASE_URL=postgresql://... (if using Prisma directly)
```

### Local Poller
```
BACKEND_URL=https://your-backend.onrender.com
API_KEY=your-secret-for-local-poller
OPENAI_API_KEY=sk-xxx (for OCR)
```

---

## Phase 6: Deployment Checklist

### Backend (Render)
- [ ] Create Neon/Supabase PostgreSQL database
- [ ] Run migrations: `alembic upgrade head`
- [ ] Create Render web service
- [ ] Set environment variables
- [ ] Deploy and verify `/docs` endpoint works

### Frontend (Vercel recommended)
- [ ] Create Vercel project
- [ ] Set `NEXT_PUBLIC_API_URL` environment variable
- [ ] Deploy and verify dashboard loads

### Local Poller
- [ ] Configure `BACKEND_URL` and `API_KEY`
- [ ] Test connection to cloud backend
- [ ] Run scraping job and verify data appears in dashboard

---

## Cost Estimates (Free Tiers)

| Service | Free Tier |
|---------|-----------|
| Render | 750 hours/month (sleeps after 15min inactivity) |
| Neon | 0.5 GB storage, 190 compute hours |
| Vercel | 100 GB bandwidth, unlimited deploys |
| Supabase | 500 MB database, 2 GB bandwidth |

---

## Quick Start Commands

```bash
# 1. Setup database
DATABASE_URL="postgresql://..." alembic upgrade head

# 2. Test backend locally with cloud DB
DATABASE_URL="postgresql://..." uvicorn app.main:app --reload

# 3. Deploy backend to Render (via GitHub push)
git push origin main

# 4. Deploy frontend to Vercel
cd frontend && vercel

# 5. Run local poller
BACKEND_URL="https://xxx.onrender.com" python local_poller.py
```
