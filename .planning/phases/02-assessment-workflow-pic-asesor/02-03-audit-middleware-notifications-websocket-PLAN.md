---
phase: 02-assessment-workflow-pic-asesor
plan: 03
type: execute
wave: 2
depends_on: [02-01]
files_modified:
  - backend/app/services/audit_middleware.py
  - backend/app/services/notification_dispatcher.py
  - backend/app/services/ws_manager.py
  - backend/app/deps/ws_auth.py
  - backend/app/routers/notification.py
  - backend/app/routers/ws_notifications.py
  - backend/app/routers/audit_log.py
  - backend/app/main.py
  - backend/tests/test_audit_middleware.py
  - backend/tests/test_notification_dispatcher.py
  - backend/tests/test_ws_notifications.py
  - backend/tests/test_audit_log_router.py
autonomous: true
requirements:
  - REQ-notifications
  - REQ-audit-log
must_haves:
  truths:
    - "**DEC-T6-001 honored:** `AuditMiddleware` (Starlette `BaseHTTPMiddleware`) wraps every request. Captures POST/PATCH/PUT/DELETE with `<400` response and route in `/api/v1/*`. Skips GET. Skips `/api/v1/auth/refresh` (RESEARCH §11.8). Resolves `entity_type` from the first `audit:<type>` route tag. Reads `request.state.audit_before / audit_after / audit_entity_id` set by Plan 02-02 handlers. NEVER reads the response body (RESEARCH §11.15 / Pitfall 4)."
    - "**DEC-T6-001 auth capture:** `POST /api/v1/auth/login` success AND failure (with reason `bad_password | locked | inactive`) AND `POST /api/v1/auth/logout` are captured. This is done via explicit `audit_emit(...)` calls in `app/routers/auth.py` (Plan 01-05) — Plan 02-03 amends that router to add the audit hooks (and includes the amendment in `files_modified`)."
    - "**DEC-T6-002 honored:** `audit_log` reads are exposed via `GET /api/v1/audit-logs?...filters` gated by `Depends(require_role('super_admin'))`. NO PATCH, NO DELETE, NO single-row `GET /audit-logs/{id}` (RESEARCH §11.19). Append-only enforced at the router level."
    - "**DEC-T5-001 honored:** No SMTP, no email templates, no aiosmtplib/smtplib/celery/apscheduler imports. Notification channels = in-app DB row + WS push only."
    - "**DEC-T5-002 honored:** `notification_dispatcher.dispatch(...)` creates EXACTLY ONE notification row + ONE WS push per call. No bundling, no digest worker."
    - "**DEC-T5-003 honored:** Six notification types (`assessment_due | review_pending | recommendation_assigned | deadline_approaching | periode_closed | system_announcement`) — `system_announcement` is in-app only (no WS push for that type), the other five fire DB+WS."
    - "**RESEARCH §7 honored:** `WS /ws/notifications?token=...` validates JWT before `websocket.accept()`. Closes with code 1008 (Policy Violation) on bad token or revoked jti. `ws_manager` singleton keeps `{user_id: set[WebSocket]}`. No mid-session re-validation (Pitfall 5). Token is read from query param ONLY."
    - "`notification_dispatcher.dispatch(...)` is atomic-ish: `db.flush()` to get id, `db.commit()`, then `ws_manager.send_to_user(...)`. If WS push raises, the DB row is still committed — the bell badge still surfaces it on the next `/notifications` poll (RESEARCH §8)."
    - "**B-06 honored:** every test file uses real `pytest` (not `ast.parse`); WebSocket tests use `from fastapi.testclient import TestClient` + `client.websocket_connect(...)` (RESEARCH §9 + A6) because httpx AsyncClient does not speak WS."
    - "`app/main.py` is amended to register `AuditMiddleware` via `app.add_middleware(AuditMiddleware)` AFTER FastAPI's auth dependencies run (Starlette middleware order: last-added = outermost). The `audit_middleware` reads `request.state.user` populated by Plan 01-05's `current_user` dep — Plan 02-02 handlers set this BEFORE setting audit_before/after."
    - "**Pitfall 8 startup gate (RESEARCH §11.12 + Pitfall 8):** `app/main.py` adds a startup check that iterates every `APIRoute` and raises if a mutating `/api/v1/*` route lacks an `audit:<entity>` tag (with documented exceptions for `/auth/refresh` and read-only routes that happen to be POST like `/notifications/{id}/read`)."
    - "Notification router exposes: `GET /notifications` (unread-first), `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all`."
    - "Audit-log router exposes: `GET /audit-logs?user_id=&entity_type=&entity_id=&action=&from=&to=&page=&page_size=` (super_admin only). NO POST, NO PATCH, NO DELETE, NO single-row GET."
  artifacts:
    - path: "backend/app/services/audit_middleware.py"
      provides: "Starlette BaseHTTPMiddleware capturing mutating actions per DEC-T6-001; reads request.state.audit_*; never reads response body (Pitfall 4)"
      contains: "AuditMiddleware"
    - path: "backend/app/services/notification_dispatcher.py"
      provides: "dispatch(db, user_id, type, title, body, payload) — DB insert + WS push; no batching (DEC-T5-002); no SMTP (DEC-T5-001)"
      contains: "dispatch"
    - path: "backend/app/services/ws_manager.py"
      provides: "Singleton {user_id: set[WebSocket]} registry with asyncio.Lock; send_to_user(user_id, payload)"
      contains: "WsManager"
    - path: "backend/app/deps/ws_auth.py"
      provides: "validate_ws_token(token) → User | raise; reuses Plan 05's decode_token + is_revoked"
      contains: "decode_token"
    - path: "backend/app/routers/ws_notifications.py"
      provides: "WebSocket /ws/notifications?token=... — RESEARCH §7 pattern"
      contains: "websocket_connect"
    - path: "backend/app/routers/notification.py"
      provides: "GET /notifications + PATCH read + PATCH read-all; audit:notification tag"
      contains: "audit:notification"
    - path: "backend/app/routers/audit_log.py"
      provides: "GET /audit-logs (super_admin only, append-only — no PATCH/DELETE/single-row GET)"
      contains: "super_admin"
    - path: "backend/app/main.py"
      provides: "Registers AuditMiddleware + startup audit-tag check (Pitfall 8); mounts WebSocket route"
      contains: "add_middleware"
  key_links:
    - from: "backend/app/services/audit_middleware.py"
      to: "backend/app/models/audit_log.py"
      via: "INSERT row from request.state.audit_* fields"
      pattern: "AuditLog"
    - from: "backend/app/services/notification_dispatcher.py"
      to: "backend/app/services/ws_manager.py"
      via: "ws_manager.send_to_user(user_id, payload)"
      pattern: "ws_manager"
    - from: "backend/app/routers/ws_notifications.py"
      to: "backend/app/deps/ws_auth.py"
      via: "validate_ws_token(token) before websocket.accept()"
      pattern: "validate_ws_token"
    - from: "backend/app/main.py"
      to: "backend/app/services/audit_middleware.py"
      via: "app.add_middleware(AuditMiddleware) — Starlette LIFO order"
      pattern: "add_middleware\\(AuditMiddleware\\)"
---

## Revision History

- **Iteration 1 (initial):** Audit middleware + WS manager + notification dispatcher + three new routers + main.py amendment for middleware registration + Pitfall 8 startup audit-tag check. Wave 2 parallel with Plan 02-02 — files_modified are disjoint from Plan 02-02 except for `backend/app/main.py` (only this plan owns it for the middleware registration), and the auth router amendment is needed for DEC-T6-001 login/logout capture so this plan adds `backend/app/routers/auth.py` to its modified list (overlap with Plan 01-05 is fine because Plan 01-05 already shipped). All locked decisions honored.

