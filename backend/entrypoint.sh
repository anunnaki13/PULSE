#!/bin/sh
# PULSE backend entrypoint.
# RESEARCH.md Pitfall #2: "migrate THEN gunicorn" — Alembic must complete before
# any worker starts taking traffic, and dependents (pulse-db) must be healthy
# (enforced by compose `depends_on: condition: service_healthy`).

set -e

echo "[entrypoint] running alembic migrations..."
alembic upgrade head

echo "[entrypoint] starting gunicorn (4 × UvicornWorker on :8000)..."
exec gunicorn app.main:app \
     -k uvicorn.workers.UvicornWorker \
     -w 4 \
     -b 0.0.0.0:8000 \
     --access-logfile - \
     --error-logfile  -
