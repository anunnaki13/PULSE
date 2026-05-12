---
status: blocked
phase: 06-stream-coverage-hcr-golive
plan: 05
checked_at: "2026-05-12T23:41:00.000+07:00"
---

# Phase 06 Production Checklist

## Passed Locally

- [x] `docker compose -f docker-compose.yml config --quiet` passed.
- [x] All compose services healthy after recreate:
  - `pulse-db`
  - `pulse-redis`
  - `pulse-backend`
  - `pulse-frontend`
  - `pulse-nginx`
  - `pulse-backup`
- [x] Postgres is internal-only. Docker inspect shows `5432/tcp` has no host binding.
- [x] Only `pulse-nginx` publishes the app port: `0.0.0.0:3399->80/tcp`.
- [x] Docker log rotation configured and applied: `json-file`, `max-size=10m`, `max-file=5`.
- [x] Backup sidecar is running with a DB healthcheck.
- [x] Nginx WebSocket connection cap added for `/ws/` via `limit_conn`.
- [x] Manual backup succeeded: `/backups/pulse-20260512T074046Z.sql.gz`.
- [x] Restore drill succeeded into temporary database `pulse_restore_probe`; restored public tables: 25.
- [x] Temporary restore database was dropped after the drill.
- [x] Production readiness checker added:
  - `./scripts/dev.ps1 prod-check`
  - `./scripts/dev.sh prod-check`
- [x] Readiness checker correctly fails current local `.env` because production secrets and OpenRouter config are not provisioned yet.
- [x] Production env generator added:
  - `./scripts/dev.ps1 prod-env`
  - `./scripts/dev.sh prod-env`
  - `make prod-env`
- [x] Production env generator verified on Bash and PowerShell using temporary files; generated candidates pass readiness checks when production values are present.
- [x] Production smoke scripts added:
  - `./scripts/dev.ps1 prod-smoke`
  - `./scripts/dev.sh prod-smoke`
  - `make prod-smoke`
- [x] Production smoke scripts verified on Bash and PowerShell against the active local stack, including dashboard and PDF export when `PERIODE_ID` is provided.
- [x] Local smoke re-run on 2026-05-12 23:41 WIB:
  - `health_detail_status=ok`
  - `ai_mode=mock`
  - `dashboard_nko=2.2500`
  - `report_pdf_bytes=1138`
- [x] Go-live runbook created: `06-GO-LIVE-RUNBOOK.md`.
- [x] `/api/v1/health/detail` passed:
  - DB ok
  - Redis ok
  - AI available in mock mode
- [x] Pedoman RAG table seeded: `pedoman_chunks=5`.
- [x] Phase 06 final API smoke passed; see `06-FINAL-UAT.md`.

## Production Blockers

- [ ] Rotate `.env` secrets before go-live:
  - `APP_SECRET_KEY` is present and long enough but still default-like.
  - `JWT_SECRET_KEY` is present and long enough but still default-like.
  - `POSTGRES_PASSWORD` is too short/default-like.
  - `INITIAL_ADMIN_PASSWORD` is too short/default-like.
- [ ] Provision OpenRouter production key and confirm quota.
  - `OPENROUTER_API_KEY` is empty locally.
  - `AI_MOCK_MODE=true`; production must set `AI_MOCK_MODE=false`.
- [ ] Provision SSL certificate for the production domain.
- [ ] Apply VPS firewall policy: allow only SSH plus app ports (`22`, `3399` or `443`, depending on deployment mode).
- [ ] Configure external health monitoring against `/api/v1/health` or `/api/v1/health/detail`.

Run `./scripts/dev.ps1 prod-check` on Windows or `./scripts/dev.sh prod-check` in WSL after provisioning the production `.env`. The command must pass before Phase 06 can be closed for go-live.

Use `./scripts/dev.ps1 prod-env` or `./scripts/dev.sh prod-env` to create a strong-secret production env candidate, then review and install it on the production host.

## Handover Notes

- Local dev URL remains `http://127.0.0.1:3399/`.
- Production should run with `docker compose -f docker-compose.yml up -d --wait` so `docker-compose.override.yml` does not enable dev reload/HMR mode.
- Keep mock fallback code enabled, but do not run production with `AI_MOCK_MODE=true`.
