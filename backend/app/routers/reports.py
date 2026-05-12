"""Phase 4 report export endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import require_role
from app.deps.db import get_db
from app.models.assessment_session import AssessmentSession
from app.models.indikator import Indikator
from app.models.periode import Periode
from app.models.recommendation import Recommendation
from app.services.compliance_summary import compute_compliance_summary
from app.services.nko_calculator import get_or_create_snapshot
from app.services.report_exports import render_csv, render_pdf, render_word_html

router = APIRouter(prefix="/reports", tags=["reports"])


def _s(value: object) -> str:
    if isinstance(value, Decimal):
        return f"{value:.4f}"
    return "" if value is None else str(value)


def _download(content: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _periode_or_404(db: AsyncSession, periode_id: uuid.UUID) -> Periode:
    row = await db.get(Periode, periode_id)
    if row is None or row.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "periode_not_found")
    return row


def _artifact(title: str, format_value: str, rows: list[list[object]], filename_base: str) -> Response:
    if format_value == "excel":
        return _download(
            render_csv(["Section", "Metric", "Value", "Notes"], rows),
            f"{filename_base}.csv",
            "text/csv; charset=utf-8",
        )
    if format_value == "word":
        return _download(
            render_word_html(title, [("Ringkasan", rows)]),
            f"{filename_base}.doc",
            "application/msword",
        )
    if format_value == "pdf":
        return _download(
            render_pdf(title, [" | ".join(_s(cell) for cell in row) for row in rows]),
            f"{filename_base}.pdf",
            "application/pdf",
        )
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unsupported_report_format")


@router.get(
    "/nko-semester",
    dependencies=[Depends(require_role("super_admin", "admin_unit", "manajer_unit", "viewer"))],
)
async def export_nko_semester(
    periode_id: uuid.UUID,
    format: str = Query("pdf", pattern="^(pdf|excel|word)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    periode = await _periode_or_404(db, periode_id)
    snapshot = await get_or_create_snapshot(db, periode_id)
    compliance = await compute_compliance_summary(db, periode_id)
    rows = [
        ["Periode", "Nama", periode.nama, f"{periode.tahun} TW{periode.triwulan} SMT{periode.semester}"],
        ["NKO", "Gross Pilar I-V", snapshot.gross_pilar_total, "Sebelum pengurang compliance"],
        ["NKO", "Pengurang Compliance", snapshot.compliance_deduction, "Capped summary Phase 4"],
        ["NKO", "NKO Final", snapshot.nko_total, f"Source {snapshot.source}"],
        ["Compliance", "Laporan Telat", compliance.late_report_count, "Jumlah laporan terlambat"],
        ["Compliance", "Invalid", compliance.invalid_report_count, "Jumlah laporan invalid"],
        ["Compliance", "Total Pengurang", compliance.total_pengurang, f"Cap {compliance.cap}"],
    ]
    for pillar in (snapshot.breakdown or {}).get("pilar", []):
        rows.append(["Pilar", pillar.get("kode"), pillar.get("contribution"), pillar.get("nama")])
    return _artifact("Laporan NKO Semester PULSE", format, rows, f"pulse-nko-semester-{periode.tahun}-tw{periode.triwulan}")


@router.get(
    "/assessment-sheet",
    dependencies=[Depends(require_role("super_admin", "admin_unit", "manajer_unit", "viewer"))],
)
async def export_assessment_sheet(
    periode_id: uuid.UUID,
    format: str = Query("excel", pattern="^(pdf|excel|word)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    periode = await _periode_or_404(db, periode_id)
    rows = (
        await db.execute(
            select(AssessmentSession, Indikator)
            .join(Indikator, AssessmentSession.indikator_id == Indikator.id)
            .where(AssessmentSession.periode_id == periode_id, AssessmentSession.deleted_at.is_(None))
            .order_by(Indikator.kode, AssessmentSession.updated_at.desc())
        )
    ).all()
    export_rows = [["Periode", "Nama", periode.nama, "Assessment sheet"]]
    for session, indikator in rows:
        export_rows.append(
            [
                "Assessment",
                indikator.kode,
                session.state.value,
                f"realisasi={_s(session.realisasi)} target={_s(session.target)} nilai_final={_s(session.nilai_final)}",
            ]
        )
    return _artifact("Kertas Kerja Assessment PULSE", format, export_rows, f"pulse-assessment-{periode.tahun}-tw{periode.triwulan}")


@router.get(
    "/compliance-detail",
    dependencies=[Depends(require_role("super_admin", "admin_unit", "manajer_unit", "viewer"))],
)
async def export_compliance_detail(
    periode_id: uuid.UUID,
    format: str = Query("excel", pattern="^(pdf|excel|word)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    periode = await _periode_or_404(db, periode_id)
    summary = await compute_compliance_summary(db, periode_id)
    rows = [
        ["Periode", "Nama", periode.nama, f"Total pengurang {_s(summary.total_pengurang)}"],
        ["Summary", "Laporan", summary.report_count, f"late={summary.late_report_count} invalid={summary.invalid_report_count}"],
        ["Summary", "Komponen", summary.component_count, f"pengurang={_s(summary.komponen_pengurang)}"],
    ]
    for row in summary.rows:
        rows.append([row.get("type"), row.get("kode"), row.get("pengurang"), row.get("nama")])
    return _artifact("Detail Compliance PULSE", format, rows, f"pulse-compliance-{periode.tahun}-tw{periode.triwulan}")


@router.get(
    "/recommendation-tracker",
    dependencies=[Depends(require_role("super_admin", "admin_unit", "manajer_unit", "viewer"))],
)
async def export_recommendation_tracker(
    periode_id: uuid.UUID,
    format: str = Query("excel", pattern="^(pdf|excel|word)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    periode = await _periode_or_404(db, periode_id)
    rows = (
        await db.scalars(
            select(Recommendation)
            .where(
                Recommendation.deleted_at.is_(None),
                or_(Recommendation.source_periode_id == periode_id, Recommendation.target_periode_id == periode_id),
            )
            .order_by(Recommendation.updated_at.desc())
        )
    ).all()
    export_rows = [["Periode", "Nama", periode.nama, "Recommendation tracker"]]
    for recommendation in rows:
        export_rows.append(
            [
                "Recommendation",
                recommendation.severity.value,
                recommendation.status.value,
                f"{recommendation.progress_percent}% - {recommendation.deskripsi[:160]}",
            ]
        )
    return _artifact("Recommendation Tracker PULSE", format, export_rows, f"pulse-recommendations-{periode.tahun}-tw{periode.triwulan}")
