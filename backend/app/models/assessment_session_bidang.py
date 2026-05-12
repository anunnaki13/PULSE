"""Bidang membership for aggregate assessment sessions."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AssessmentSessionBidang(Base):
    __tablename__ = "assessment_session_bidang"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessment_session.id", ondelete="CASCADE"), primary_key=True)
    bidang_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bidang.id", ondelete="CASCADE"), primary_key=True)
