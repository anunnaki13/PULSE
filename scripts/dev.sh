#!/usr/bin/env bash
# PULSE — Bash developer verbs
# Mirror of Makefile/dev.ps1 for hosts that prefer a plain shell script.
# Works under Git Bash on Windows, and directly on Linux/macOS.
#
# Usage:
#   ./scripts/dev.sh up
#   ./scripts/dev.sh seed
#   FILE=backup.sql.gz ./scripts/dev.sh restore

set -euo pipefail

show_help() {
    cat <<'EOF'
PULSE — Developer verbs (bash)
  ./scripts/dev.sh up              Start all services
  ./scripts/dev.sh down            Stop and remove all services
  ./scripts/dev.sh build           Build all images
  ./scripts/dev.sh seed            Seed bidang + Konkin 2026 master data
  ./scripts/dev.sh migrate         Run Alembic migrations to head
  ./scripts/dev.sh test            Run backend pytest + frontend vitest
  ./scripts/dev.sh backup          Trigger backup script in pulse-backup sidecar
  FILE=… ./scripts/dev.sh restore  Restore from a backup file
  ./scripts/dev.sh logs            Tail logs from all services
  ./scripts/dev.sh lint            Run ruff + eslint
  ./scripts/dev.sh prod-env        Generate .env.production.generated
  ./scripts/dev.sh prod-check      Validate production readiness gates
  BASE_URL=… EMAIL=… PASSWORD=… [PERIODE_ID=…] ./scripts/dev.sh prod-smoke
EOF
}

verb="${1:-help}"

case "$verb" in
    help)    show_help ;;
    up)      docker compose up -d --wait ;;
    down)    docker compose down ;;
    build)   docker compose build ;;
    seed)    docker compose exec pulse-backend python -m app.seed ;;
    migrate) docker compose exec pulse-backend alembic upgrade head ;;
    test)
        docker compose exec pulse-backend pytest -x -q
        ( cd frontend && pnpm exec vitest run --reporter=basic )
        ;;
    backup)  docker compose exec pulse-backup /scripts/backup.sh ;;
    restore)
        if [ -z "${FILE:-}" ]; then
            echo "Usage: FILE=<backup.sql.gz> $0 restore" >&2
            exit 2
        fi
        docker compose exec -T pulse-backup /scripts/restore.sh "$FILE"
        ;;
    logs)    docker compose logs -f --tail=200 ;;
    lint)
        ( cd backend  && ruff check . )
        ( cd frontend && pnpm run lint )
        ;;
    prod-env) ./scripts/generate-prod-env.sh ;;
    prod-check) ./scripts/prod-readiness.sh ;;
    prod-smoke) ./scripts/prod-smoke.sh ;;
    *)       show_help ;;
esac
