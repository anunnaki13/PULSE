"""Pydantic DTOs for Phase 5 AI features."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recommendation import ActionItem, RecommendationSeverityLit


class AiStatusPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    available: bool
    mode: Literal["mock", "openrouter", "unavailable"]
    routine_model: str
    complex_model: str
    message: str


class AiAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment_session_id: UUID
    user_note: str | None = Field(default=None, max_length=10_000)


class AiSuggestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    log_id: UUID
    suggestion_type: str
    text: str
    model_used: str
    fallback_used: bool
    pii_masked: bool


class AiDraftRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: RecommendationSeverityLit
    deskripsi: str
    action_items: list[ActionItem]
    target_outcome: str


class AiDraftRecommendationResponse(AiSuggestionResponse):
    structured: AiDraftRecommendation


class AiAnomalyResponse(AiSuggestionResponse):
    classification: Literal["legitimate_improvement", "data_entry_error", "needs_verification", "suspicious"]
    risk_score: int = Field(ge=0, le=100)
    reasons: list[str]


class AiInlineHelpPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    indikator_id: UUID
    apa_itu: str
    formula_explanation: str
    best_practice: str
    common_pitfalls: str
    related_indikator: list
    generated_by_model: str
    generated_at: datetime
    expires_at: datetime | None


class AiComparativeAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment_session_id: UUID


class AiComparativeAnalysisResponse(AiSuggestionResponse):
    trend: list[dict]


class AiFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: bool
    user_edited_version: str | None = Field(default=None, max_length=20_000)


class AiSourceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str
    section: str
    page: int | None = None
    score: float = Field(ge=0, le=1)


class AiRagChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=3, max_length=4000)


class AiRagChatResponse(AiSuggestionResponse):
    sources: list[AiSourceCitation]


class AiPeriodeSummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periode_id: UUID


class AiPeriodeSummaryResponse(AiSuggestionResponse):
    periode_id: UUID
    word_count: int
    sources: list[AiSourceCitation]


class AiActionPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periode_id: UUID
    assessment_session_id: UUID | None = None
    focus: str | None = Field(default=None, max_length=2000)


class AiActionPlanResponse(AiSuggestionResponse):
    periode_id: UUID
    structured: AiDraftRecommendation
    sources: list[AiSourceCitation]
