# Product Overview

INEC Election Results Agent is an AI-powered system for extracting Nigerian election results from the INEC IREV (Independent National Electoral Commission - INEC Result Viewing) portal.

## What It Does

- Scrapes election result sheet images from the INEC IREV portal
- Performs OCR on result sheet images using a dual-engine approach (Tesseract for high-quality images, GPT-4 Vision for low-quality)
- Extracts structured data (party names, vote counts, totals) from OCR output
- Validates extracted data (vote sum checks, confidence scoring)
- Aggregates results at ward, LGA, and state levels
- Provides a dashboard for browsing, filtering, and exporting results

## Key Domain Concepts

- **Geographic hierarchy**: State → LGA (Local Government Area) → Ward → Polling Unit
- **Election types**: Presidential, Gubernatorial, Senatorial, House of Representatives, State Assembly
- **Result sheets**: Physical paper documents photographed and uploaded to the INEC portal
- **IREV portal**: https://www.inecelectionresults.ng — the official results viewing portal

## Multi-Agent Architecture

The system uses a LangGraph-based multi-agent workflow:
1. **Navigator Agent** — traverses the portal hierarchy and downloads result sheets
2. **Processor Agent** — handles image preprocessing, OCR, and data extraction
3. **Validator Agent** — validates extracted data and flags anomalies
4. **Orchestrator Agent** — coordinates work distribution, checkpointing, and job management
