"""Recommendation routes and lifecycle operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import current_user, require_role
from app.deps.csrf import require_csrf
from app.deps.db import get_db
from app.models.assessment_session import AssessmentSession
from app.models.recommendation import Recommendation, RecommendationStatus
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationProgressUpdate,
    RecommendationPublic,
    RecommendationVerifyClose,
)
from app.services.recommendation_create import OwnerRequired, create_recommendation_with_owner_resolution
from app.services.recommendation_fsm import (
    InvalidLifecycle,
    assert_mark_completed_allowed,
    assert_verify_close_allowed,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


async def _get_recommendation_or_404(db: AsyncSession, rec_id: uuid.UUID) -> Recommendation:
    row = await db.get(Recommendation, rec_id)
    if not row or row.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "recommendation_not_found")
    return row


def _owns_any_action_item(rec: Recommendation, user: User) -> bool:
    return any((it or {}).get("owner_user_id") == str(user.id) for it in (rec.action_items or []))


@router.get("", response_model=dict)
async def list_recommendations(
    periode_id: uuid.UUID | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    owner_user_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    stmt = select(Recommendation).where(Recommendation.deleted_at.is_(None))
    if periode_id is not None:
        stmt = stmt.where(Recommendation.target_periode_id == periode_id)
    if status_value is not None:
        stmt = stmt.where(Recommendation.status == status_value)
    rows = (await db.scalars(stmt.order_by(Recommendation.updated_at.desc()))).all()
    roles = {r.name for r in user.roles}
    filtered: list[Recommendation] = []
    for row in rows:
        if "pic_bidang" in roles and not (roles & {"super_admin", "asesor"}):
            if not _owns_any_action_item(row, user):
                continue
        if owner_user_id is not None and not any((it or {}).get("owner_user_id") == str(owner_user_id) for it in (row.action_items or [])):
            continue
        filtered.append(row)
    start = (page - 1) * page_size
    page_rows = filtered[start : start + page_size]
    return {
        "data": [RecommendationPublic.model_validate(r) for r in page_rows],
        "meta": {"page": page, "page_size": page_size, "total": len(filtered)},
    }


@router.get("/{rec_id}", response_model=RecommendationPublic)
async def get_recommendation(
    rec_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> RecommendationPublic:
    row = await _get_recommendation_or_404(db, rec_id)
    roles = {r.name for r in user.roles}
    if "pic_bidang" in roles and not (roles & {"super_admin", "asesor"}) and not _owns_any_action_item(row, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "recommendation_not_found")
    return RecommendationPublic.model_validate(row)


@router.post(
    "",
    response_model=RecommendationPublic,
    status_code=status.HTTP_201_CREATED,
    tags=["audit:recommendation"],
    dependencies=[Depends(require_role("asesor", "super_admin")), Depends(require_csrf)],
)
async def create_recommendation(
    payload: RecommendationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> RecommendationPublic:
    session = await db.get(AssessmentSession, payload.source_assessment_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "source_assessment_not_found")
    try:
        row = await create_recommendation_with_owner_resolution(
            db,
            source_assessment_id=payload.source_assessment_id,
            source_periode_id=session.periode_id,
            severity=payload.severity,
            deskripsi=payload.deskripsi,
            action_items=payload.action_items,
            target_periode_id=payload.target_periode_id,
            created_by=user.id,
        )
    except OwnerRequired as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"error": f"owner_required_for_action_item_{exc.index}"})
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = {"status": row.status.value, "severity": row.severity.value if hasattr(row.severity, "value") else row.severity}
    request.state.audit_entity_id = str(row.id)
    return RecommendationPublic.model_validate(row)


@router.patch(
    "/{rec_id}/progress",
    response_model=RecommendationPublic,
    tags=["audit:recommendation"],
    dependencies=[Depends(require_role("pic_bidang", "super_admin")), Depends(require_csrf)],
)
async def update_progress(
    rec_id: uuid.UUID,
    payload: RecommendationProgressUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> RecommendationPublic:
    row = await _get_recommendation_or_404(db, rec_id)
    roles = {r.name for r in user.roles}
    if "super_admin" not in roles and not _owns_any_action_item(row, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not_owner_of_any_action_item")
    request.state.audit_before = {"status": row.status.value, "progress_percent": row.progress_percent}
    if row.status == RecommendationStatus.OPEN:
        row.status = RecommendationStatus.IN_PROGRESS
    if payload.progress_percent is not None:
        row.progress_percent = payload.progress_percent
    if payload.progress_notes is not None:
        row.progress_notes = payload.progress_notes
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = {"status": row.status.value, "progress_percent": row.progress_percent}
    request.state.audit_entity_id = str(row.id)
    return RecommendationPublic.model_validate(row)


@router.post(
    "/{rec_id}/mark-completed",
    response_model=RecommendationPublic,
    tags=["audit:recommendation"],
    dependencies=[Depends(require_role("pic_bidang", "super_admin")), Depends(require_csrf)],
)
async def mark_completed(
    rec_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> RecommendationPublic:
    row = await _get_recommendation_or_404(db, rec_id)
    roles = {r.name for r in user.roles}
    if "super_admin" not in roles and not _owns_any_action_item(row, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not_owner_of_any_action_item")
    try:
        assert_mark_completed_allowed(row.status)
    except InvalidLifecycle as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    request.state.audit_before = {"status": row.status.value}
    row.status = RecommendationStatus.PENDING_REVIEW
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = {"status": row.status.value}
    request.state.audit_entity_id = str(row.id)
    return RecommendationPublic.model_validate(row)


@router.post(
    "/{rec_id}/verify-close",
    response_model=RecommendationPublic,
    tags=["audit:recommendation"],
    dependencies=[Depends(require_role("asesor", "super_admin")), Depends(require_csrf)],
)
async def verify_close(
    rec_id: uuid.UUID,
    payload: RecommendationVerifyClose,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> RecommendationPublic:
    row = await _get_recommendation_or_404(db, rec_id)
    try:
        assert_verify_close_allowed(row.status)
    except InvalidLifecycle as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    request.state.audit_before = {"status": row.status.value}
    row.status = RecommendationStatus.CLOSED
    row.asesor_close_notes = payload.asesor_close_notes
    row.closed_at = datetime.now(timezone.utc)
    row.closed_by = user.id
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = {"status": row.status.value}
    request.state.audit_entity_id = str(row.id)
    return RecommendationPublic.model_validate(row)


@router.post(
    "/{rec_id}/manual-close",
    response_model=RecommendationPublic,
    tags=["audit:recommendation"],
    dependencies=[Depends(require_role("asesor", "super_admin")), Depends(require_csrf)],
)
async def manual_close(
    rec_id: uuid.UUID,
    payload: RecommendationVerifyClose,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> RecommendationPublic:
    row = await _get_recommendation_or_404(db, rec_id)
    request.state.audit_before = {"status": row.status.value, "manual_close": True}
    row.status = RecommendationStatus.CLOSED
    row.asesor_close_notes = payload.asesor_close_notes
    row.closed_at = datetime.now(timezone.utc)
    row.closed_by = user.id
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = {"status": row.status.value, "manual_close": True}
    request.state.audit_entity_id = str(row.id)
    return RecommendationPublic.model_validate(row)
