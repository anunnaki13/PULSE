"""Executive dashboard API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import require_role
from app.deps.csrf import require_csrf
from app.deps.db import get_db
from app.schemas.dashboard import DashboardExecutiveResponse, DashboardHeatmapResponse, DashboardTrendResponse, NkoSnapshotPublic
from app.services.dashboard_broadcast import broadcast_nko_updated
from app.services.nko_calculator import get_or_create_snapshot, maturity_heatmap, recompute_nko_snapshot, trend_for_indikator

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/executive",
    response_model=DashboardExecutiveResponse,
    dependencies=[Depends(require_role("manajer_unit", "super_admin", "viewer"))],
)
async def executive_dashboard(
    periode_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DashboardExecutiveResponse:
    snapshot = await get_or_create_snapshot(db, periode_id)
    return DashboardExecutiveResponse(snapshot=NkoSnapshotPublic.model_validate(snapshot), data=snapshot.breakdown)


@router.get(
    "/maturity-heatmap",
    response_model=DashboardHeatmapResponse,
    dependencies=[Depends(require_role("manajer_unit", "super_admin", "viewer"))],
)
async def get_maturity_heatmap(
    tahun: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
) -> DashboardHeatmapResponse:
    return DashboardHeatmapResponse(tahun=tahun, data=await maturity_heatmap(db, tahun))


@router.get(
    "/trend",
    response_model=DashboardTrendResponse,
    dependencies=[Depends(require_role("manajer_unit", "super_admin", "viewer"))],
)
async def get_dashboard_trend(
    indikator_id: uuid.UUID,
    tahun: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
) -> DashboardTrendResponse:
    return DashboardTrendResponse(indikator_id=indikator_id, tahun=tahun, data=await trend_for_indikator(db, indikator_id, tahun))


@router.post(
    "/recompute",
    response_model=NkoSnapshotPublic,
    tags=["audit:nko_snapshot"],
    dependencies=[Depends(require_role("super_admin", "admin_unit")), Depends(require_csrf)],
)
async def recompute_dashboard(
    request: Request,
    periode_id: uuid.UUID,
    source: str = Query("live", pattern="^(live|fallback|demo)$"),
    db: AsyncSession = Depends(get_db),
) -> NkoSnapshotPublic:
    snapshot = await recompute_nko_snapshot(db, periode_id, source=source)
    await broadcast_nko_updated(periode_id, snapshot.nko_total)
    request.state.audit_before = None
    request.state.audit_after = {"nko_total": str(snapshot.nko_total), "source": snapshot.source}
    request.state.audit_entity_id = str(snapshot.id)
    return NkoSnapshotPublic.model_validate(snapshot)
