# PULSE — backend image. Multi-stage: builder installs deps from pyproject.toml,
# runtime is a slim python:3.11-slim with only the prefix + libpq + curl (for healthcheck).
# Plan 03 (backend skeleton) creates backend/app/, backend/alembic/, backend/pyproject.toml.

# -----------------------------------------------------------------------------
# Stage 1 — builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Plan 03 will create these. Copy now so Docker layer caches based on dependency
# manifests rather than full source. If pyproject.toml is missing at build time
# the build fails loudly — which is the correct signal that Plan 03 must land first.
COPY pyproject.toml ./
# Optional lockfile / README that pyproject may reference; non-fatal if absent.
COPY README.md* ./

# Install the project + production extras into a relocatable prefix.
RUN pip install --upgrade pip \
    && pip install --prefix=/install ".[prod]"


# -----------------------------------------------------------------------------
# Stage 2 — runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Runtime needs only libpq for asyncpg/psycopg + curl for the Docker healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 pulse \
    && useradd  --system --uid 1000 --gid 1000 --create-home pulse

# Pull installed packages from the builder stage.
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application sources (Plan 03 ships these).
COPY app/ ./app/
COPY alembic.ini* ./
COPY alembic/   ./alembic/
COPY entrypoint.sh ./entrypoint.sh

RUN chmod 0755 ./entrypoint.sh \
    && chown -R pulse:pulse /app

USER pulse

EXPOSE 8000

CMD ["./entrypoint.sh"]