<objective>
Ship the cross-cutting capture + push layer for Phase 2: (a) `AuditMiddleware` that auto-captures every mutating `/api/v1/*` request based on `request.state.audit_*` set by handlers (Plan 02-02); (b) WebSocket plumbing (`ws_manager` + `ws_auth` + `ws_notifications` router); (c) `notification_dispatcher` that fires DB+WS atomically; (d) `/notifications` REST router + `/audit-logs` super_admin read router; (e) Pitfall 8 startup gate that catches missing audit tags on future routes. Every locked decision (DEC-T5-001/002/003 + DEC-T6-001/002) is enforced server-side.

Purpose: Closes REQ-notifications + REQ-audit-log. Parallel with Plan 02-02 (zero file overlap on routers/services/models). Required by Plan 02-04 (frontend `useNotifications` consumes `/ws/notifications`) and the E2E checkpoint (Plan 02-06 walks the operator through bell badge increment + audit-log filter view).

Output: 3 services + 1 dep + 3 routers + `app/main.py` amendment + 4 test files. NO SMTP. NO worker. NO PATCH/DELETE on audit-logs.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/02-assessment-workflow-pic-asesor/02-CONTEXT.md
@.planning/phases/02-assessment-workflow-pic-asesor/02-RESEARCH.md
@.planning/phases/02-assessment-workflow-pic-asesor/02-01-backend-schema-and-migrations-PLAN.md
@.planning/phases/01-foundation-master-data-auth/01-05-auth-backend-jwt-rbac-SUMMARY.md

<interfaces>
<!-- From Plan 02-01 (already in place) -->
- app.models.notification.Notification + NotificationType
- app.models.audit_log.AuditLog
- app.schemas.notification.NotificationPublic
- app.schemas.audit.AuditLogPublic

<!-- From Phase 1 (already in place) -->
- app.core.security.decode_token(token, expected_type="access") -> claims dict
- app.services.refresh_tokens.is_revoked(user_id, jti) -> bool (Plan 05)
- app.deps.auth.require_role, current_user
- app.deps.csrf.require_csrf
- backend/app/main.py (Plan 03+05 created; this plan amends to add AuditMiddleware + startup hook)
- backend/app/routers/auth.py (Plan 05 created; this plan amends to add audit_emit calls for login success/failure + logout)

<!-- Exposed seams (consumed by Plan 02-04/05/06) -->

# Notification REST (audit:notification on writes; require_csrf)
GET    /api/v1/notifications                    current_user  -> {data:[NotificationPublic], meta} unread-first
PATCH  /api/v1/notifications/{id}/read          current_user  -> 200 (idempotent)
PATCH  /api/v1/notifications/read-all           current_user  -> 200 {marked: N}

# WebSocket (no CSRF — WS has no body; token in query param per RESEARCH §7)
WS     /ws/notifications?token=<access_jwt>     close 1008 on invalid; otherwise stream JSON pushes

# Audit log (super_admin only — append-only; NO PATCH/DELETE/single-row GET)
GET    /api/v1/audit-logs?user_id=&entity_type=&entity_id=&action=&from=&to=&page=&page_size=  -> {data:[AuditLogPublic], meta}

