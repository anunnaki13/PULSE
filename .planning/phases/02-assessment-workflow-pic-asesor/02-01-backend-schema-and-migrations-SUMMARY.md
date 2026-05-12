---
phase: 02-assessment-workflow-pic-asesor
plan: 01
subsystem: database
tags: [fastapi, sqlalchemy, alembic, pydantic, postgres, audit-log]
requires:
  - phase: 01-foundation-master-data-auth
    provides: users, roles, bidang, indikator, Alembic head 0003_master_data, auto-discovery Base
provides:
  - Phase 2 Postgres schema foundation for periode, assessment sessions, recommendations, notifications, and audit logs
  - Pydantic v2 DTOs for Phase 2 routers with extra='forbid'
  - Linear Alembic chain 0004 -> 0005 -> 0006
  - Smoke tests for model/schema imports, validators, and migration metadata
affects: [02-02-periode-assessment-recommendation-routers, 02-03-audit-middleware-notifications-websocket]
tech-stack:
  added: []
  patterns: [drop-in model auto-discovery, pure Pydantic validators, manual Alembic DDL]
key-files:
  created:
    - backend/app/models/periode.py
    - backend/app/models/assessment_session.py
    - backend/app/models/assessment_session_bidang.py
    - backend/app/models/indikator_applicable_bidang.py
    - backend/app/models/recommendation.py
    - backend/app/models/notification.py
    - backend/app/models/audit_log.py
    - backend/app/schemas/periode.py
    - backend/app/schemas/assessment.py
    - backend/app/schemas/recommendation.py
    - backend/app/schemas/notification.py
    - backend/app/schemas/audit.py
    - backend/alembic/versions/20260513_100000_0004_periode_and_sessions.py
    - backend/alembic/versions/20260513_110000_0005_recommendation_notification.py
    - backend/alembic/versions/20260513_120000_0006_audit_log.py
    - backend/tests/test_phase2_models_import.py
    - backend/tests/test_phase2_migrations.py
  modified: []
key-decisions:
  - "Used hand-written migrations to preserve locked enum names, FK ordering, and DEC-T6-002 index names."
  - "Kept schema validators pure; owner resolution and DB lookups remain deferred to services in Plan 02-02."
patterns-established:
  - "Phase 2 models are added as new modules only; app.db.base auto-discovery picks them up without edits."
  - "Request DTOs use ConfigDict(extra='forbid') so writable server-derived fields are rejected at the edge."
requirements-completed:
  - REQ-periode-lifecycle
  - REQ-self-assessment-kpi-form
  - REQ-self-assessment-ml-form
  - REQ-pic-actions
  - REQ-asesor-review
  - REQ-recommendation-create
  - REQ-recommendation-lifecycle
  - REQ-notifications
  - REQ-audit-log
duration: 35min
completed: 2026-05-11
---

# Phase 02 Plan 01: Backend Schema And Migrations Summary

**Postgres schema, SQLAlchemy models, and Pydantic contracts for the Assessment Workflow domain.**

## Accomplishments

- Added seven Phase 2 tables: `periode`, `assessment_session`, `assessment_session_bidang`, `indikator_applicable_bidang`, `recommendation`, `notification`, `audit_log`.
- Added five Pydantic schema modules with `ConfigDict(extra="forbid")`; `AsesorReview` enforces override `nilai_final` plus `catatan_asesor >= 20 chars`.
- Added Alembic chain from `0003_master_data` to head `0006_audit_log`.
- Auto-discovery confirmed: `Base.metadata.tables` includes `audit_log`, `assessment_session`, `assessment_session_bidang`, `indikator_applicable_bidang`, `notification`, `periode`, and `recommendation`.

## Enum Values

- `periode.status`: `draft`, `aktif`, `self_assessment`, `asesmen`, `finalisasi`, `closed`
- `assessment_session.state`: `draft`, `submitted`, `approved`, `overridden`, `revision_requested`, `abandoned`
- `recommendation.status`: `open`, `in_progress`, `pending_review`, `closed`, `carried_over`
- `recommendation.severity`: `low`, `medium`, `high`, `critical`
- `notification.type`: `assessment_due`, `review_pending`, `recommendation_assigned`, `deadline_approaching`, `periode_closed`, `system_announcement`

## Verification

- `python3.11 -m pytest tests/test_phase2_models_import.py tests/test_phase2_migrations.py -x -q` -> `8 passed`
- `python3.11 -m pytest tests/test_no_upload_policy.py -x -q` -> `2 passed`
- `alembic heads` -> `0006_audit_log (head)`
- `rg -i "siskonkin" <17 created files>` -> no matches

## Deviations From Plan

- `test_phase2_migrations.py` is static in unit mode instead of starting an ephemeral Postgres container. The live migration path remains deferred to the compose/E2E checkpoint; Alembic parsing and head resolution were still verified.

## Next Phase Readiness

Plan `02-02` can now build domain services and routers against these models/schemas. Plan `02-03` can build audit middleware, notification dispatch, WebSocket notifications, and audit-log read APIs against the new `notification` and `audit_log` tables.

---
*Phase: 02-assessment-workflow-pic-asesor*
*Completed: 2026-05-11*
