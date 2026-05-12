from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import require_role
from app.deps.db import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogPublic

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def _apply_filters(
    stmt,
    *,
    user_id: UUID | None,
    entity_type: str | None,
    entity_id: UUID | None,
    action_contains: str | None,
    from_: datetime | None,
    to: datetime | None,
):
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
    return stmt


@router.get("", dependencies=[Depends(require_role("super_admin"))])
async def list_audit_logs(
    user_id: UUID | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    action_contains: str | None = None,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict:
    filters = {
        "user_id": user_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action_contains": action_contains,
        "from_": from_,
        "to": to,
    }
    stmt = _apply_filters(select(AuditLog), **filters).order_by(AuditLog.created_at.desc())
    rows = (await db.scalars(stmt.offset((page - 1) * page_size).limit(page_size))).all()
    total = await db.scalar(_apply_filters(select(func.count()).select_from(AuditLog), **filters))
    return {
        "data": [AuditLogPublic.model_validate(row).model_dump(mode="json") for row in rows],
        "meta": {"page": page, "page_size": page_size, "total": int(total or 0)},
    }
