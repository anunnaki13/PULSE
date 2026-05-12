"""Compliance tracker DTOs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ComplianceLaporanDefinisiPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    kode: str
    nama: str
    default_due_day: int
    pengurang_per_keterlambatan: Decimal
    pengurang_per_invaliditas: Decimal
    is_active: bool


class ComplianceLaporanSubmissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periode_id: UUID
    definisi_id: UUID
    bulan: int = Field(ge=1, le=12)
    tanggal_jatuh_tempo: date
    tanggal_submit: date | None = None
    is_valid: bool = True
    catatan: str | None = Field(default=None, max_length=10_000)


class ComplianceLaporanSubmissionPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    periode_id: UUID
    definisi_id: UUID
    bulan: int
    tanggal_jatuh_tempo: date
    tanggal_submit: date | None
    keterlambatan_hari: int
    is_valid: bool
    catatan: str | None
    created_at: datetime
    updated_at: datetime


class ComplianceKomponenPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    kode: str
    nama: str
    formula: dict
    pengurang_cap: Decimal
    is_active: bool


class ComplianceKomponenRealisasiCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periode_id: UUID
    komponen_id: UUID
    nilai: Decimal
    pengurang: Decimal = Field(ge=0)
    payload: dict = Field(default_factory=dict)
    catatan: str | None = Field(default=None, max_length=10_000)


class ComplianceKomponenRealisasiPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    periode_id: UUID
    komponen_id: UUID
    nilai: Decimal
    pengurang: Decimal
    payload: dict
    catatan: str | None
    created_at: datetime
    updated_at: datetime


class ComplianceSummaryPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periode_id: UUID
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