# Dispatcher (Python API consumed by Plan 02-02 handlers)
dispatch(db: AsyncSession, *, user_id: UUID, type_: NotificationType, title: str, body: str, payload: dict | None = None) -> Notification
dispatch_assessment_due_for_periode(db, periode_id)
dispatch_review_pending(db, session)
dispatch_review_finished(db, session, *, decision: str)
dispatch_recommendation_assigned(db, recommendation_id)
dispatch_periode_closed(db, periode_id)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: ws_manager singleton + ws_auth dep + ws_notifications WebSocket router + audit_middleware + main.py registration + Pitfall 8 startup gate</name>
  <files>
    backend/app/services/ws_manager.py,
    backend/app/deps/ws_auth.py,
    backend/app/routers/ws_notifications.py,
    backend/app/services/audit_middleware.py,
    backend/app/main.py,
    backend/tests/test_audit_middleware.py,
    backend/tests/test_ws_notifications.py
  </files>
  <action>
    1. `backend/app/services/ws_manager.py` — exact RESEARCH §7 pattern (singleton with asyncio.Lock):
       ```python
       from __future__ import annotations
       import asyncio
       from collections import defaultdict
       from fastapi import WebSocket
       from app.core.logging import get_logger

       log = get_logger("pulse.ws.manager")

       class WsManager:
           def __init__(self) -> None:
               self._lock = asyncio.Lock()
               self._conns: dict[str, set[WebSocket]] = defaultdict(set)

           async def register(self, user_id: str, ws: WebSocket) -> None:
               async with self._lock:
                   self._conns[user_id].add(ws)
                   log.info("ws_registered", user_id=user_id, count=len(self._conns[user_id]))

           async def unregister(self, user_id: str, ws: WebSocket) -> None:
               async with self._lock:
                   self._conns[user_id].discard(ws)
                   if not self._conns[user_id]:
                       del self._conns[user_id]
                   log.info("ws_unregistered", user_id=user_id)

           async def send_to_user(self, user_id: str, payload: dict) -> int:
               """Best-effort fanout. Returns number of sockets the message reached."""
               async with self._lock:
                   sockets = list(self._conns.get(user_id, set()))
               sent = 0
               for sock in sockets:
                   try:
                       await sock.send_json(payload)
                       sent += 1
                   except Exception as e:
                       log.warning("ws_send_failed", user_id=user_id, error=str(e))
                       # Disconnected socket — receive loop handles unregister
               return sent

           def online_users(self) -> set[str]:
               return set(self._conns.keys())

       ws_manager = WsManager()
       ```

    2. `backend/app/deps/ws_auth.py`:
       ```python
       from __future__ import annotations
       from fastapi import WebSocket, status
       from app.core.security import decode_token
       from app.services.refresh_tokens import is_revoked
       from app.core.logging import get_logger

       log = get_logger("pulse.ws.auth")

       class WsAuthFailed(Exception):
           def __init__(self, reason: str):
               self.reason = reason

       async def validate_ws_token(token: str) -> str:
           """Returns user_id (str). Raises WsAuthFailed on bad/expired/revoked token."""
           try:
               claims = decode_token(token, expected_type="access")
           except Exception:
               raise WsAuthFailed("invalid_token")
           user_id = claims.get("sub")
           jti = claims.get("jti")
           if not user_id or not jti:
               raise WsAuthFailed("missing_claims")
           # Check revocation (Plan 05 service — Redis-backed)
           if await is_revoked(user_id, jti):
               raise WsAuthFailed("revoked")
           return user_id
       ```

    3. `backend/app/routers/ws_notifications.py`:
       ```python
       from __future__ import annotations
       from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
       from app.deps.ws_auth import validate_ws_token, WsAuthFailed
       from app.services.ws_manager import ws_manager
       from app.core.logging import get_logger

       log = get_logger("pulse.ws.notifications")

       # NOTE: WS endpoints don't go through the api_router prefix system because Starlette
       # mounts WebSocket routes separately. We expose this under /ws/notifications (NOT /api/v1/...).
       # The auto-discovery router walker in app/routers/__init__.py only does APIRouter HTTP includes,
       # so this file declares a separate `ws_router` symbol that app/main.py mounts directly.
       ws_router = APIRouter()

       @ws_router.websocket("/ws/notifications")
       async def notifications_ws(websocket: WebSocket, token: str = Query(...)):
           try:
               user_id = await validate_ws_token(token)
           except WsAuthFailed as e:
               await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.reason)
               return
           await websocket.accept()
           await ws_manager.register(user_id, websocket)
           try:
               while True:
                   # Client doesn't need to send us anything; this keeps the connection alive
                   # so we get disconnect events propagated up.
                   _ = await websocket.receive_text()
           except WebSocketDisconnect:
               pass
           finally:
               await ws_manager.unregister(user_id, websocket)
       ```
       Add to `backend/app/routers/__init__.py`: import this module's `ws_router` and append it to a top-level export `ws_router` consumed by `main.py`. Avoid putting WS under `/api/v1/...` — clients connect to `/ws/notifications` directly.

    4. `backend/app/services/audit_middleware.py` — RESEARCH §4 + Pitfall 4 (no body capture):
       ```python
       from __future__ import annotations
       from typing import Iterable
       from starlette.middleware.base import BaseHTTPMiddleware
       from starlette.requests import Request
       from starlette.responses import Response
       from sqlalchemy.ext.asyncio import AsyncSession
       from app.db.session import async_session_factory
       from app.models.audit_log import AuditLog
       from app.deps.auth import current_user_optional
       from app.core.logging import get_logger

       log = get_logger("pulse.audit.middleware")

       CAPTURE_VERBS = {"POST", "PATCH", "PUT", "DELETE"}
       SKIP_PATHS = ("/api/v1/auth/refresh",)              # DEC-T6-001 + RESEARCH §11.8
       SKIP_PATH_PREFIXES = ("/ws/",)                       # WebSocket upgrade requests

       class AuditMiddleware(BaseHTTPMiddleware):
           async def dispatch(self, request: Request, call_next):
               # Fast paths
               if request.method not in CAPTURE_VERBS:
                   return await call_next(request)
               path = request.url.path
               if path in SKIP_PATHS or any(path.startswith(p) for p in SKIP_PATH_PREFIXES):
                   return await call_next(request)
               # Run handler
               response: Response = await call_next(request)
               # Skip non-success
               if response.status_code >= 400:
                   return response
               # Resolve entity_type from tag
               route = request.scope.get("route")
               entity_type = self._resolve_entity_type(getattr(route, "tags", None))
               # Capture rows from request.state — multiple emissions supported via audit_rows list
               rows: list[dict] = list(getattr(request.state, "audit_rows", []) or [])
               if not rows and entity_type:
                   rows = [{
                       "entity_type": entity_type,
                       "entity_id":   getattr(request.state, "audit_entity_id", None),
                       "before_data": getattr(request.state, "audit_before", None),
                       "after_data":  getattr(request.state, "audit_after", None),
                   }]
               if not rows:
                   # Mutating route with neither tag nor handler-set state — skip silently.
                   # Pitfall 8 startup gate would have caught this if the route were tagged-eligible.
                   return response
               # Best-effort write — never fail the response on audit error
               try:
                   user = await current_user_optional(request)
                   async with async_session_factory() as db:
                       for r in rows:
                           db.add(AuditLog(
                               user_id=user.id if user else None,
                               action=f"{request.method} {route.path if route else path}",
                               entity_type=r.get("entity_type"),
                               entity_id=r.get("entity_id"),
                               before_data=r.get("before_data"),
                               after_data=r.get("after_data"),
                               ip_address=request.client.host if request.client else None,
                               user_agent=request.headers.get("user-agent"),
                           ))
                       await db.commit()
               except Exception as e:
                   log.warning("audit_write_failed", error=str(e), path=path, method=request.method)
                   # Swallow — never break the live request
               return response

           @staticmethod
           def _resolve_entity_type(tags: Iterable[str] | None) -> str | None:
               for t in (tags or []):
                   if isinstance(t, str) and t.startswith("audit:"):
                       return t.split(":", 1)[1]
               return None
       ```

       Note: Plan 01-03 already declared a placeholder `current_user_optional` dep, or we add one here returning `None` when no auth header/cookie is present. Match the Plan 01-05 dep style:
       ```python
       # backend/app/deps/auth.py (existing — Plan 05 added current_user; this plan adds current_user_optional if missing)
       async def current_user_optional(request: Request):
           try:
               return await current_user(request, db=...)
           except Exception:
               return None
       ```
       If Plan 01-05 already exposes this, reuse — otherwise the middleware can do a minimal cookie/Bearer decode using `decode_token` directly.

    5. `backend/app/main.py` — amendments (this is a MODIFIED file from Plan 01-03 + 01-05):
       ```python
       # Existing Plan-1 imports + app construction stay
       from app.services.audit_middleware import AuditMiddleware
       from app.routers.ws_notifications import ws_router as notifications_ws_router

       app.add_middleware(AuditMiddleware)   # Plan 02-03 — registered AFTER all Plan-1 middleware
       app.include_router(notifications_ws_router)

       @app.on_event("startup")
       async def _audit_tag_startup_gate():
           """Pitfall 8 (RESEARCH §11.12): every mutating /api/v1/* route must carry
           an `audit:<entity>` tag, with the documented exception of /auth/refresh and
           read-only notifications endpoints whose tag is unnecessary.

           Documented exceptions (no audit tag required):
             - /api/v1/auth/refresh       (high volume, DEC-T6-001)
             - GET     anything           (DEC-T6-001 — mutating verbs only)
             - WebSocket upgrades         (no body, no entity)
           """
           from fastapi.routing import APIRoute
           offenders: list[str] = []
           AUDIT_EXEMPT = {"/api/v1/auth/refresh"}
           for route in app.routes:
               if not isinstance(route, APIRoute):
                   continue
               methods = (route.methods or set()) - {"GET", "HEAD", "OPTIONS"}
               if not methods:
                   continue
               if not route.path.startswith("/api/v1/"):
                   continue
               if route.path in AUDIT_EXEMPT:
                   continue
               tags = route.tags or []
               if not any(isinstance(t, str) and t.startswith("audit:") for t in tags):
                   offenders.append(f"{sorted(methods)} {route.path}")
           if offenders:
               raise RuntimeError(
                   "Pitfall 8 (RESEARCH §11.12): the following mutating /api/v1 routes are missing the `audit:<entity>` tag:\n"
                   + "\n".join(f"  - {o}" for o in offenders)
                   + "\nAdd `tags=['audit:<entity_type>']` to the route decorator."
               )
       ```

    6. `backend/tests/test_audit_middleware.py`:
       ```python
       import pytest
       from sqlalchemy import select
       from app.models.audit_log import AuditLog

       @pytest.mark.asyncio
       async def test_patch_session_creates_audit_row(client, db_session, pic_token, per_bidang_session, csrf_cookie):
           r = await client.patch(
               f"/api/v1/assessment/sessions/{per_bidang_session.id}/self-assessment",
               json={"realisasi": 90, "target": 100},
               headers={"Authorization": f"Bearer {pic_token}", "X-CSRF-Token": csrf_cookie},
           )
           assert r.status_code == 200
           rows = (await db_session.scalars(select(AuditLog).where(AuditLog.entity_id == per_bidang_session.id))).all()
           assert len(rows) == 1
           assert rows[0].entity_type == "assessment_session"
           assert rows[0].action.startswith("PATCH ")
           assert rows[0].after_data is not None

       @pytest.mark.asyncio
       async def test_get_does_not_create_audit_row(client, db_session, admin_token, per_bidang_session):
           await client.get(f"/api/v1/assessment/sessions/{per_bidang_session.id}",
                            headers={"Authorization": f"Bearer {admin_token}"})
           rows = (await db_session.scalars(select(AuditLog))).all()
           # No new rows (some may exist from fixture)
           assert all(r.action.startswith("PATCH ") is False and r.action.startswith("POST ") is False for r in rows)

       @pytest.mark.asyncio
       async def test_auth_refresh_not_captured(client, refresh_cookie):
           # Plan 05 exposes /auth/refresh; the audit middleware must skip it
           await client.post("/api/v1/auth/refresh", cookies={"refresh_token": refresh_cookie})
           # The audit row count for action LIKE 'POST /api/v1/auth/refresh' must be 0
           rows = (await db_session.scalars(select(AuditLog).where(AuditLog.action.like("POST %/auth/refresh")))).all()
           assert len(rows) == 0

       @pytest.mark.asyncio
       async def test_failed_request_not_captured(client, pic_token, csrf_cookie):
           # 422 from missing CSRF or scope violation should NOT create an audit row
           r = await client.post(f"/api/v1/periode", json={"tahun": 2026, "triwulan": 5, "semester": 1, "nama": "x"},
                                  headers={"Authorization": f"Bearer {pic_token}", "X-CSRF-Token": csrf_cookie})
           assert r.status_code >= 400
           # No audit row for this failed request

       def test_audit_middleware_does_not_read_response_body(client, admin_token, csrf_cookie):
           """Pitfall 4 / RESEARCH §11.15: middleware must not consume the response body.
           Regression test: a route returning >2KB JSON must not have its body lost."""
           r = client.get("/api/v1/health")
           assert r.text  # body intact
           assert r.headers.get("content-type", "").startswith("application/json")
       ```

    7. `backend/tests/test_ws_notifications.py` (RESEARCH §9 — Starlette TestClient pattern, A6):
       ```python
       import asyncio
       import pytest
       from fastapi.testclient import TestClient
       from starlette.websockets import WebSocketDisconnect
       from app.main import app
       from app.services.notification_dispatcher import dispatch
       from app.models.notification import NotificationType

       def test_ws_rejects_missing_token():
           with TestClient(app) as c:
               with pytest.raises(WebSocketDisconnect):
                   with c.websocket_connect("/ws/notifications"):
                       pass

       def test_ws_rejects_invalid_token():
           with TestClient(app) as c:
               with pytest.raises(WebSocketDisconnect) as exc:
                   with c.websocket_connect("/ws/notifications?token=garbage"):
                       pass
               assert exc.value.code == 1008

       def test_ws_accepts_valid_token_and_receives_push(admin_token, admin_unit_user):
           """End-to-end: connect, dispatch via the sync wrapper, receive JSON."""
           with TestClient(app) as c:
               with c.websocket_connect(f"/ws/notifications?token={admin_token}") as ws:
                   # Fire a dispatch in a background event loop
                   async def _fire():
                       # New session because dispatch needs its own
                       from app.db.session import async_session_factory
                       async with async_session_factory() as db:
                           await dispatch(db, user_id=admin_unit_user.id, type_=NotificationType.SYSTEM_ANNOUNCEMENT,
                                          title="Test", body="hello")
                   # NOTE: SYSTEM_ANNOUNCEMENT is in-app only per DEC-T5-003 — adjust to a WS-enabled type
                   async def _fire_ws_type():
                       from app.db.session import async_session_factory
                       async with async_session_factory() as db:
                           await dispatch(db, user_id=admin_unit_user.id, type_=NotificationType.REVIEW_PENDING,
                                          title="Test", body="hello")
                   asyncio.get_event_loop().run_until_complete(_fire_ws_type())
                   data = ws.receive_json()
                   assert data["type"] == "review_pending"
                   assert data["title"] == "Test"
       ```

       Note: the test relies on the same in-process app sharing `ws_manager` between the test thread and the dispatch path. Starlette's `TestClient` runs the WS in a worker thread; the dispatch's `ws_manager.send_to_user` runs in whatever loop the dispatcher uses. If the test is flaky, mark it `@pytest.mark.skipif(not _docker_available)` and rely on Plan 02-06 E2E to cover the live-loop path (mirror Plan 01-05 SUMMARY decision on docker-dependent tests).

    Commit: `feat(02-03): ws_manager + ws_auth + ws_notifications router + audit_middleware + main.py registration with Pitfall 8 startup gate`.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $files = 'backend/app/services/ws_manager.py','backend/app/deps/ws_auth.py','backend/app/routers/ws_notifications.py','backend/app/services/audit_middleware.py','backend/app/main.py','backend/tests/test_audit_middleware.py','backend/tests/test_ws_notifications.py';
        foreach ($f in $files) { if (-not (Test-Path $f)) { Write-Output ('missing: ' + $f); exit 1 } };
        $am = Get-Content 'backend/app/services/audit_middleware.py' -Raw;
        # RESEARCH §11.15 / Pitfall 4: never read response body
        if ($am -match 'response\.body' -or $am -match 'await response\.body') { Write-Output 'Pitfall 4: middleware must not read response body'; exit 2 };
        # GET skipped (DEC-T6-001)
        if ($am -notmatch 'POST.*PATCH.*PUT.*DELETE' -and $am -notmatch 'CAPTURE_VERBS') { Write-Output 'DEC-T6-001: must capture only POST/PATCH/PUT/DELETE'; exit 3 };
        # /auth/refresh skipped (DEC-T6-001 + RESEARCH §11.8)
        if ($am -notmatch 'auth/refresh') { Write-Output 'DEC-T6-001: must skip /auth/refresh'; exit 4 };
        # 4xx/5xx skipped (only success-side audit)
        if ($am -notmatch 'status_code >= 400') { Write-Output 'audit: skip non-success responses'; exit 5 };
        # Tag resolution via audit:<type>
        if ($am -notmatch 'audit:') { exit 6 };
        # WS auth — closes 1008 on invalid (RESEARCH §7)
        $ws = Get-Content 'backend/app/routers/ws_notifications.py' -Raw;
        if ($ws -notmatch 'WS_1008_POLICY_VIOLATION') { Write-Output 'RESEARCH §7: must close 1008 on invalid token'; exit 7 };
        if ($ws -notmatch 'token: str\s*=\s*Query') { Write-Output 'RESEARCH §7: token must come from query param'; exit 8 };
        # ws_manager — asyncio.Lock present
        $wsm = Get-Content 'backend/app/services/ws_manager.py' -Raw;
        if ($wsm -notmatch 'asyncio.Lock') { exit 9 };
        if ($wsm -notmatch 'send_to_user') { exit 10 };
        # main.py — middleware registered + startup gate present
        $main = Get-Content 'backend/app/main.py' -Raw;
        if ($main -notmatch 'add_middleware\(AuditMiddleware\)') { Write-Output 'main.py must register AuditMiddleware'; exit 11 };
        if ($main -notmatch 'audit:' -and $main -notmatch '_audit_tag_startup_gate') { Write-Output 'main.py must include Pitfall 8 startup gate'; exit 12 };
        # No SMTP / worker imports in any of these files
        $allFiles = (Get-Content $files -Raw) -join '`n';
        foreach ($bad in 'aiosmtplib','smtplib','celery','apscheduler') {
          if ($allFiles -match $bad) { Write-Output ('DEC-T5-001 / RESEARCH §11.5+11: ' + $bad + ' forbidden'); exit 13 }
        };
        # Import smoke
        wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && python3.11 -c \"from app.services.audit_middleware import AuditMiddleware; from app.services.ws_manager import ws_manager; from app.deps.ws_auth import validate_ws_token; from app.routers.ws_notifications import ws_router; print(\\\"audit+ws ok\\\")\"' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Write-Output 'audit/ws import smoke failed'; exit 14 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    AuditMiddleware exists (no response-body read; skips GET / auth/refresh / WS upgrades / 4xx-5xx); ws_manager + ws_auth + ws_notifications router exist (token query param, 1008 on invalid); main.py registers middleware + Pitfall 8 startup gate; no SMTP/worker imports anywhere; all five new module files import cleanly under WSL.
  </done>
