FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Setup non-root security user
RUN useradd -m -u 10001 appuser

# Copy dependency specifications
COPY pyproject.toml uv.lock ./

# Install Python dependencies into virtual environment
RUN uv sync --frozen --no-dev

# Copy application source code
COPY . .

# Adjust permissions for non-root user
RUN chown -R appuser:appuser /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
