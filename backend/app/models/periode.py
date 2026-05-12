"""Assessment periode model for Phase 2."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PeriodeStatus(StrEnum):
    DRAFT = "draft"
    AKTIF = "aktif"
    SELF_ASSESSMENT = "self_assessment"
    ASESMEN = "asesmen"
    FINALISASI = "finalisasi"
    CLOSED = "closed"


class Periode(Base):
    __tablename__ = "periode"
    __table_args__ = (
        UniqueConstraint("tahun", "triwulan", name="uq_periode_tahun_triwulan"),
        CheckConstraint("triwulan BETWEEN 1 AND 4", name="ck_periode_triwulan"),
        CheckConstraint("semester BETWEEN 1 AND 2", name="ck_periode_semester"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    tahun: Mapped[int] = mapped_column(Integer, nullable=False)
    triwulan: Mapped[int] = mapped_column(Integer, nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[PeriodeStatus] = mapped_column(
        ENUM(
            PeriodeStatus,
            name="periode_status",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'draft'::periode_status"),
    )
    tanggal_buka: Mapped[date | None] = mapped_column(Date, nullable=True)
    tanggal_tutup: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_transition_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_transition_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_transition_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