</task>

<task type="auto">
  <name>Task 2: notification_dispatcher + auth router amendment for login/logout audit (DEC-T6-001) + notification REST router</name>
  <files>
    backend/app/services/notification_dispatcher.py,
    backend/app/routers/notification.py,
    backend/app/routers/auth.py,
    backend/tests/test_notification_dispatcher.py
  </files>
  <action>
    1. `backend/app/services/notification_dispatcher.py` — RESEARCH §8 pattern; DEC-T5-002 one-per-event, DEC-T5-003 type-channel mapping:
       ```python
       from __future__ import annotations
       from uuid import UUID
       from sqlalchemy import select
       from sqlalchemy.ext.asyncio import AsyncSession
       from app.models.notification import Notification, NotificationType
       from app.models.assessment_session import AssessmentSession
       from app.models.assessment_session_bidang import AssessmentSessionBidang
       from app.models.user import User
       from app.models.role import Role
       from app.services.ws_manager import ws_manager
       from app.core.logging import get_logger

       log = get_logger("pulse.notification.dispatcher")

       # DEC-T5-003: which types fan out via WS? system_announcement is in-app only.
       WS_ENABLED_TYPES = {
           NotificationType.ASSESSMENT_DUE,
           NotificationType.REVIEW_PENDING,
           NotificationType.RECOMMENDATION_ASSIGNED,
           NotificationType.DEADLINE_APPROACHING,
           NotificationType.PERIODE_CLOSED,
       }

       async def dispatch(db: AsyncSession, *, user_id: UUID, type_: NotificationType,
                          title: str, body: str, payload: dict | None = None) -> Notification:
           """Create one DB row + (if WS-enabled) one WS push. DEC-T5-002: no batching."""
           n = Notification(user_id=user_id, type=type_, title=title, body=body, payload=payload or {})
           db.add(n); await db.flush()
           await db.commit()    # commit so /notifications GET sees it
           if type_ in WS_ENABLED_TYPES:
               try:
                   await ws_manager.send_to_user(str(user_id), {
                       "id": str(n.id), "type": type_.value, "title": title,
                       "body": body, "payload": n.payload, "created_at": n.created_at.isoformat() if n.created_at else None,
                   })
               except Exception as e:
                   log.warning("ws_push_failed", user_id=str(user_id), type=type_.value, error=str(e))
           return n

       # Convenience wrappers per Plan 02-02 caller surface:

       async def dispatch_assessment_due_for_periode(db: AsyncSession, periode_id: UUID) -> int:
           """For every newly-spawned session, notify its PIC."""
           sessions = (await db.scalars(select(AssessmentSession).where(AssessmentSession.periode_id == periode_id))).all()
           count = 0
           for s in sessions:
               if s.bidang_id is not None:
                   pic = await db.scalar(select(User).where(User.bidang_id == s.bidang_id, User.is_active.is_(True)).order_by(User.created_at.asc()))
                   if pic:
                       await dispatch(db, user_id=pic.id, type_=NotificationType.ASSESSMENT_DUE,
                                       title="Self-assessment baru tersedia",
                                       body="Periode baru aktif. Silakan isi self-assessment untuk indikator yang ter-assign ke bidang Anda.",
                                       payload={"periode_id": str(periode_id), "session_id": str(s.id)})
                       count += 1
               else:
                   # Aggregate: notify every PIC in assessment_session_bidang
                   bidang_ids = (await db.scalars(select(AssessmentSessionBidang.bidang_id).where(AssessmentSessionBidang.session_id == s.id))).all()
                   pics = (await db.scalars(select(User).where(User.bidang_id.in_(bidang_ids), User.is_active.is_(True)))).all()
                   for pic in pics:
                       await dispatch(db, user_id=pic.id, type_=NotificationType.ASSESSMENT_DUE,
                                       title="Self-assessment baru tersedia (sesi bersama)",
                                       body="Periode baru aktif. Sesi ini dipakai bersama beberapa bidang.",
                                       payload={"periode_id": str(periode_id), "session_id": str(s.id), "aggregate": True})
                       count += 1
           return count

       async def dispatch_review_pending(db: AsyncSession, session: AssessmentSession) -> int:
           """Notify all users with role=asesor."""
           asesors = (await db.scalars(
               select(User).join(User.roles).where(Role.name == "asesor", User.is_active.is_(True))
           )).all()
           for a in asesors:
               await dispatch(db, user_id=a.id, type_=NotificationType.REVIEW_PENDING,
                              title="Submission baru menunggu review",
                              body=f"Self-assessment submitted di periode — silakan review.",
                              payload={"session_id": str(session.id), "periode_id": str(session.periode_id)})
           return len(asesors)

       async def dispatch_review_finished(db: AsyncSession, session: AssessmentSession, *, decision: str) -> int:
           """Notify the PIC of the session that their submission was reviewed (approve/override/revision)."""
           if session.bidang_id is None:
               # aggregate — notify every PIC in the list
               bidang_ids = (await db.scalars(select(AssessmentSessionBidang.bidang_id).where(AssessmentSessionBidang.session_id == session.id))).all()
               targets = (await db.scalars(select(User).where(User.bidang_id.in_(bidang_ids), User.is_active.is_(True)))).all()
           else:
               targets = (await db.scalars(select(User).where(User.bidang_id == session.bidang_id, User.is_active.is_(True)))).all()
           label = {"approve":"disetujui","override":"di-override","request_revision":"perlu revisi"}.get(decision, decision)
           for t in targets:
               await dispatch(db, user_id=t.id, type_=NotificationType.REVIEW_PENDING,   # piggyback on review_pending; UI variant per payload.decision
                              title=f"Submission Anda {label}",
                              body=f"Asesor telah menyelesaikan review (decision={decision}).",
                              payload={"session_id": str(session.id), "decision": decision})
           return len(targets)

       async def dispatch_recommendation_assigned(db: AsyncSession, recommendation_id: str) -> int:
           """Notify every distinct owner_user_id in action_items."""
           from app.models.recommendation import Recommendation
           rec = await db.get(Recommendation, UUID(recommendation_id) if isinstance(recommendation_id, str) else recommendation_id)
           if rec is None: return 0
           owners = {it.get("owner_user_id") for it in (rec.action_items or []) if it.get("owner_user_id")}
           count = 0
           for o in owners:
               try:
                   await dispatch(db, user_id=UUID(o), type_=NotificationType.RECOMMENDATION_ASSIGNED,
                                  title="Rekomendasi baru di-assign",
                                  body=rec.deskripsi[:200],
                                  payload={"recommendation_id": str(rec.id), "severity": rec.severity.value if hasattr(rec.severity, "value") else rec.severity})
                   count += 1
               except Exception:
                   continue
           return count

       async def dispatch_periode_closed(db: AsyncSession, periode_id: UUID) -> int:
           """Fan out periode_closed to every active user (super_admin announcement style — small ops scale, no harm)."""
           users = (await db.scalars(select(User).where(User.is_active.is_(True)))).all()
           for u in users:
               await dispatch(db, user_id=u.id, type_=NotificationType.PERIODE_CLOSED,
                              title="Periode ditutup", body="Periode telah di-finalisasi dan ditutup.",
                              payload={"periode_id": str(periode_id)})
           return len(users)
       ```

    2. `backend/app/routers/auth.py` (AMENDMENT) — add audit hooks to login/logout per DEC-T6-001:
       ```python
       # Plan 01-05 already shipped login + refresh + logout + me. Plan 02-03 adds:
       #
       #   Inside POST /auth/login:
       #     - On success: request.state.audit_after = {"event":"login.success","email":payload.email,"user_id":str(user.id)}
       #                   request.state.audit_entity_id = str(user.id)
       #                   # Tag the route: tags=["audit:auth"]
       #     - On failure (each branch — bad_password, locked, inactive):
       #         request.state.audit_after = {"event":"login.failure","email":payload.email,"reason":"bad_password"|"locked"|"inactive"}
       #         # No entity_id (user may not exist)
       #
       #   Inside POST /auth/logout:
       #     - request.state.audit_after = {"event":"logout","user_id":str(user.id) if user else None}
       #     - Tag: tags=["audit:auth"]
       #
       #   /auth/refresh: NO audit (DEC-T6-001). Already excluded by middleware SKIP_PATHS.
       ```
       For the **failure path**, the middleware only fires when `response.status_code < 400` — but login failures return 401/422. Two options:
         (a) Push the audit row from inside the auth handler directly (one-off DB insert via the audit_log model).
         (b) Special-case the middleware to allow `entity_type=="auth"` to write even on 4xx.
       **Decision (RESEARCH §4 hybrid pattern):** Option (a) — auth router calls `audit_emit_immediately(...)` for failed login. Add a tiny helper:
       ```python
       # backend/app/services/audit_immediate.py    (NEW helper, used only by auth router)
       async def audit_emit_immediately(db: AsyncSession, *, user_id: UUID | None, action: str, before: dict | None, after: dict | None,
                                         entity_type: str | None, entity_id: UUID | None, request: Request | None) -> None:
           row = AuditLog(
               user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id,
               before_data=before, after_data=after,
               ip_address=(request.client.host if request and request.client else None),
               user_agent=(request.headers.get("user-agent") if request else None),
           )
           db.add(row); await db.commit()
       ```
       Then auth.py login failure branches call `audit_emit_immediately(db, user_id=None, action="POST /api/v1/auth/login", before=None, after={"event":"login.failure","reason":"bad_password"}, entity_type="auth", entity_id=None, request=request)` before raising 401.

       Add `backend/app/services/audit_immediate.py` to `files_modified` if you create it (already listed implicitly via auth.py amendment — but mention it explicitly).

       Update `files_modified` accordingly: add `backend/app/services/audit_immediate.py` to this plan's frontmatter `files_modified` list.

    3. `backend/app/routers/notification.py`:
       ```python
       from fastapi import APIRouter, Depends, HTTPException, Request
       from sqlalchemy import select, func
       from sqlalchemy.ext.asyncio import AsyncSession
       from app.deps.auth import current_user, require_role
       from app.deps.csrf import require_csrf
       from app.deps.db import get_db
       from app.models.notification import Notification
       from app.schemas.notification import NotificationPublic

       router = APIRouter(prefix="/notifications", tags=["notifications"])

       @router.get("", dependencies=[Depends(require_role("super_admin","admin_unit","pic_bidang","asesor","manajer_unit","viewer"))])
       async def list_notifications(page: int = 1, page_size: int = 50, db: AsyncSession = Depends(get_db), user = Depends(current_user)):
           # Unread first (read_at NULLS FIRST), then created_at DESC — matches index in 0005
           stmt = select(Notification).where(Notification.user_id == user.id).order_by(
               Notification.read_at.is_(None).desc(),  # NULLS FIRST equivalent
               Notification.created_at.desc(),
           ).limit(page_size).offset((page - 1) * page_size)
           rows = (await db.scalars(stmt)).all()
           total = await db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user.id))
           return {"data": [NotificationPublic.model_validate(r).model_dump(mode="json") for r in rows],
                   "meta": {"page": page, "page_size": page_size, "total": total}}

       @router.patch("/{notif_id}/read", tags=["audit:notification"], dependencies=[Depends(require_csrf)])
       async def mark_read(notif_id, request: Request, db: AsyncSession = Depends(get_db), user = Depends(current_user)):
           n = await db.get(Notification, notif_id)
           if not n or n.user_id != user.id: raise HTTPException(404)
           if n.read_at is None:
               request.state.audit_before = {"read_at": None}
               n.read_at = func.now()
               await db.commit(); await db.refresh(n)
               request.state.audit_after = {"read_at": n.read_at.isoformat() if n.read_at else None}
               request.state.audit_entity_id = str(n.id)
           return {"data": NotificationPublic.model_validate(n).model_dump(mode="json")}

       @router.patch("/read-all", tags=["audit:notification"], dependencies=[Depends(require_csrf)])
       async def mark_all_read(request: Request, db: AsyncSession = Depends(get_db), user = Depends(current_user)):
           result = await db.execute(
               Notification.__table__.update()
                   .where(Notification.user_id == user.id, Notification.read_at.is_(None))
                   .values(read_at=func.now())
           )
           await db.commit()
           request.state.audit_after = {"marked": result.rowcount}
           request.state.audit_entity_id = str(user.id)   # entity is the user (subject)
           return {"data": {"marked": result.rowcount}}
       ```

    4. `backend/tests/test_notification_dispatcher.py`:
       - `dispatch(db, user_id=u.id, type_=ASSESSMENT_DUE, ...)` creates one notification row.
       - DEC-T5-002: calling `dispatch` twice creates TWO rows (no batching).
       - DEC-T5-003: SYSTEM_ANNOUNCEMENT type does NOT trigger WS (mock `ws_manager.send_to_user`); other types DO call it.
       - `dispatch_assessment_due_for_periode` after `create_sessions_for_periode` fans out one notif per PIC.
       - `dispatch_recommendation_assigned` reads `action_items[*].owner_user_id` and dispatches per distinct owner.
       - GET /notifications returns unread first, ordered by created_at DESC.
       - PATCH /notifications/{id}/read flips read_at; idempotent.

    Commit: `feat(02-03): notification_dispatcher + notification router + audit on login/logout (DEC-T5-001..003 + DEC-T6-001)`.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $files = 'backend/app/services/notification_dispatcher.py','backend/app/routers/notification.py','backend/app/routers/auth.py','backend/tests/test_notification_dispatcher.py';
        foreach ($f in $files) { if (-not (Test-Path $f)) { Write-Output ('missing: ' + $f); exit 1 } };
        $nd = Get-Content 'backend/app/services/notification_dispatcher.py' -Raw;
        # No SMTP (DEC-T5-001)
        foreach ($bad in 'aiosmtplib','smtplib','SMTP','celery','apscheduler') {
          if ($nd -match $bad) { Write-Output ('DEC-T5-001: ' + $bad + ' forbidden'); exit 2 }
        };
        # DEC-T5-002: one row per call (no batch/digest)
        if ($nd -match 'digest' -or $nd -match 'batch_insert') { Write-Output 'DEC-T5-002: no batching allowed'; exit 3 };
        # DEC-T5-003: system_announcement in-app only — check WS_ENABLED_TYPES does NOT include it
        if ($nd -match 'SYSTEM_ANNOUNCEMENT.*WS_ENABLED' -or $nd -match 'WS_ENABLED.*SYSTEM_ANNOUNCEMENT') { Write-Output 'DEC-T5-003: system_announcement must NOT be in WS_ENABLED_TYPES'; exit 4 };
        # All six notification types referenced
        foreach ($t in 'ASSESSMENT_DUE','REVIEW_PENDING','RECOMMENDATION_ASSIGNED','DEADLINE_APPROACHING','PERIODE_CLOSED','SYSTEM_ANNOUNCEMENT') {
          if ($nd -notmatch $t) { Write-Output ('DEC-T5-003 missing type ' + $t); exit 5 }
        };
        # Notification router audit tags + CSRF on writes
        $nr = Get-Content 'backend/app/routers/notification.py' -Raw;
        if ($nr -notmatch 'audit:notification') { exit 6 };
        if ($nr -notmatch 'require_csrf') { exit 7 };
        # Auth router amendment — login success + failure capture (DEC-T6-001)
        $ar = Get-Content 'backend/app/routers/auth.py' -Raw;
        if ($ar -notmatch 'audit:auth') { Write-Output 'DEC-T6-001: auth router missing audit:auth tag'; exit 8 };
        # Failed login still captured via immediate audit
        if ($ar -notmatch 'audit_emit_immediately' -and $ar -notmatch 'audit_immediate') { Write-Output 'DEC-T6-001: failed-login audit capture missing'; exit 9 };
        # Import smoke
        wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && python3.11 -c \"from app.services.notification_dispatcher import dispatch, WS_ENABLED_TYPES; from app.routers.notification import router; from app.routers.auth import router as auth_router; print(len(router.routes), len(auth_router.routes), len(WS_ENABLED_TYPES))\"' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { exit 10 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    notification_dispatcher exists with WS_ENABLED_TYPES excluding system_announcement (DEC-T5-003), no SMTP/worker, one-row-per-call (no batching, DEC-T5-002); auth router amended with `audit:auth` tag + failed-login immediate audit; notification router exists with audit:notification + CSRF on writes; import smoke green.
  </done>
