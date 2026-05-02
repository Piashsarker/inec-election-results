---
inclusion: fileMatch
fileMatchPattern: "frontend/**"
---

# Frontend Layer - INEC Election Results Dashboard

## Architecture
- **Framework**: Next.js 14 (App Router) with React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom theme (dark/light mode)
- **UI Components**: Radix UI primitives + custom components
- **Charts**: Recharts for data visualization
- **Tables**: @tanstack/react-table for data tables
- **Icons**: lucide-react

## Project Structure
```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout with navigation + ThemeProvider
│   ├── page.tsx            # Dashboard home
│   ├── elections/          # Election browsing (type → state → LGA → ward)
│   ├── results/            # Results listing and detail views
│   └── aggregation/        # Aggregated results with charts
├── components/
│   ├── charts/             # Recharts components (PartyBarChart, VoteDistributionPie, TrendLineChart)
│   ├── ui/                 # Shared UI components (ExportCenter, JobMonitor)
│   ├── forms/              # Form components
│   └── tables/             # Table components
├── lib/
│   ├── api.ts              # API client (fetch wrapper for backend)
│   ├── theme.tsx           # ThemeProvider context (light/dark)
│   └── utils.ts            # Utility functions (cn helper)
└── types/
    └── index.ts            # TypeScript interfaces for all data models
```

## Key Patterns
- Client components use `'use client'` directive
- API calls go through `lib/api.ts` which wraps fetch with error handling
- API base URL configured via `NEXT_PUBLIC_API_URL` environment variable
- Theme managed via React Context in `lib/theme.tsx`
- CSS utility function `cn()` combines clsx + tailwind-merge

## Data Types (types/index.ts)
- `ElectionResult` - Polling unit result with party votes
- `AggregatedResult` - Ward/LGA/State level aggregation
- `ScrapingJob` - Job tracking with status
- `PartyResult` - Individual party vote count
- Geographic hierarchy: `State` → `LGA` → `Ward` → `PollingUnit`

## API Client (lib/api.ts)
- Base URL: `NEXT_PUBLIC_API_URL` or `http://localhost:8000/api/v1`
- Endpoints: elections, results, aggregation, jobs, export
- All responses typed with TypeScript interfaces

## Build & Deploy
- Build: `npm run build` (outputs standalone for Docker)
- `next.config.js` has `output: 'standalone'` for containerized deployment
- Docker: multi-stage build (builder → runner with standalone output)

## Conventions
- Use Tailwind utility classes, avoid custom CSS
- Components use semantic HTML with ARIA attributes
- Dark mode via CSS variables (bg-background, text-foreground, etc.)
- Responsive design with Tailwind breakpoints (md:, lg:)
