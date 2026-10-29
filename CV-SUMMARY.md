# INEC Election Results Agent — Condensed CV Entry

*AI document-intelligence system for extracting structured election results from photographs of Nigerian result sheets.*

**Stack:** Python, GPT-4 Vision, Tesseract, OpenCV, LangGraph, FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery/Redis, Playwright, Next.js 14 / TypeScript

---

## One-liner
Built an end-to-end AI system that turns photos of election result sheets into validated, structured, aggregated data — pairing a dual-engine OCR pipeline (Tesseract + GPT-4 Vision) with a LangGraph multi-agent workflow and an async FastAPI/PostgreSQL backend.

---

## CV bullets (condensed — use all 5 or trim to 3)

- Built a **dual-engine OCR pipeline** (Tesseract + GPT-4 Vision) with an **OpenCV preprocessing stack** (deskew, denoise, CLAHE) and **adaptive, cost-aware engine selection** driven by a computed image-quality score, with cross-engine fallback; validated end-to-end on real result-sheet photographs.
- Designed a **LangGraph multi-agent workflow** (navigate → download → OCR → extract → validate → store/flag) with an **async orchestrator** providing concurrency control, checkpointing, and pause/resume for long-running jobs.
- Implemented a **confidence-scoring and domain-constrained validation engine** (vote-sum reconciliation, plausibility bounds, anomaly detection) that flags low-reliability extractions for **human-in-the-loop** review.
- Engineered an **async FastAPI + SQLAlchemy 2.0 + PostgreSQL** backend with Alembic migrations, a **Celery/Redis** task queue, and hierarchical Ward → LGA → State aggregation behind a versioned REST API.
- Delivered a **Next.js 14 / TypeScript** dashboard with a hand-built, keyboard-accessible **interactive SVG map of Nigeria**, Recharts visualizations, and CSV/JSON export.

---

## Core skills

**AI/ML:** multimodal LLMs (GPT-4 Vision), document AI / visual information extraction, adaptive model routing, confidence estimation, uncertainty-aware human-in-the-loop, domain-constrained output verification.

**Agentic AI:** LangGraph state graphs, multi-agent orchestration, checkpointing & resumable workflows.

**Computer vision / OCR:** OpenCV (deskew, denoise, CLAHE, thresholding), image-quality assessment, Tesseract, table/grid detection.

**Systems:** async Python, FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, Celery + Redis, Playwright automation (rate limiting, backoff retry), Docker.

**Frontend/dataviz:** TypeScript, Next.js 14, React, Recharts, TanStack Table, interactive SVG mapping, accessibility.

**Practice:** layered architecture, pytest, empirical validation on real data, mypy/ruff/black.

---

## Why it reads as PhD / R&D AI-engineer level
Multimodal extraction on degraded real-world imagery; a difficulty-based routing policy trading accuracy against cost; principled uncertainty handling with human-in-the-loop; verification of model output against structured domain rules; and empirical validation on real data with honest error-mode analysis.

---

## Accuracy guardrails (for interviews)
- Live portal HTML parsing is **stubbed** (browser/retry/download layer is real) — say *"architected for large-scale concurrent scraping,"* not *"scraped nationwide."*
- Demonstrated scale: **one ward, 17 polling units** (Osun 2026 gubernatorial).
- **No property-based (hypothesis) tests** — do not claim them.
- **LangGraph** is genuinely exercised; **LangChain** is present but the LLM is called directly via the OpenAI client.