</task>

<task type="auto">
  <name>Task 3: audit-log read-only router (super_admin) + test (verifies no PATCH/DELETE/single-row GET surface)</name>
  <files>
    backend/app/routers/audit_log.py,
    backend/tests/test_audit_log_router.py
  </files>
  <action>
    1. `backend/app/routers/audit_log.py` — append-only contract enforced at router level (DEC-T6-002 + RESEARCH §11.19):
       ```python
       from __future__ import annotations
       from datetime import datetime
       from uuid import UUID
       from typing import Literal
       from fastapi import APIRouter, Depends, Query
       from sqlalchemy import select, func
       from sqlalchemy.ext.asyncio import AsyncSession
       from app.deps.auth import require_role
       from app.deps.db import get_db
       from app.models.audit_log import AuditLog
       from app.schemas.audit import AuditLogPublic

       router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])

       @router.get("", dependencies=[Depends(require_role("super_admin"))])
       async def list_audit_logs(
           user_id: UUID | None = None,
           entity_type: str | None = None,
           entity_id: UUID | None = None,
           action_contains: str | None = None,
           from_: datetime | None = Query(default=None, alias="from"),
           to:   datetime | None = None,
           page: int = 1,
           page_size: int = Query(default=50, le=200),
           db: AsyncSession = Depends(get_db),
       ):
           stmt = select(AuditLog)
           if user_id is not None:
               stmt = stmt.where(AuditLog.user_id == user_id)
           if entity_type is not None:
               stmt = stmt.where(AuditLog.entity_type == entity_type)
           if entity_id is not None:
               stmt = stmt.where(AuditLog.entity_id == entity_id)
           if action_contains:
               stmt = stmt.where(AuditLog.action.ilike(f"%{action_contains}%"))
           if from_ is not None:
               stmt = stmt.where(AuditLog.created_at >= from_)
           if to is not None:
               stmt = stmt.where(AuditLog.created_at <= to)
           stmt = stmt.order_by(AuditLog.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
           rows = (await db.scalars(stmt)).all()
           # Total — use same WHEREs (omit ORDER BY / OFFSET / LIMIT)
           count_stmt = select(func.count()).select_from(AuditLog)
           # Re-apply filters (DRY helper preferred — kept inline for brevity here)
           if user_id is not None:    count_stmt = count_stmt.where(AuditLog.user_id == user_id)
           if entity_type is not None: count_stmt = count_stmt.where(AuditLog.entity_type == entity_type)
           if entity_id is not None:   count_stmt = count_stmt.where(AuditLog.entity_id == entity_id)
           if action_contains:        count_stmt = count_stmt.where(AuditLog.action.ilike(f"%{action_contains}%"))
           if from_ is not None:      count_stmt = count_stmt.where(AuditLog.created_at >= from_)
           if to is not None:         count_stmt = count_stmt.where(AuditLog.created_at <= to)
           total = await db.scalar(count_stmt)
           return {"data": [AuditLogPublic.model_validate(r).model_dump(mode="json") for r in rows],
                   "meta": {"page": page, "page_size": page_size, "total": total}}

       # No POST, no PATCH, no DELETE, no single-row GET.  Append-only contract.
       ```

    2. `backend/tests/test_audit_log_router.py`:
       ```python
       import pytest

       @pytest.mark.asyncio
       async def test_audit_logs_requires_super_admin(client, admin_unit_token):
           # admin_unit ≠ super_admin
           r = await client.get("/api/v1/audit-logs",
                                 headers={"Authorization": f"Bearer {admin_unit_token}"})
           assert r.status_code == 403

       @pytest.mark.asyncio
       async def test_audit_logs_super_admin_can_filter(client, super_admin_token, sample_audit_rows):
           r = await client.get("/api/v1/audit-logs?entity_type=assessment_session",
                                 headers={"Authorization": f"Bearer {super_admin_token}"})
           assert r.status_code == 200
           data = r.json()["data"]
           assert all(row["entity_type"] == "assessment_session" for row in data)

       @pytest.mark.asyncio
       async def test_no_post_patch_delete_single_get_on_audit_logs(client, super_admin_token):
           """RESEARCH §11.19: append-only — no PATCH/DELETE; no single-row GET surface."""
           h = {"Authorization": f"Bearer {super_admin_token}"}
           assert (await client.post  ("/api/v1/audit-logs", json={}, headers=h)).status_code in (404, 405)
           assert (await client.patch ("/api/v1/audit-logs/00000000-0000-0000-0000-000000000000", json={}, headers=h)).status_code in (404, 405)
           assert (await client.delete("/api/v1/audit-logs/00000000-0000-0000-0000-000000000000", headers=h)).status_code in (404, 405)
           assert (await client.get   ("/api/v1/audit-logs/00000000-0000-0000-0000-000000000000", headers=h)).status_code in (404, 405)

       @pytest.mark.asyncio
       async def test_audit_logs_pagination_caps_page_size(client, super_admin_token):
           r = await client.get("/api/v1/audit-logs?page_size=10000",
                                 headers={"Authorization": f"Bearer {super_admin_token}"})
           # Pydantic Query(le=200) → 422
           assert r.status_code == 422
       ```

    Commit: `feat(02-03): audit_log read router (super_admin, append-only) + tests`.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $files = 'backend/app/routers/audit_log.py','backend/tests/test_audit_log_router.py';
        foreach ($f in $files) { if (-not (Test-Path $f)) { Write-Output ('missing: ' + $f); exit 1 } };
        $al = Get-Content 'backend/app/routers/audit_log.py' -Raw;
        # super_admin only (DEC-T6-002)
        if ($al -notmatch 'require_role\(\"super_admin\"\)') { Write-Output 'DEC-T6-002: must be super_admin only'; exit 2 };
        # Append-only: NO POST, NO PATCH, NO DELETE decorators
        if ($al -match '@router\.post') { Write-Output 'RESEARCH §11.19: no POST on /audit-logs'; exit 3 };
        if ($al -match '@router\.patch') { Write-Output 'RESEARCH §11.19: no PATCH on /audit-logs'; exit 4 };
        if ($al -match '@router\.delete') { Write-Output 'RESEARCH §11.19: no DELETE on /audit-logs'; exit 5 };
        # No single-row GET (RESEARCH §11.19)
        if ($al -match '@router\.get\(\"/\{') { Write-Output 'RESEARCH §11.19: no single-row GET on /audit-logs'; exit 6 };
        # Filters supported per DEC-T6-002
        foreach ($f in 'user_id','entity_type','entity_id','from','to','page_size') {
          if ($al -notmatch $f) { Write-Output ('filter ' + $f + ' missing on audit-logs GET'); exit 7 }
        };
        # page_size capped (sanity)
        if ($al -notmatch 'le=200' -and $al -notmatch 'le=100') { Write-Output 'page_size must be capped'; exit 8 };
        # Import smoke
        wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && python3.11 -c \"from app.routers.audit_log import router; methods = sorted({m for r in router.routes for m in (r.methods or set())}); print(methods)\"' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { exit 9 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Audit-log router exists at `/api/v1/audit-logs`; super_admin gate; only a list GET (no single-row GET, no POST/PATCH/DELETE — append-only contract per RESEARCH §11.19); filters per DEC-T6-002; page_size capped at 200.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| WebSocket client → /ws/notifications | Token in query param; validated before accept; closed 1008 on fail |
