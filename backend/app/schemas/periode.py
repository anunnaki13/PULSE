"""Pydantic DTOs for periode lifecycle."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PeriodeStatusLit = Literal["draft", "aktif", "self_assessment", "asesmen", "finalisasi", "closed"]


class PeriodeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tahun: int = Field(ge=2024, le=2099)
    triwulan: int = Field(ge=1, le=4)
    semester: int = Field(ge=1, le=2)
    nama: str = Field(min_length=1, max_length=255)
    tanggal_buka: date | None = None
    tanggal_tutup: date | None = None


class PeriodeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nama: str | None = Field(default=None, min_length=1, max_length=255)
    tanggal_buka: date | None = None
    tanggal_tutup: date | None = None


class PeriodeTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_state: PeriodeStatusLit
    reason: str | None = None


class PeriodePublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tahun: int
    triwulan: int
    semester: int
    nama: str
    status: PeriodeStatusLit
    tanggal_buka: date | None
    tanggal_tutup: date | None
    last_transition_reason: str | None
    last_transition_by: UUID | None
    last_transition_at: datetime | None
    created_at: datetime
    updated_at: datetime
