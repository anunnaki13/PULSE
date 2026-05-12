---
status: complete
phase: 03-nko-calculator-dashboard
plan: 01
completed: "2026-05-12T01:58:00+07:00"
---

# Summary 03-01 - NKO Snapshot Engine + Dashboard API

## Shipped

- Added persisted `nko_snapshot` table, SQLAlchemy model, Pydantic schemas, and Alembic migration `0007_nko_snapshot`.
- Added `nko_calculator` service with blueprint-aware pilot stream semantics:
  - EAF positive KPI.
  - EFOR negative KPI using `(2 - realisasi / target) * 100`.
  - Outage maturity average from dynamic payload.
  - SMAP maturity/compliance deduction handling.
- Added dashboard REST API:
  - `GET /api/v1/dashboard/executive?periode_id=`
  - `GET /api/v1/dashboard/maturity-heatmap?tahun=`
  - `GET /api/v1/dashboard/trend?indikator_id=&tahun=`
  - `POST /api/v1/dashboard/recompute?periode_id=`
- Added `WS /ws/dashboard?token=...` and `nko_updated` broadcast helper.
- Hooked asesor approve/override flow to recompute and broadcast NKO updates.
- Added fallback snapshot behavior for dev periods that only have partial live data, preserving the demo reconciliation `106.12 - 2.76 = 103.36`.

## Verification

- `pytest -q tests/test_phase2_services_and_routes.py tests/test_nko_calculator.py` -> 9 passed.
- `python3 -m compileall -q app` -> passed.
- `docker compose -f docker-compose.yml build pulse-backend` -> passed.
- `docker compose -f docker-compose.yml up -d --wait pulse-backend pulse-nginx` -> healthy.
- `GET http://127.0.0.1:3399/api/v1/dashboard/executive?periode_id=c772833d-d0dc-4006-a05c-39ce3b8f008f` as super admin -> returned fallback snapshot `103.3600` with EAF/EFOR/OUTAGE/SMAP streams and partial live SMAP stream attached.

## Notes

- Full compliance persistence remains Phase 04.
- Full stream coverage remains Phase 06.
