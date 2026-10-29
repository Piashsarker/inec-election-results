FROM python:3.11-slim

# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies — includes Playwright OS deps + libpq for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client lib
    libpq-dev \
    gcc \
    # Playwright browser dependencies
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxshmfence1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only — smallest footprint)
RUN playwright install chromium --with-deps 2>/dev/null || true

# Copy application code
COPY . .

# Create runtime dirs
RUN mkdir -p logs data/result_sheets

# Non-root user for security
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Run with 4 Uvicorn workers in production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
