"""Compliance tracker models for Phase 4."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Computed, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ComplianceLaporanDefinisi(Base):
    __tablename__ = "compliance_laporan_definisi"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    kode: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    default_due_day: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("10"))
    pengurang_per_keterlambatan: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, server_default=text("0.039"))
    pengurang_per_invaliditas: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, server_default=text("0.039"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)


class ComplianceLaporanSubmission(Base):
    __tablename__ = "compliance_laporan_submission"
    __table_args__ = (
        UniqueConstraint("periode_id", "definisi_id", "bulan", name="uq_compliance_laporan_submission_period_def_month"),
        CheckConstraint("bulan BETWEEN 1 AND 12", name="ck_compliance_submission_bulan"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    periode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("periode.id", ondelete="CASCADE"), nullable=False, index=True)
    definisi_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("compliance_laporan_definisi.id", ondelete="RESTRICT"), nullable=False, index=True)
    bulan: Mapped[int] = mapped_column(Integer, nullable=False)
    tanggal_jatuh_tempo: Mapped[date] = mapped_column(Date, nullable=False)
    tanggal_submit: Mapped[date | None] = mapped_column(Date, nullable=True)
    keterlambatan_hari: Mapped[int] = mapped_column(
        Integer,
        Computed(
            "CASE WHEN tanggal_submit IS NULL OR tanggal_submit <= tanggal_jatuh_tempo "
            "THEN 0 ELSE tanggal_submit - tanggal_jatuh_tempo END",
            persisted=True,
        ),
        nullable=False,
    )
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    catatan: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)


class ComplianceKomponen(Base):
    __tablename__ = "compliance_komponen"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    kode: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    formula: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    pengurang_cap: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, server_default=text("10"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)


class ComplianceKomponenRealisasi(Base):
    __tablename__ = "compliance_komponen_realisasi"
    __table_args__ = (UniqueConstraint("periode_id", "komponen_id", name="uq_compliance_komponen_realisasi_period_component"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    periode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("periode.id", ondelete="CASCADE"), nullable=False, index=True)
    komponen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("compliance_komponen.id", ondelete="RESTRICT"), nullable=False, index=True)
    nilai: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    pengurang: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default=text("0"))
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    catatan: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)
