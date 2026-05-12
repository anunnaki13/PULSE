from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import current_user, require_role
from app.deps.csrf import require_csrf
from app.deps.db import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationPublic

router = APIRouter(prefix="/notifications", tags=["notifications"])

_ANY_ROLE = ("super_admin", "admin_unit", "pic_bidang", "asesor", "manajer_unit", "viewer")


@router.get("", dependencies=[Depends(require_role(*_ANY_ROLE))])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.read_at.is_(None).desc(), Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.scalars(stmt)).all()
    total = await db.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.id)
    )
    return {
        "data": [NotificationPublic.model_validate(row).model_dump(mode="json") for row in rows],
        "meta": {"page": page, "page_size": page_size, "total": int(total or 0)},
    }


@router.patch(
    "/read-all",
    tags=["audit:notification"],
    dependencies=[Depends(require_csrf)],
)
async def mark_all_read(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    request.state.audit_after = {"marked": result.rowcount}
    request.state.audit_entity_id = str(user.id)
    return {"data": {"marked": result.rowcount}}


@router.patch(
    "/{notif_id}/read",
    tags=["audit:notification"],
    dependencies=[Depends(require_csrf)],
)
async def mark_read(
    notif_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    notif = await db.get(Notification, notif_id)
    if notif is None or notif.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "notification_not_found")
    if notif.read_at is None:
        request.state.audit_before = {"read_at": None}
        notif.read_at = datetime.now(timezone.utc)
        await db.flush()
        await db.commit()
        await db.refresh(notif)
        request.state.audit_after = {"read_at": notif.read_at.isoformat() if notif.read_at else None}
        request.state.audit_entity_id = str(notif.id)
    return {"data": NotificationPublic.model_validate(notif).model_dump(mode="json")}
