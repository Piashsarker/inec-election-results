# Manual Scraping Guide

Step-by-step instructions to run the INEC IREV portal scraper locally.

## Prerequisites

1. **Python 3.11+** installed
2. **PostgreSQL** and **Redis** running (via Docker or locally)
3. **Tesseract OCR** installed on your system
4. **OpenAI API key** (for GPT-4 Vision fallback on low-quality images)

## One-Time Setup

### 1. Create and activate the virtual environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright browsers

This downloads the Chromium binary that the scraper uses to automate the INEC portal:

```bash
playwright install chromium
```

> If you get `zsh: command not found: playwright`, make sure your venv is activated first.

### 4. Install Tesseract OCR (macOS)

```bash
brew install tesseract
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Description | Required |
|----------|-------------|----------|
| `BACKEND_URL` | URL of the backend API (default: `http://localhost:8000`) | For submitting results |
| `API_KEY` | API key for backend authentication | For submitting results |
| `OPENAI_API_KEY` | OpenAI key for GPT-4 Vision OCR | For low-quality images |
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | PostgreSQL connection | If running full backend |
| `REDIS_HOST` / `REDIS_PORT` | Redis connection | If running full backend |

### 6. Start infrastructure (if submitting to local backend)

```bash
# From project root
docker compose up -d   # Starts PostgreSQL + Redis

# Then start the backend API
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Running the Scraper

### Basic usage

```bash
cd backend
source .venv/bin/activate
python local_poller.py --election presidential --state lagos
```

### Command-line options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--election` | `-e` | `presidential` | Election type: `presidential`, `gubernatorial`, `senatorial`, `house_of_reps`, `state_assembly` |
| `--state` | `-s` | _(all states)_ | Target state (e.g., `lagos`, `kano`, `rivers`) |
| `--lga` | `-l` | _(all LGAs)_ | Target Local Government Area |
| `--limit` | `-n` | `10` | Maximum number of polling units to scrape |
| `--dry-run` | | _(off)_ | Scrape but don't submit results to backend |

### Examples

```bash
# Scrape 5 presidential results from Lagos (dry run, no backend needed)
python local_poller.py -e presidential -s lagos -n 5 --dry-run

# Scrape gubernatorial results from Kano, Nassarawa LGA
python local_poller.py -e gubernatorial -s kano -l nassarawa -n 20

# Scrape all available presidential results from Rivers state
python local_poller.py -e presidential -s rivers -n 100
```

### Dry run mode

Use `--dry-run` to test scraping without needing the backend running. Results are printed to stdout as JSON:

```bash
python local_poller.py -e presidential -s lagos -n 3 --dry-run
```

## How It Works

1. **Browser launch** — Playwright opens a headless Chromium browser
2. **Portal navigation** — Navigates to `https://www.inecelectionresults.ng/elections/types`
3. **Selection** — Selects the election type, state, and LGA
4. **Download** — Downloads result sheet images from each polling unit
5. **OCR** — Extracts text using Tesseract (high-quality) or GPT-4 Vision (low-quality)
6. **Parsing** — Structures the extracted text into party names, vote counts, totals
7. **Validation** — Checks vote sums and assigns confidence scores
8. **Submission** — Sends results to the backend API (unless `--dry-run`)

## Troubleshooting

### `BrowserType.launch: Executable doesn't exist`

Playwright browsers aren't installed. Run:

```bash
source .venv/bin/activate
playwright install chromium
```

### `zsh: command not found: playwright`

Your virtual environment isn't activated:

```bash
source .venv/bin/activate
```

### `Cannot reach backend`

Either the backend isn't running or `BACKEND_URL` is wrong. Use `--dry-run` to skip backend submission, or start the backend:

```bash
docker compose up -d
uvicorn app.main:app --reload --port 8000
```

### Timeout errors / slow scraping

The INEC portal can be slow. Adjust these in `.env`:

```env
SCRAPING_REQUEST_DELAY_SECONDS=2.0      # Increase delay between requests
SCRAPING_DOWNLOAD_TIMEOUT_SECONDS=60    # Increase timeout
SCRAPING_MAX_RETRIES=5                  # Number of retry attempts
```

### Low confidence / bad OCR results

- Ensure Tesseract is installed: `tesseract --version`
- Set a valid `OPENAI_API_KEY` in `.env` for GPT-4 Vision fallback
- Adjust `OCR_CONFIDENCE_THRESHOLD` in `.env` (default: 0.8)
