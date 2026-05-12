# PULSE — Performance & Unit Live Scoring Engine
# Cross-platform DX entrypoint. Use under Git Bash on Windows or directly on Linux/macOS.
# Windows hosts without `make` should call `./scripts/dev.ps1 <verb>` (PowerShell fallback).

.PHONY: help up down build seed migrate test backup restore lint logs prod-env prod-check prod-smoke

help:
	@echo "PULSE — Developer verbs"
	@echo "  make up              Start all services (docker compose up -d --wait)"
	@echo "  make down            Stop and remove all services"
	@echo "  make build           Build all images"
	@echo "  make seed            Seed bidang + Konkin 2026 master data"
	@echo "  make migrate         Run Alembic migrations to head"
	@echo "  make test            Run backend pytest + frontend vitest"
	@echo "  make backup          Trigger backup script in pulse-backup sidecar"
	@echo "  make restore FILE=…  Restore from a backup file (gzipped pg_dump)"
	@echo "  make logs            Tail logs from all services"
	@echo "  make lint            Run ruff (backend) + eslint (frontend)"
	@echo "  make prod-env        Generate .env.production.generated"
	@echo "  make prod-check      Validate production readiness gates"
	@echo "  BASE_URL=… EMAIL=… PASSWORD=… [PERIODE_ID=…] make prod-smoke"
	@echo ""
	@echo "Windows users without make: ./scripts/dev.ps1 <verb>"

up:
	docker compose up -d --wait

down:
	docker compose down

build:
	docker compose build

seed:
	docker compose exec pulse-backend python -m app.seed

migrate:
	docker compose exec pulse-backend alembic upgrade head

test:
	docker compose exec pulse-backend pytest -x -q && cd frontend && pnpm exec vitest run --reporter=basic

backup:
	docker compose exec pulse-backup /scripts/backup.sh

restore:
	@[ -n "$$FILE" ] || (echo "Usage: make restore FILE=<backup.sql.gz>"; exit 2)
	docker compose exec -T pulse-backup /scripts/restore.sh "$$FILE"

logs:
	docker compose logs -f --tail=200

lint:
	cd backend && ruff check . ; cd ../frontend && pnpm run lint

prod-env:
	./scripts/generate-prod-env.sh

prod-check:
	./scripts/prod-readiness.sh

prod-smoke:
	./scripts/prod-smoke.sh
