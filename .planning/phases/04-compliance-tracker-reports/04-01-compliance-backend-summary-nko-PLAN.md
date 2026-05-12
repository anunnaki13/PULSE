---
status: planned
phase: 04-compliance-tracker-reports
plan: 01
requirements_addressed:
  - REQ-compliance-laporan-tracker
  - REQ-compliance-komponen
  - REQ-compliance-summary
---

# Plan 04-01 - Compliance Backend + NKO Integration

## Objective

Persist routine report and compliance component realization data, expose compliance APIs, compute capped deduction summary, and integrate that summary into the Phase 03 NKO snapshot service.

## Scope

- Add compliance report definition/submission models and migration.
- Seed the nine routine reports with default `0.039` deduction factors.
- Store `keterlambatan_hari` as generated column.
- Add compliance component and component realization models for PACA, Critical Event, ICOFR, and NAC.
- Add APIs:
  - `GET /compliance/laporan-definisi`
  - `POST /compliance/submissions`
  - `GET /compliance/submissions?periode_id=`
  - `GET /compliance/summary?periode_id=`
  - `GET /compliance/components`
  - `POST /compliance/component-realizations`
- Recompute NKO snapshot after compliance mutations.

## Verification

- Unit tests for delay and deduction math.
- Router registration tests.
- API smoke: Pengusahaan late 2 days returns deduction `0.078` in summary.
- Backend compile and Docker health.