| Middleware → audit_log | Append-only at router level (no PATCH/DELETE); middleware is best-effort (errors swallowed) |
| notification_dispatcher → ws_manager | Best-effort push; DB row is the durable source of truth |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-03-S-01 | Spoofing | WS connection with stolen/invalid token | mitigate | `validate_ws_token` decodes + checks `is_revoked` before accept; closes 1008 on fail (RESEARCH §7). Test: `test_ws_rejects_invalid_token`. |
| T-02-03-S-02 | Spoofing | WS connection with expired-but-not-revoked token | accept | Pitfall 5: short access-token lifetime (60 min from Plan 05) + Zustand-driven reconnect after refresh keeps the window small. No mid-session re-validation. |
| T-02-03-T-01 | Tampering | Forging audit_log via direct POST | mitigate | RESEARCH §11.19: NO POST/PATCH/DELETE on `/audit-logs` router. Audit rows are written ONLY by middleware (with `request.state.audit_*` set by handlers) or by `audit_emit_immediately` (auth router for failed login). |
| T-02-03-T-02 | Tampering | Skipping audit-tag on a new route | mitigate | Pitfall 8 startup gate in `app/main.py`: enumerates `app.routes`, raises RuntimeError if any mutating `/api/v1/*` route lacks `audit:<entity>` tag. Catches the regression at boot. |
| T-02-03-R-01 | Repudiation | Audit-log row deletion | mitigate | No DELETE endpoint; no `deleted_at` column on `audit_log` (Plan 02-01 schema); retention forever (DEC-T6-002). |
| T-02-03-D-01 | DOS | WebSocket connection flood | accept | nginx `limit_conn` is a Phase 6 prod-checklist add (RESEARCH §Security Domain). Phase 2 ws_manager has no per-user cap. Acceptable at PLN ops scale. |
| T-02-03-D-02 | DOS | Audit middleware blocks request on DB failure | mitigate | Best-effort write inside `try/except` — log warning, never propagate. Request still returns to client. |
| T-02-03-I-01 | Info disclosure | audit_log read by non-super_admin | mitigate | `require_role("super_admin")` on every audit-log read endpoint. Test: `test_audit_logs_requires_super_admin`. |
| T-02-03-I-02 | Info disclosure | WS token visible in nginx access logs | accept | Production nginx config (Plan 01-02) doesn't log query strings on `/ws/*` location. Documented in Phase 6 prod hardening checklist. |
| T-02-03-E-01 | Elevation | Bypass middleware via custom route | mitigate | Middleware sits at the ASGI app level — every request goes through it. Custom routes still hit it; only WS upgrades skip (by `SKIP_PATH_PREFIXES`). |
</threat_model>

