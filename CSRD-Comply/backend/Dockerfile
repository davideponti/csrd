FROM python:3.12-slim AS builder

WORKDIR /app

# Install system deps needed for psycopg2, pycairo, numpy, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev python3-dev \
    libcairo2-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# libpq needed at runtime for psycopg2
# libcairo2 (senza -dev) needed at runtime per pycairo
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev libcairo2 ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY backend/ .
COPY ai_engine/ ./ai_engine/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]