"""Pydantic DTOs for assessment sessions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl, model_validator

from app.schemas.recommendation import RecommendationCreate

SessionStateLit = Literal["draft", "submitted", "approved", "overridden", "revision_requested", "abandoned"]


class AssessmentSelfAssessmentPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: dict | None = None
    realisasi: Decimal | None = None
    target: Decimal | None = None
    catatan_pic: str | None = None
    link_eviden: HttpUrl | None = None


class AssessmentSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AsesorReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "override", "request_revision"]
    nilai_final: Decimal | None = None
    catatan_asesor: str | None = None
    inline_recommendations: list[RecommendationCreate] | None = None

    @model_validator(mode="after")
    def validate_override(self) -> "AsesorReview":
        if self.decision == "override":
            if self.nilai_final is None:
                raise ValueError("nilai_final is required when decision is override")
            if self.catatan_asesor is None or len(self.catatan_asesor) < 20:
                raise ValueError("catatan_asesor must be >= 20 chars when decision is override")
        elif self.nilai_final is not None:
            raise ValueError("nilai_final is only accepted when decision is override")
        return self


class AssessmentSessionPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    periode_id: UUID
    indikator_id: UUID
    bidang_id: UUID | None
    state: SessionStateLit
    payload: dict | None
    realisasi: Decimal | None
    target: Decimal | None
    pencapaian: Decimal | None
    nilai: Decimal | None
    nilai_final: Decimal | None
    catatan_pic: str | None
    catatan_asesor: str | None
    link_eviden: HttpUrl | None
    submitted_at: datetime | None
    asesor_reviewed_at: datetime | None
    updated_at: datetime


class AssessmentIndikatorPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    kode: str
    nama: str
    bobot: Decimal
    polaritas: Literal["positif", "negatif", "range"]
    formula: str | None


class AssessmentMlStreamPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    kode: str
    nama: str
    version: str
    structure: dict


class AssessmentSessionDetail(AssessmentSessionPublic):
    indikator: AssessmentIndikatorPublic | None = None
    ml_stream: AssessmentMlStreamPublic | None = None