<verification>
After this plan executes:

1. `wsl -d Ubuntu-22.04 -- python3.11 -m pytest backend/tests/test_audit_middleware.py backend/tests/test_ws_notifications.py backend/tests/test_notification_dispatcher.py backend/tests/test_audit_log_router.py -x -q` passes (WS test may skip in unit-mode if `_docker_available()` is False — that's expected; Plan 02-06 E2E covers the live path).
2. Plan 02-02's existing tests still pass (auto-discovery means dropping new routers doesn't break old endpoints).
3. `wsl -d Ubuntu-22.04 -- python3.11 -c "from app.main import app; print(type(app.user_middleware[0]).__name__ if app.user_middleware else 'none'); print('AuditMiddleware' in str([type(m).__name__ for m in app.user_middleware]))"` confirms AuditMiddleware is registered.
4. Triggering app startup (e.g., `python3.11 -c "from app.main import app; import asyncio; asyncio.run(app.router.startup())"` or live `uvicorn app.main:app`) does NOT raise the Pitfall 8 startup gate (every mutating `/api/v1/*` route has `audit:<entity>` tag — Plan 02-02 + Plan 02-03 together satisfy this).
5. No string `aiosmtplib`, `smtplib`, `celery`, `apscheduler` exists in any file this plan creates.
6. `GET /api/v1/audit-logs` exposes only the list endpoint (no `POST/PATCH/DELETE/{id}`).
</verification>

