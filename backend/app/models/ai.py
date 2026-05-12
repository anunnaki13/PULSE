"""AI integration persistence models for Phase 5."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AiSuggestionLog(Base):
    __tablename__ = "ai_suggestion_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    suggestion_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    context_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    context_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion_text: Mapped[str] = mapped_column(Text, nullable=False)
    structured_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("'openrouter'"))
    pii_masked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, server_default=text("0"))
    accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    user_edited_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)


class AiInlineHelp(Base):
    __tablename__ = "ai_inline_help"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    indikator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("indikator.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    apa_itu: Mapped[str] = mapped_column(Text, nullable=False)
    formula_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    best_practice: Mapped[str] = mapped_column(Text, nullable=False)
    common_pitfalls: Mapped[str] = mapped_column(Text, nullable=False)
    related_indikator: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    generated_by_model: Mapped[str] = mapped_column(String(100), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)
