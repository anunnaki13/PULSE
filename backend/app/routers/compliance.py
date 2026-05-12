"""Compliance tracker API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import current_user, require_role
from app.deps.csrf import require_csrf
from app.deps.db import get_db
from app.models.compliance import (
    ComplianceKomponen,
    ComplianceKomponenRealisasi,
    ComplianceLaporanDefinisi,
    ComplianceLaporanSubmission,
)
from app.models.user import User
from app.schemas.compliance import (
    ComplianceKomponenPublic,
    ComplianceKomponenRealisasiCreate,
    ComplianceKomponenRealisasiPublic,
    ComplianceLaporanDefinisiPublic,
    ComplianceLaporanSubmissionCreate,
    ComplianceLaporanSubmissionPublic,
    ComplianceSummaryPublic,
)
from app.services.compliance_summary import compute_compliance_summary
from app.services.dashboard_broadcast import broadcast_nko_updated
from app.services.nko_calculator import recompute_nko_snapshot

router = APIRouter(prefix="/compliance", tags=["compliance"])


def _page(data: list, page: int, page_size: int, total: int) -> dict:
    return {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}}


async def _recompute_and_broadcast(db: AsyncSession, periode_id: uuid.UUID) -> None:
    snapshot = await recompute_nko_snapshot(db, periode_id, source="live")
    await broadcast_nko_updated(periode_id, snapshot.nko_total)


@router.get("/laporan-definisi", response_model=dict)
async def list_laporan_definisi(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
) -> dict:
    q = select(ComplianceLaporanDefinisi).where(ComplianceLaporanDefinisi.is_active.is_(True))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        await db.scalars(
            q.order_by(ComplianceLaporanDefinisi.kode)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return _page([ComplianceLaporanDefinisiPublic.model_validate(row) for row in rows], page, page_size, int(total or 0))


@router.get("/submissions", response_model=dict)
async def list_laporan_submissions(
    periode_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
) -> dict:
    q = select(ComplianceLaporanSubmission).where(ComplianceLaporanSubmission.periode_id == periode_id)
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        await db.scalars(
            q.order_by(ComplianceLaporanSubmission.bulan, ComplianceLaporanSubmission.definisi_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return _page([ComplianceLaporanSubmissionPublic.model_validate(row) for row in rows], page, page_size, int(total or 0))


@router.post(
    "/submissions",
    response_model=ComplianceLaporanSubmissionPublic,
    status_code=status.HTTP_201_CREATED,
    tags=["audit:compliance_submission"],
    dependencies=[Depends(require_role("super_admin", "admin_unit")), Depends(require_csrf)],
)
async def upsert_laporan_submission(
    payload: ComplianceLaporanSubmissionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> ComplianceLaporanSubmissionPublic:
    definition = await db.get(ComplianceLaporanDefinisi, payload.definisi_id)
    if definition is None or not definition.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "laporan_definisi_not_found")

    row = await db.scalar(
        select(ComplianceLaporanSubmission).where(
            ComplianceLaporanSubmission.periode_id == payload.periode_id,
            ComplianceLaporanSubmission.definisi_id == payload.definisi_id,
            ComplianceLaporanSubmission.bulan == payload.bulan,
        )
    )
    request.state.audit_before = ComplianceLaporanSubmissionPublic.model_validate(row).model_dump(mode="json") if row else None
    if row is None:
        row = ComplianceLaporanSubmission(created_by=user.id, **payload.model_dump())
        db.add(row)
    else:
        for key, value in payload.model_dump().items():
            setattr(row, key, value)
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = ComplianceLaporanSubmissionPublic.model_validate(row).model_dump(mode="json")
    request.state.audit_entity_id = str(row.id)
    await _recompute_and_broadcast(db, payload.periode_id)
    return ComplianceLaporanSubmissionPublic.model_validate(row)


@router.get("/summary", response_model=ComplianceSummaryPublic)
async def compliance_summary(
    periode_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
) -> ComplianceSummaryPublic:
    return ComplianceSummaryPublic(**(await compute_compliance_summary(db, periode_id)).as_dict())


@router.get("/components", response_model=dict)
async def list_components(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
) -> dict:
    q = select(ComplianceKomponen).where(ComplianceKomponen.is_active.is_(True))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        await db.scalars(
            q.order_by(ComplianceKomponen.kode)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return _page([ComplianceKomponenPublic.model_validate(row) for row in rows], page, page_size, int(total or 0))


@router.post(
    "/component-realizations",
    response_model=ComplianceKomponenRealisasiPublic,
    status_code=status.HTTP_201_CREATED,
    tags=["audit:compliance_component"],
    dependencies=[Depends(require_role("super_admin", "admin_unit")), Depends(require_csrf)],
)
async def upsert_component_realization(
    payload: ComplianceKomponenRealisasiCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> ComplianceKomponenRealisasiPublic:
    component = await db.get(ComplianceKomponen, payload.komponen_id)
    if component is None or not component.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "compliance_component_not_found")

    row = await db.scalar(
        select(ComplianceKomponenRealisasi).where(
            ComplianceKomponenRealisasi.periode_id == payload.periode_id,
            ComplianceKomponenRealisasi.komponen_id == payload.komponen_id,
        )
    )
    request.state.audit_before = ComplianceKomponenRealisasiPublic.model_validate(row).model_dump(mode="json") if row else None
    if row is None:
        row = ComplianceKomponenRealisasi(created_by=user.id, **payload.model_dump())
        db.add(row)
    else:
        for key, value in payload.model_dump().items():
            setattr(row, key, value)
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = ComplianceKomponenRealisasiPublic.model_validate(row).model_dump(mode="json")
    request.state.audit_entity_id = str(row.id)
    await _recompute_and_broadcast(db, payload.periode_id)
    return ComplianceKomponenRealisasiPublic.model_validate(row)
