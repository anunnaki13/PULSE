"""Compliance deduction calculation and summary service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import (
    ComplianceKomponen,
    ComplianceKomponenRealisasi,
    ComplianceLaporanDefinisi,
    ComplianceLaporanSubmission,
)

Q = Decimal("0.0001")
COMPLIANCE_CAP = Decimal("10.0000")


def q(value: Decimal) -> Decimal:
    return value.quantize(Q, rounding=ROUND_HALF_UP)


def calculate_laporan_pengurang(
    keterlambatan_hari: int,
    is_valid: bool,
    pengurang_per_keterlambatan: Decimal,
    pengurang_per_invaliditas: Decimal,
) -> Decimal:
    late = Decimal(keterlambatan_hari) * Decimal(pengurang_per_keterlambatan)
    invalid = Decimal("0") if is_valid else Decimal(pengurang_per_invaliditas)
    return q(late + invalid)


@dataclass(frozen=True)
class ComplianceSummary:
    periode_id: uuid.UUID
    report_count: int
    late_report_count: int
    invalid_report_count: int
    component_count: int
    laporan_pengurang: Decimal
    komponen_pengurang: Decimal
    total_pengurang_raw: Decimal
    total_pengurang: Decimal
    cap: Decimal
    rows: list[dict]

    @property
    def has_records(self) -> bool:
        return self.report_count > 0 or self.component_count > 0

    def as_dict(self) -> dict:
        return {
            "periode_id": self.periode_id,
            "report_count": self.report_count,
            "late_report_count": self.late_report_count,
            "invalid_report_count": self.invalid_report_count,
            "component_count": self.component_count,
            "laporan_pengurang": self.laporan_pengurang,
            "komponen_pengurang": self.komponen_pengurang,
            "total_pengurang_raw": self.total_pengurang_raw,
            "total_pengurang": self.total_pengurang,
            "cap": self.cap,
            "rows": self.rows,
        }


async def compute_compliance_summary(db: AsyncSession, periode_id: uuid.UUID) -> ComplianceSummary:
    report_rows = (
        await db.execute(
            select(ComplianceLaporanSubmission, ComplianceLaporanDefinisi)
            .join(ComplianceLaporanDefinisi, ComplianceLaporanSubmission.definisi_id == ComplianceLaporanDefinisi.id)
            .where(ComplianceLaporanSubmission.periode_id == periode_id)
            .order_by(ComplianceLaporanSubmission.bulan, ComplianceLaporanDefinisi.kode)
        )
    ).all()
    component_rows = (
        await db.execute(
            select(ComplianceKomponenRealisasi, ComplianceKomponen)
            .join(ComplianceKomponen, ComplianceKomponenRealisasi.komponen_id == ComplianceKomponen.id)
            .where(ComplianceKomponenRealisasi.periode_id == periode_id)
            .order_by(ComplianceKomponen.kode)
        )
    ).all()

    report_total = Decimal("0")
    rows: list[dict] = []
    late_count = 0
    invalid_count = 0
    for submission, definition in report_rows:
        pengurang = calculate_laporan_pengurang(
            submission.keterlambatan_hari,
            submission.is_valid,
            definition.pengurang_per_keterlambatan,
            definition.pengurang_per_invaliditas,
        )
        report_total += pengurang
        if submission.keterlambatan_hari > 0:
            late_count += 1
        if not submission.is_valid:
            invalid_count += 1
        rows.append(
            {
                "type": "laporan",
                "kode": definition.kode,
                "nama": definition.nama,
                "bulan": submission.bulan,
                "keterlambatan_hari": submission.keterlambatan_hari,
                "is_valid": submission.is_valid,
                "pengurang": float(pengurang),
            }
        )

    component_total = Decimal("0")
    for realization, component in component_rows:
        pengurang = q(min(Decimal(realization.pengurang), Decimal(component.pengurang_cap)))
        component_total += pengurang
        rows.append(
            {
                "type": "komponen",
                "kode": component.kode,
                "nama": component.nama,
                "nilai": float(realization.nilai),
                "pengurang": float(pengurang),
            }
        )

    raw = q(report_total + component_total)
    capped = q(min(raw, COMPLIANCE_CAP))
    return ComplianceSummary(
        periode_id=periode_id,
        report_count=len(report_rows),
        late_report_count=late_count,
        invalid_report_count=invalid_count,
        component_count=len(component_rows),
        laporan_pengurang=q(report_total),
        komponen_pengurang=q(component_total),
        total_pengurang_raw=raw,
        total_pengurang=capped,
        cap=COMPLIANCE_CAP,
        rows=rows,
    )
