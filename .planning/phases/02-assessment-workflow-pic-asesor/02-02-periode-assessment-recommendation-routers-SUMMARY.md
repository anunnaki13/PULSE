---
phase: 02-assessment-workflow-pic-asesor
plan: 02
subsystem: api
tags: [fastapi, sqlalchemy, csrf, rbac, workflow, recommendation]
requires:
  - phase: 02-assessment-workflow-pic-asesor
    provides: Phase 2 models, schemas, Alembic chain 0004-0006
provides:
  - Periode lifecycle router and FSM
  - Assessment session router for PIC and asesor flows
  - Recommendation router with owner resolution and lifecycle guards
  - Phase 2 service layer for pencapaian, session creation, and carry-over
affects: [02-03-audit-middleware-notifications-websocket, frontend-phase-02]
tech-stack:
  added: []
  patterns: [audit tag on mutating routes, service-layer owner resolution, last-write-wins autosave]
key-files:
  created:
    - backend/app/services/periode_fsm.py
    - backend/app/services/recommendation_fsm.py
    - backend/app/services/session_creator.py
    - backend/app/services/carry_over.py
    - backend/app/services/pencapaian.py
    - backend/app/services/recommendation_create.py
    - backend/app/routers/periode.py
    - backend/app/routers/assessment_session.py
    - backend/app/routers/recommendation.py
    - backend/tests/test_phase2_services_and_routes.py
  modified:
    - backend/app/schemas/assessment.py
key-decisions:
  - "Kept auto-save last-write-wins and server-authoritative pencapaian in the backend service layer."
  - "Resolved recommendation owners in a dedicated service instead of schema validators to preserve pure validation boundaries."
patterns-established:
  - "Every mutating Phase 2 route carries an audit:* tag for Plan 02-03 middleware."
  - "PIC scoping is enforced in route helpers using bidang_id or aggregate membership rows."
requirements-completed:
  - REQ-periode-lifecycle
  - REQ-self-assessment-kpi-form
  - REQ-self-assessment-ml-form
  - REQ-auto-save
  - REQ-pic-actions
  - REQ-asesor-review
  - REQ-recommendation-create
  - REQ-recommendation-lifecycle
duration: 40min
completed: 2026-05-11
---

# Phase 02 Plan 02: Periode, Assessment, Recommendation Routers Summary

**Periode lifecycle, PIC self-assessment, asesor review, and recommendation lifecycle APIs on top of the new Phase 2 schema.**

## Accomplishments

- Added `periode`, `assessment_session`, and `recommendation` routers under `/api/v1`.
- Added FSM and service helpers for periode transitions, recommendation transitions, pencapaian calculation, session creation, carry-over, and owner resolution.
- Preserved `link_eviden` as URL-only in OpenAPI across request and public DTOs.
- Registered audit tags on mutating Phase 2 routes so the next audit middleware layer has stable entity mapping.

## Endpoint Contract

- `GET/POST/PATCH /api/v1/periode`, `POST /api/v1/periode/{id}/transition`, `GET /api/v1/periode/{id}/carry-over-summary`
- `GET /api/v1/assessment/sessions`, `GET /api/v1/assessment/sessions/{id}`, `PATCH /api/v1/assessment/sessions/{id}/self-assessment`, `POST /api/v1/assessment/sessions/{id}/submit`, `POST /api/v1/assessment/sessions/{id}/withdraw`, `POST /api/v1/assessment/sessions/{id}/asesor-review`
- `GET/POST /api/v1/recommendations`, `GET /api/v1/recommendations/{id}`, `PATCH /api/v1/recommendations/{id}/progress`, `POST /api/v1/recommendations/{id}/mark-completed`, `POST /api/v1/recommendations/{id}/verify-close`, `POST /api/v1/recommendations/{id}/manual-close`

## Verification

- `python3.11 -m pytest tests/test_phase2_models_import.py tests/test_phase2_migrations.py tests/test_phase2_services_and_routes.py tests/test_no_upload_policy.py -x -q` -> `14 passed`
- Auto-discovery import remains intact because routers are file-drop additions under `app/routers/`
- All locked decisions `DEC-T1-001..T4-004` are represented in code paths, with carry-over drain stubbed as a no-op until pending queue semantics are introduced

## Deviations From Plan

- This pass focused on unit/smoke coverage, not full DB-backed endpoint tests. The richer live-DB tests listed in the plan are still pending.
- `drain_pending_carry_overs()` is present as a stable hook but currently a no-op because no pending sentinel persistence exists yet.
- Manual carry-over endpoint was not added in this pass; automatic carry-over on periode close is implemented.

## Next Phase Readiness

Plan `02-03` can now attach audit middleware, in-app notifications, WebSocket notifications, and audit-log reads onto these mutating routes without changing route contracts.

---
*Phase: 02-assessment-workflow-pic-asesor*
*Completed: 2026-05-11*
