---
inclusion: auto
---

# Development Specification & Issue-Driven Workflow

## Issue-Driven Development

All development work should be traceable to GitHub issues. Follow these guidelines:

### Before Starting Work
1. **Check open issues** — Pull the latest GitHub issues to see if the current task relates to an existing issue.
2. **Reference issues** — When implementing a fix or feature tied to an issue, reference it (e.g., "Fixes #12" or "Relates to #5") in commit messages and PR descriptions.
3. **Create issues for new work** — If a task doesn't have a corresponding issue, suggest creating one before or during implementation.

### Issue-to-Spec Workflow
When picking up a GitHub issue for development:
1. **Analyze the issue** — Understand the requirements, acceptance criteria, and any linked discussions.
2. **Map to specs** — Check if a Kiro spec exists under `.kiro/specs/` that covers this work. If not, consider creating one for non-trivial features.
3. **Break into tasks** — Decompose the issue into implementation tasks with clear deliverables.
4. **Implement incrementally** — Work through tasks one at a time, verifying each before moving on.

## Development Standards

### Code Quality Gates
Before considering any task complete:
- [ ] Code compiles/builds without errors
- [ ] Existing tests pass (`pytest` for backend, `npm run build` for frontend)
- [ ] New code follows project conventions (ruff/black for Python, ESLint for TypeScript)
- [ ] Type annotations are present (Python type hints, TypeScript strict mode)
- [ ] Error handling follows the custom exception hierarchy in `backend/app/core/errors.py`

### Backend Development (Python/FastAPI)
- Use async/await for all database operations and HTTP calls
- Follow the app factory pattern — register new routes in `backend/app/main.py`
- Place business logic in `backend/app/core/`, not in API route handlers
- All new models inherit from `BaseModel` in `backend/app/models/base.py`
- Use dependency injection via FastAPI `Depends` for shared resources
- Configuration goes through `backend/app/config.py` Settings class
- Use structured logging via `backend/app/core/logging.py`

### Frontend Development (Next.js/TypeScript)
- Use the App Router pattern — pages go in `frontend/app/`
- Reusable UI components follow the shadcn/ui pattern in `frontend/components/ui/`
- Shared types live in `frontend/types/index.ts`
- API calls go through `frontend/lib/api.ts`
- Use Tailwind CSS with the project's CSS variable theming system
- Ensure components are accessible (ARIA attributes, keyboard navigation)

### Database Changes
- Always create Alembic migrations for schema changes
- Migration files go in `backend/app/db/migrations/versions/`
- Test migrations with `alembic upgrade head` and `alembic downgrade -1`
- Never modify existing migration files — create new ones

### Git Workflow
- Branch from `main` for all work
- **Branch naming**: `issue/#<issue_number>` (e.g., `issue/#1`, `issue/#23`)
  - If no specific issue applies: `issue/#0-<short-description>`
- Commit messages: `type(scope): description (#issue)` (e.g., `feat(api): add pagination to results endpoint (#1)`)
- One logical change per commit
- Push with `-u` flag to set upstream tracking
- Create PRs with:
  - Concise title (under 70 chars)
  - Body with: summary of changes, what was tested, and issue reference (`Closes #<number>` or `Relates to #<number>`)
- PRs always target `main` branch

## Spec Creation Guidelines

When creating a new spec for a feature or issue:

### Requirements Document
- List functional requirements as numbered items
- Include acceptance criteria for each requirement
- Note any constraints or dependencies
- Reference the GitHub issue number

### Design Document
- Describe the technical approach
- List files to be created or modified
- Define API contracts (request/response shapes) if applicable
- Note any new dependencies needed

### Task Breakdown
- Each task should be independently verifiable
- Order tasks by dependency (foundational work first)
- Include validation steps in each task
- Estimate complexity (small/medium/large)
