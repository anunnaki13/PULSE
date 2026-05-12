---
status: planned
phase: 03-nko-calculator-dashboard
plan: 01
title: nko-snapshot-engine-dashboard-api
requirements_addressed:
  - REQ-nko-calc-engine
  - REQ-nko-aggregation-rules
  - REQ-nko-realtime-ws
  - REQ-dashboard-executive
  - REQ-dashboard-heatmap
  - REQ-dashboard-trend
depends_on:
  - Phase 02 complete
---

# Plan 03-01 - NKO Snapshot Engine + Dashboard API

## Objective

Build the backend scoring core for Phase 03: persist NKO snapshots, calculate the four pilot streams with blueprint-aware formulas, expose dashboard API payloads, and broadcast live dashboard updates when approved assessment values change.

## Scope

- Add `nko_snapshot` model, schema, Alembic migration, and indexes for periode/current snapshot lookup.
- Implement a calculation service that normalizes Phase 2 approved assessment data into pilar, indikator, stream, and formula breakdowns.
- Implement pilot stream calculators:
  - EAF positive KPI: `(realisasi / target) * 100`, percent unit.
  - EFOR negative KPI: `(2 - (realisasi / target)) * 100`, percent unit.
  - Outage maturity: area/sub-area average from ML payload, level 0-4 unit.
  - SMAP compliance/maturity: tracked separately with compliance/pengurang-ready fields.
- Implement aggregation helpers for missing/tidak-dinilai cases required by `REQ-nko-aggregation-rules`.
- Add REST endpoints:
  - `GET /dashboard/executive?periode_id=`
  - `GET /dashboard/maturity-heatmap?tahun=`
  - `GET /dashboard/trend?indikator_id=&tahun=`
  - `POST /dashboard/recompute?periode_id=` admin/super-admin maintenance hook.
- Add `WS /ws/dashboard?token=...` and publish `nko_updated` messages after recompute.
- Hook recompute after asesor approve/override in assessment review flow.

## Implementation Notes

- Persist both final totals and breakdown JSONB. The frontend needs drilldown and formula trace, so do not store only `nko_total`.
- Treat compliance deduction as a first-class breakdown field even if Phase 04 owns the full compliance tracker.
- Keep dummy fallback generation in backend only for empty dev periods. Mark fallback payloads with `source: "fallback"` so the UI can label them.
- Reuse existing auth and WebSocket token patterns from Phase 2 notification implementation.
- Avoid adding Phase 04 compliance tables in this plan.

## Verification

- Backend tests for model import, migration metadata, and snapshot persistence.
- Unit tests for pilot stream formulas and aggregation fallbacks.
- Router tests for dashboard endpoints with authorized and unauthorized roles.
- WebSocket test or service-level broadcast test for `nko_updated`.
- Container health after migration and rebuild:
  - `docker compose -f docker-compose.yml build pulse-backend`
  - `docker compose -f docker-compose.yml up -d --wait pulse-backend pulse-nginx`
  - `curl http://127.0.0.1:3399/api/v1/health`

## Acceptance Checks

- A Phase 2 asesor approval recomputes and persists a current `nko_snapshot`.
- `GET /dashboard/executive?periode_id=` returns NKO total, gross pilar total, compliance deduction, pilar cards, pilot stream cards, recommendation summary, and formula ledger.
- Worked example can reconcile gross `106.12` minus compliance `2.76` to NKO `103.36` in deterministic fixture or seeded demo data.
- Dashboard read routes are available to `manajer_unit`, `super_admin`, and `viewer`; write/recompute maintenance route is admin-only.

## Deferred

- Full compliance tracker integration stays in Phase 04.
- Full stream inventory and HCR/OCR coverage stay in Phase 06.
