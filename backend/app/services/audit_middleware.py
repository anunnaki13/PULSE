from __future__ import annotations

import uuid
from typing import Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.deps.auth import current_user_optional
from app.models.audit_log import AuditLog

log = get_logger("pulse.audit.middleware")

CAPTURE_VERBS = {"POST", "PATCH", "PUT", "DELETE"}
SKIP_PATHS = {"/api/v1/auth/refresh"}
SKIP_PATH_PREFIXES = ("/ws/",)


def _uuid_or_none(value: object) -> uuid.UUID | None:
    if value in (None, ""):
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in CAPTURE_VERBS:
            return await call_next(request)
        path = request.url.path
        if path in SKIP_PATHS or any(path.startswith(p) for p in SKIP_PATH_PREFIXES):
            return await call_next(request)

        response: Response = await call_next(request)
        if response.status_code >= 400:
            return response

        route = request.scope.get("route")
        route_path = getattr(route, "path", path)
        entity_type = self._resolve_entity_type(getattr(route, "tags", None))
        rows: list[dict] = list(getattr(request.state, "audit_rows", []) or [])
        if not rows and entity_type:
            rows = [
                {
                    "entity_type": entity_type,
                    "entity_id": getattr(request.state, "audit_entity_id", None),
                    "before_data": getattr(request.state, "audit_before", None),
                    "after_data": getattr(request.state, "audit_after", None),
                }
            ]
        if not rows:
            return response

        try:
            async with SessionLocal() as db:
                user = await current_user_optional(request, db)
                for row in rows:
                    db.add(
                        AuditLog(
                            user_id=user.id if user else None,
                            action=f"{request.method} {route_path}",
                            entity_type=row.get("entity_type"),
                            entity_id=_uuid_or_none(row.get("entity_id")),
                            before_data=row.get("before_data"),
                            after_data=row.get("after_data"),
                            ip_address=request.client.host if request.client else None,
                            user_agent=request.headers.get("user-agent"),
                        )
                    )
                await db.commit()
        except Exception as exc:
            log.warning("audit_write_failed", error=str(exc), path=path, method=request.method)
        return response

    @staticmethod
    def _resolve_entity_type(tags: Iterable[str] | None) -> str | None:
        for tag in tags or []:
            if isinstance(tag, str) and tag.startswith("audit:"):
                return tag.split(":", 1)[1]
        return None
