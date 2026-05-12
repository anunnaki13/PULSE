"""Assessment session model for PIC self-assessment and asesor review."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SessionState(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    OVERRIDDEN = "overridden"
    REVISION_REQUESTED = "revision_requested"
    ABANDONED = "abandoned"


class AssessmentSession(Base):
    __tablename__ = "assessment_session"
    __table_args__ = (
        UniqueConstraint("periode_id", "indikator_id", "bidang_id", name="uq_session_periode_indikator_bidang"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    periode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("periode.id", ondelete="CASCADE"), nullable=False, index=True)
    indikator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("indikator.id", ondelete="RESTRICT"), nullable=False, index=True)
    bidang_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bidang.id", ondelete="SET NULL"), nullable=True, index=True)
    state: Mapped[SessionState] = mapped_column(
        ENUM(
            SessionState,
            name="assessment_session_state",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'draft'::assessment_session_state"),
    )
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    realisasi: Mapped[object | None] = mapped_column(Numeric(20, 4), nullable=True)
    target: Mapped[object | None] = mapped_column(Numeric(20, 4), nullable=True)
    pencapaian: Mapped[object | None] = mapped_column(Numeric(10, 4), nullable=True)
    nilai: Mapped[object | None] = mapped_column(Numeric(10, 4), nullable=True)
    nilai_final: Mapped[object | None] = mapped_column(Numeric(10, 4), nullable=True)
    catatan_pic: Mapped[str | None] = mapped_column(Text, nullable=True)
    catatan_asesor: Mapped[str | None] = mapped_column(Text, nullable=True)
    link_eviden: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    asesor_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    asesor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
