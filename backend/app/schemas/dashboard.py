"""Dashboard and NKO snapshot DTOs."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NkoSnapshotPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    periode_id: UUID
    nko_total: Decimal
    gross_pilar_total: Decimal
    compliance_deduction: Decimal
    breakdown: dict[str, Any]
    source: Literal["live", "fallback", "demo"]
    is_final: bool
    updated_at: datetime


class DashboardRecomputeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["live", "fallback", "demo"] = "live"


class DashboardExecutiveResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot: NkoSnapshotPublic
    data: dict[str, Any]


class DashboardHeatmapResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tahun: int
    data: list[dict[str, Any]]


class DashboardTrendResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    indikator_id: UUID
    tahun: int
    data: list[dict[str, Any]]
