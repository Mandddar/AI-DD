FROM python:3.12-slim

WORKDIR /app

# System dependencies: PostgreSQL client, Tesseract OCR engine
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project definition and install dependencies
COPY pyproject.toml .python-version ./
RUN uv sync --no-dev --no-install-project

COPY . .

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