<success_criteria>
- [ ] AuditMiddleware exists; skips GET, /auth/refresh, /ws/*, 4xx-5xx; never reads response body
- [ ] AuditMiddleware resolves entity_type from `audit:<type>` tag; reads `request.state.audit_before/after/entity_id`
- [ ] Pitfall 8 startup gate in `main.py` catches missing audit tags at boot
- [ ] ws_manager singleton + ws_auth dep + ws_notifications router exist; closes 1008 on invalid token
- [ ] notification_dispatcher fires DB row + (for WS-enabled types only — DEC-T5-003) WS push; no batching (DEC-T5-002)
- [ ] WS_ENABLED_TYPES excludes SYSTEM_ANNOUNCEMENT (DEC-T5-003)
- [ ] Auth router amended with `audit:auth` tag + immediate audit emission for failed login (DEC-T6-001)
- [ ] Notification REST router has unread-first GET + PATCH read + PATCH read-all; mutating routes carry `audit:notification` + CSRF
- [ ] Audit-log router has ONLY a filterable list GET; no POST/PATCH/DELETE/single-row GET; super_admin only (DEC-T6-002 + RESEARCH §11.19)
- [ ] No SMTP / celery / apscheduler / aiosmtplib in any file
- [ ] All 4 new test files run green under WSL pytest (WS test may skip if Docker unavailable in unit mode)
</success_criteria>

<output>
After completion, write `.planning/phases/02-assessment-workflow-pic-asesor/02-03-audit-middleware-notifications-websocket-SUMMARY.md`. Include the startup-gate audit-tag inventory (list every `/api/v1/*` mutating route + its tag) and the notification type → channel matrix.
</output>
