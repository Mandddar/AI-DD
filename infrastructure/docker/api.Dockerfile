# ───────────────────────────────────────────────────────
# API Dockerfile — multi-stage, optimised for layer caching
# ───────────────────────────────────────────────────────

# ── Stage 1: Dependencies ────────────────────────────
FROM python:3.12-slim AS deps

WORKDIR /app

# System libs needed by psycopg, pytesseract, pymupdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# uv for fast installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy lock + project definition first (cache layer when deps unchanged)
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: Runtime ─────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime-only system libs (no gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tesseract-ocr tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv needed at runtime to invoke `uv run`
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy pre-built virtualenv from deps stage
COPY --from=deps /app/.venv /app/.venv
COPY --from=deps /app/pyproject.toml /app/uv.lock /app/.python-version /app/

# Copy application code
COPY . .

# Uploads directory
RUN mkdir -p /app/uploads

# Non-root user
RUN adduser --disabled-password --gecos "" --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
