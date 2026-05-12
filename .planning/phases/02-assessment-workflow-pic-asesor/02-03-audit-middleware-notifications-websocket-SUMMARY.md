# Plan 02-03 Summary - Audit Middleware, Notifications, WebSocket

## Outcome

Status: COMPLETE

Implemented the Phase 02 cross-cutting backend layer for audit capture, in-app notifications, WebSocket notification push, and read-only audit-log access.

## Shipped

- Added `AuditMiddleware` for mutating `/api/v1/*` requests.
  - Captures `POST`, `PATCH`, `PUT`, `DELETE`.
  - Skips `GET`, `/api/v1/auth/refresh`, `/ws/*`, and non-success responses.
  - Resolves entity type from `audit:<entity>` route tags.
  - Reads `request.state.audit_before`, `audit_after`, `audit_entity_id`, or `audit_rows`.
  - Does not read response bodies.
- Added immediate audit emission for auth failures.
  - `POST /auth/login` success is captured by middleware.
  - `POST /auth/login` failures are captured directly with `bad_password`, `locked`, or `inactive`.
  - `POST /auth/logout` is tagged and captured.
- Added notification infrastructure.
  - `notification_dispatcher.dispatch(...)` creates exactly one DB row per call.
  - WS push is best effort after commit.
  - `system_announcement` is in-app only.
- Added WebSocket notification channel.
  - `WS /ws/notifications?token=...`.
  - Token is read from query param only.
  - Invalid/missing tokens close with 1008.
  - `ws_manager` tracks `{user_id: set[WebSocket]}`.
- Added notification REST router.
  - `GET /api/v1/notifications`.
  - `PATCH /api/v1/notifications/{id}/read`.
  - `PATCH /api/v1/notifications/read-all`.
- Added audit-log read router.
  - `GET /api/v1/audit-logs`.
  - Super-admin only.
  - No POST, PATCH, DELETE, or single-row GET.
- Added startup gate in `app.main`.
  - Every mutating `/api/v1/*` route must carry an `audit:<entity>` tag.
  - `/api/v1/auth/refresh` is the documented exception.
- Added `jti` to access tokens so WebSocket token validation can perform revocation checks.
- Fixed `Notification.type` SQLAlchemy mapping to the existing PostgreSQL `notification_type` enum.

## Audit Tag Inventory

- `PATCH /api/v1/assessment/sessions/{session_id}/self-assessment` -> `audit:assessment_session`
- `POST /api/v1/assessment/sessions/{session_id}/submit` -> `audit:assessment_session`
- `POST /api/v1/assessment/sessions/{session_id}/withdraw` -> `audit:assessment_session`
- `POST /api/v1/assessment/sessions/{session_id}/asesor-review` -> `audit:assessment_session`
- `POST /api/v1/auth/login` -> `audit:auth`
- `POST /api/v1/auth/logout` -> `audit:auth`
- `POST /api/v1/bidang` -> `audit:bidang`
- `PATCH /api/v1/bidang/{bidang_id}` -> `audit:bidang`
- `DELETE /api/v1/bidang/{bidang_id}` -> `audit:bidang`
- `POST /api/v1/konkin/templates` -> `audit:konkin_template`
- `PATCH /api/v1/konkin/templates/{template_id}` -> `audit:konkin_template`
- `POST /api/v1/konkin/templates/{template_id}/lock` -> `audit:konkin_template`
- `POST /api/v1/konkin/templates/{template_id}/import-from-excel` -> `audit:konkin_template`
- `POST /api/v1/konkin/templates/{template_id}/perspektif` -> `audit:perspektif`
- `PATCH /api/v1/konkin/perspektif/{perspektif_id}` -> `audit:perspektif`
- `DELETE /api/v1/konkin/perspektif/{perspektif_id}` -> `audit:perspektif`
- `POST /api/v1/konkin/perspektif/{perspektif_id}/indikator` -> `audit:indikator`
- `PATCH /api/v1/konkin/indikator/{indikator_id}` -> `audit:indikator`
- `DELETE /api/v1/konkin/indikator/{indikator_id}` -> `audit:indikator`
- `POST /api/v1/ml-stream` -> `audit:ml_stream`
- `PATCH /api/v1/ml-stream/{stream_id}` -> `audit:ml_stream`
- `DELETE /api/v1/ml-stream/{stream_id}` -> `audit:ml_stream`
- `PATCH /api/v1/notifications/read-all` -> `audit:notification`
- `PATCH /api/v1/notifications/{notif_id}/read` -> `audit:notification`
- `POST /api/v1/periode` -> `audit:periode`
- `PATCH /api/v1/periode/{periode_id}` -> `audit:periode`
- `POST /api/v1/periode/{periode_id}/transition` -> `audit:periode`
- `POST /api/v1/recommendations` -> `audit:recommendation`
- `PATCH /api/v1/recommendations/{rec_id}/progress` -> `audit:recommendation`
- `POST /api/v1/recommendations/{rec_id}/mark-completed` -> `audit:recommendation`
- `POST /api/v1/recommendations/{rec_id}/verify-close` -> `audit:recommendation`
- `POST /api/v1/recommendations/{rec_id}/manual-close` -> `audit:recommendation`

Exception:

- `POST /api/v1/auth/refresh` -> no audit by DEC-T6-001.

## Notification Channel Matrix

| Type | DB Row | WebSocket |
| --- | --- | --- |
| `assessment_due` | yes | yes |
| `review_pending` | yes | yes |
| `recommendation_assigned` | yes | yes |
| `deadline_approaching` | yes | yes |
| `periode_closed` | yes | yes |
| `system_announcement` | yes | no |

## Verification

- `python3.11 -m pytest tests/test_audit_middleware.py tests/test_notification_dispatcher.py tests/test_ws_notifications.py tests/test_audit_log_router.py -x -q`
  - Result: 13 passed.
- `python3.11 -m pytest tests/test_phase2_models_import.py tests/test_phase2_migrations.py tests/test_phase2_services_and_routes.py tests/test_no_upload_policy.py tests/test_auth.py tests/test_rbac.py -x -q`
  - Result: 26 passed.
- Startup audit-tag gate executed successfully.
- Docker stack rebuilt with the updated backend image and verified healthy at `/api/v1/health`.
- Admin login verified through `http://127.0.0.1:3399/api/v1/auth/login`.
