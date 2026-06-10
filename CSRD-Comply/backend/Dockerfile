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

# Runtime deps for psycopg2, pycairo, xhtml2pdf, health checks
# ⚠️ On Debian Trixie, libgdk-pixbuf2.0-0 was renamed to libgdk-pixbuf-2.0-0
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY backend/ .
COPY ai_engine/ ./ai_engine/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
