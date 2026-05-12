"""Recommendation lifecycle model."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecommendationStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    CLOSED = "closed"
    CARRIED_OVER = "carried_over"


class RecommendationSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Recommendation(Base):
    __tablename__ = "recommendation"
    __table_args__ = (CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_recommendation_progress_percent"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    source_assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessment_session.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_periode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("periode.id", ondelete="RESTRICT"), nullable=False, index=True)
    target_periode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("periode.id", ondelete="RESTRICT"), nullable=False, index=True)
    carried_from_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("recommendation.id", ondelete="SET NULL"), nullable=True)
    carried_to_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("recommendation.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[RecommendationStatus] = mapped_column(
        ENUM(
            RecommendationStatus,
            name="recommendation_status",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'open'::recommendation_status"),
    )
    severity: Mapped[RecommendationSeverity] = mapped_column(
        ENUM(
            RecommendationSeverity,
            name="recommendation_severity",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    deskripsi: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    progress_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    asesor_close_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
