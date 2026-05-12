"""Assessment session routes for PIC and asesor workflow."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import current_user, require_role
from app.deps.csrf import require_csrf
from app.deps.db import get_db
from app.models.assessment_session import AssessmentSession, SessionState
from app.models.assessment_session_bidang import AssessmentSessionBidang
from app.models.indikator import Indikator
from app.models.ml_stream import MlStream
from app.models.recommendation import RecommendationStatus
from app.models.user import User
from app.schemas.assessment import (
    AssessmentIndikatorPublic,
    AssessmentMlStreamPublic,
    AssessmentSelfAssessmentPatch,
    AssessmentSessionDetail,
    AssessmentSessionPublic,
    AssessmentSubmit,
    AsesorReview,
)
from app.services.pencapaian import compute_pair
from app.services.dashboard_broadcast import broadcast_nko_updated
from app.services.nko_calculator import recompute_nko_snapshot
from app.services.recommendation_create import create_recommendation_with_owner_resolution

router = APIRouter(prefix="/assessment/sessions", tags=["assessment-sessions"])


async def _get_session_or_404(db: AsyncSession, session_id: uuid.UUID) -> AssessmentSession:
    row = await db.get(AssessmentSession, session_id)
    if not row or row.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "assessment_session_not_found")
    return row


async def _indikator_for_session(db: AsyncSession, session: AssessmentSession) -> Indikator:
    row = await db.get(Indikator, session.indikator_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "indikator_not_found")
    return row


async def _ml_stream_for_indikator(db: AsyncSession, indikator: Indikator) -> MlStream | None:
    code = "OUTAGE" if indikator.kode in {"OM", "OUTAGE"} else indikator.kode
    return await db.scalar(select(MlStream).where(MlStream.kode == code, MlStream.deleted_at.is_(None)))


async def _session_detail(db: AsyncSession, session: AssessmentSession) -> AssessmentSessionDetail:
    detail = AssessmentSessionDetail.model_validate(session)
    indikator = await _indikator_for_session(db, session)
    detail.indikator = AssessmentIndikatorPublic.model_validate(indikator)
    stream = await _ml_stream_for_indikator(db, indikator)
    if stream is not None:
        detail.ml_stream = AssessmentMlStreamPublic.model_validate(stream)
    return detail


async def _user_can_access_session(db: AsyncSession, user: User, session: AssessmentSession) -> bool:
    roles = {r.name for r in user.roles}
    if roles & {"super_admin", "asesor"}:
        return True
    if "pic_bidang" not in roles:
        return False
    if session.bidang_id is not None:
        return user.bidang_id == session.bidang_id
    bidang_ids = (
        await db.scalars(select(AssessmentSessionBidang.bidang_id).where(AssessmentSessionBidang.session_id == session.id))
    ).all()
    return user.bidang_id in set(bidang_ids)


def _validate_submit_gate(payload: dict | None) -> list[str]:
    offenders: list[str] = []
    for key, value in (payload or {}).items():
        if not isinstance(value, dict):
            continue
        numeric = value.get("value")
        tidak_dinilai = bool(value.get("tidak_dinilai"))
        reason = value.get("tidak_dinilai_reason")
        if numeric is None and not (tidak_dinilai and isinstance(reason, str) and len(reason) >= 10):
            offenders.append(str(key))
    return offenders


def _normalize_url(value) -> str | None:
    return str(value) if value is not None else None


@router.get("", response_model=dict)
async def list_sessions(
    periode_id: uuid.UUID | None = None,
    state: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    stmt = select(AssessmentSession).where(AssessmentSession.deleted_at.is_(None))
    if periode_id is not None:
        stmt = stmt.where(AssessmentSession.periode_id == periode_id)
    if state is not None:
        stmt = stmt.where(AssessmentSession.state == state)

    rows = (await db.scalars(stmt.order_by(AssessmentSession.updated_at.desc()))).all()
    visible: list[AssessmentSession] = []
    for row in rows:
        if await _user_can_access_session(db, user, row):
            visible.append(row)
    start = (page - 1) * page_size
    page_rows = visible[start : start + page_size]
    return {
        "data": [await _session_detail(db, r) for r in page_rows],
        "meta": {"page": page, "page_size": page_size, "total": len(visible)},
    }


@router.get("/{session_id}", response_model=AssessmentSessionDetail)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AssessmentSessionDetail:
    row = await _get_session_or_404(db, session_id)
    if not await _user_can_access_session(db, user, row):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "assessment_session_not_found")
    return await _session_detail(db, row)


@router.patch(
    "/{session_id}/self-assessment",
    response_model=AssessmentSessionPublic,
    tags=["audit:assessment_session"],
    dependencies=[Depends(require_role("pic_bidang", "super_admin")), Depends(require_csrf)],
)
async def patch_self_assessment(
    session_id: uuid.UUID,
    payload: AssessmentSelfAssessmentPatch,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AssessmentSessionDetail:
    row = await _get_session_or_404(db, session_id)
    if not await _user_can_access_session(db, user, row):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "session_out_of_scope")
    if row.state not in {SessionState.DRAFT, SessionState.REVISION_REQUESTED}:
        raise HTTPException(status.HTTP_409_CONFLICT, "session_not_editable")
    request.state.audit_before = {"state": row.state.value, "updated_at": row.updated_at.isoformat()}
    data = payload.model_dump(exclude_unset=True)
    if "payload" in data:
        row.payload = data["payload"]
    if "realisasi" in data:
        row.realisasi = data["realisasi"]
    if "target" in data:
        row.target = data["target"]
    if "catatan_pic" in data:
        row.catatan_pic = data["catatan_pic"]
    if "link_eviden" in data:
        row.link_eviden = _normalize_url(data["link_eviden"])
    indikator = await _indikator_for_session(db, row)
    row.pencapaian, row.nilai = compute_pair(
        Decimal(row.realisasi) if row.realisasi is not None else None,
        Decimal(row.target) if row.target is not None else None,
        indikator.polaritas,
    )
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = {"state": row.state.value, "updated_at": row.updated_at.isoformat()}
    request.state.audit_entity_id = str(row.id)
    return await _session_detail(db, row)


@router.post(
    "/{session_id}/submit",
    response_model=AssessmentSessionPublic,
    tags=["audit:assessment_session"],
    dependencies=[Depends(require_role("pic_bidang", "super_admin")), Depends(require_csrf)],
)
async def submit_session(
    session_id: uuid.UUID,
    _: AssessmentSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AssessmentSessionDetail:
    row = await _get_session_or_404(db, session_id)
    if not await _user_can_access_session(db, user, row):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "session_out_of_scope")
    offenders = _validate_submit_gate(row.payload)
    if offenders:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"error": "submit_gate_failed", "offending": offenders})
    indikator = await _indikator_for_session(db, row)
    row.pencapaian, row.nilai = compute_pair(
        Decimal(row.realisasi) if row.realisasi is not None else None,
        Decimal(row.target) if row.target is not None else None,
        indikator.polaritas,
    )
    request.state.audit_before = {"state": row.state.value}
    row.state = SessionState.SUBMITTED
    row.submitted_at = datetime.now(timezone.utc)
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = {"state": row.state.value}
    request.state.audit_entity_id = str(row.id)
    return await _session_detail(db, row)


@router.post(
    "/{session_id}/withdraw",
    response_model=AssessmentSessionPublic,
    tags=["audit:assessment_session"],
    dependencies=[Depends(require_role("pic_bidang", "super_admin")), Depends(require_csrf)],
)
async def withdraw_session(
    session_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AssessmentSessionDetail:
    row = await _get_session_or_404(db, session_id)
    if not await _user_can_access_session(db, user, row):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "session_out_of_scope")
    if row.state != SessionState.SUBMITTED or row.asesor_user_id is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "session_cannot_be_withdrawn")
    request.state.audit_before = {"state": row.state.value}
    row.state = SessionState.DRAFT
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = {"state": row.state.value}
    request.state.audit_entity_id = str(row.id)
    return await _session_detail(db, row)


@router.post(
    "/{session_id}/asesor-review",
    response_model=AssessmentSessionPublic,
    tags=["audit:assessment_session"],
    dependencies=[Depends(require_role("asesor", "super_admin")), Depends(require_csrf)],
)
async def asesor_review(
    session_id: uuid.UUID,
    payload: AsesorReview,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AssessmentSessionDetail:
    row = await _get_session_or_404(db, session_id)
    if payload.decision == "override":
        if payload.nilai_final is None or payload.catatan_asesor is None or len(payload.catatan_asesor) < 20:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "override_requires_nilai_final_and_catatan_asesor")
    request.state.audit_before = {"state": row.state.value, "nilai_final": str(row.nilai_final) if row.nilai_final is not None else None}
    row.asesor_user_id = user.id
    row.asesor_reviewed_at = datetime.now(timezone.utc)
    row.catatan_asesor = payload.catatan_asesor
    if payload.decision == "approve":
        row.state = SessionState.APPROVED
        row.nilai_final = row.nilai
    elif payload.decision == "override":
        row.state = SessionState.OVERRIDDEN
        row.nilai_final = payload.nilai_final
    else:
        row.state = SessionState.REVISION_REQUESTED
        row.nilai_final = None
    for rec in payload.inline_recommendations or []:
        await create_recommendation_with_owner_resolution(
            db,
            source_assessment_id=row.id,
            source_periode_id=row.periode_id,
            severity=rec.severity,
            deskripsi=rec.deskripsi,
            action_items=rec.action_items,
            target_periode_id=rec.target_periode_id,
            created_by=user.id,
        )
    await db.flush()
    await db.commit()
    await db.refresh(row)
    if row.state in {SessionState.APPROVED, SessionState.OVERRIDDEN}:
        snapshot = await recompute_nko_snapshot(db, row.periode_id, changed_indikator_id=row.indikator_id)
        await broadcast_nko_updated(row.periode_id, snapshot.nko_total, row.indikator_id)
    request.state.audit_after = {"state": row.state.value, "nilai_final": str(row.nilai_final) if row.nilai_final is not None else None}
    request.state.audit_entity_id = str(row.id)
    return await _session_detail(db, row)
