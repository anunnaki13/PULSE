"""Pydantic DTOs for recommendations."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RecommendationStatusLit = Literal["open", "in_progress", "pending_review", "closed", "carried_over"]
RecommendationSeverityLit = Literal["low", "medium", "high", "critical"]


class ActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Annotated[str, Field(min_length=1, max_length=2000)]
    deadline: date | None = None
    owner_user_id: UUID | None = None


class RecommendationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_assessment_id: UUID
    severity: RecommendationSeverityLit
    deskripsi: Annotated[str, Field(min_length=10, max_length=10_000)]
    action_items: Annotated[list[ActionItem], Field(min_length=1)]
    target_periode_id: UUID


class RecommendationProgressUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    progress_percent: Annotated[int, Field(ge=0, le=100)] | None = None
    progress_notes: str | None = Field(default=None, max_length=10_000)


class RecommendationMarkCompleted(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RecommendationVerifyClose(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asesor_close_notes: str = Field(min_length=1, max_length=10_000)


class RecommendationPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    source_assessment_id: UUID
    source_periode_id: UUID
    target_periode_id: UUID
    carried_from_id: UUID | None
    carried_to_id: UUID | None
    status: RecommendationStatusLit
    severity: RecommendationSeverityLit
    deskripsi: str
    action_items: list[ActionItem]
    progress_percent: int
    progress_notes: str | None
    asesor_close_notes: str | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
