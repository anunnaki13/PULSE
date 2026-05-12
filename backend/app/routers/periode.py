"""Periode CRUD and lifecycle routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import current_user, require_role
from app.deps.csrf import require_csrf
from app.deps.db import get_db
from app.models.periode import Periode, PeriodeStatus
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.periode import (
    PeriodeCreate,
    PeriodePublic,
    PeriodeTransitionRequest,
    PeriodeUpdate,
)
from app.services.carry_over import close_periode_with_carry_over, drain_pending_carry_overs
from app.services.periode_fsm import (
    InvalidTransition,
    RollbackRequiresReason,
    RollbackRequiresSuperAdmin,
    assert_transition_allowed,
)
from app.services.session_creator import create_sessions_for_periode

router = APIRouter(prefix="/periode", tags=["periode"])


async def _get_periode_or_404(db: AsyncSession, periode_id: uuid.UUID) -> Periode:
    row = await db.scalar(
        select(Periode).where(Periode.id == periode_id, Periode.deleted_at.is_(None))
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "periode_not_found")
    return row


@router.get("", response_model=dict)
async def list_periode(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    q = select(Periode).where(Periode.deleted_at.is_(None))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        await db.scalars(
            q.order_by(Periode.tahun.desc(), Periode.triwulan.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "data": [PeriodePublic.model_validate(r) for r in rows],
        "meta": {"page": page, "page_size": page_size, "total": int(total or 0)},
    }


@router.get("/{periode_id}", response_model=PeriodePublic)
async def get_periode(
    periode_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
) -> PeriodePublic:
    return PeriodePublic.model_validate(await _get_periode_or_404(db, periode_id))


@router.post(
    "",
    response_model=PeriodePublic,
    status_code=status.HTTP_201_CREATED,
    tags=["audit:periode"],
    dependencies=[Depends(require_role("super_admin")), Depends(require_csrf)],
)
async def create_periode(
    payload: PeriodeCreate,
    db: AsyncSession = Depends(get_db),
) -> PeriodePublic:
    clash = await db.scalar(
        select(Periode).where(
            Periode.tahun == payload.tahun,
            Periode.triwulan == payload.triwulan,
            Periode.deleted_at.is_(None),
        )
    )
    if clash:
        raise HTTPException(status.HTTP_409_CONFLICT, "periode_already_exists")
    row = Periode(**payload.model_dump())
    db.add(row)
    await db.flush()
    await db.commit()
    await db.refresh(row)
    return PeriodePublic.model_validate(row)


@router.patch(
    "/{periode_id}",
    response_model=PeriodePublic,
    tags=["audit:periode"],
    dependencies=[Depends(require_role("super_admin")), Depends(require_csrf)],
) 
async def update_periode(
    periode_id: uuid.UUID,
    payload: PeriodeUpdate,
    db: AsyncSession = Depends(get_db),
) -> PeriodePublic:
    row = await _get_periode_or_404(db, periode_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    await db.flush()
    await db.commit()
    await db.refresh(row)
    return PeriodePublic.model_validate(row)


@router.post(
    "/{periode_id}/transition",
    response_model=PeriodePublic,
    tags=["audit:periode"],
    dependencies=[Depends(require_role("super_admin")), Depends(require_csrf)],
)
async def transition_periode(
    periode_id: uuid.UUID,
    payload: PeriodeTransitionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> PeriodePublic:
    row = await _get_periode_or_404(db, periode_id)
    role_names = {r.name for r in user.roles}
    try:
        side_effect = assert_transition_allowed(row.status, payload.target_state, role_names, payload.reason)
    except RollbackRequiresSuperAdmin as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except RollbackRequiresReason as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    except InvalidTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))

    request.state.audit_before = {"status": str(row.status)}
    row.status = PeriodeStatus(payload.target_state)
    row.last_transition_reason = payload.reason
    row.last_transition_by = user.id
    row.last_transition_at = datetime.now(timezone.utc)

    if side_effect == "create_sessions":
        await create_sessions_for_periode(db, row.id)
    elif side_effect == "close_with_carry_over":
        await close_periode_with_carry_over(db, row)
    elif side_effect == "drain_pending_carry_overs":
        await drain_pending_carry_overs(db, row)

    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = {"status": row.status.value, "reason": row.last_transition_reason}
    request.state.audit_entity_id = str(row.id)
    return PeriodePublic.model_validate(row)


@router.get("/{periode_id}/carry-over-summary", response_model=dict)
async def carry_over_summary(
    periode_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
) -> dict:
    periode = await _get_periode_or_404(db, periode_id)
    rows = (
        await db.scalars(select(Recommendation).where(Recommendation.source_periode_id == periode.id))
    ).all()
    return {
        "data": [
            {
                "id": str(r.id),
                "source": str(r.source_periode_id),
                "target": str(r.target_periode_id),
                "carried_to_id": str(r.carried_to_id) if r.carried_to_id else None,
            }
            for r in rows
        ]
    }
