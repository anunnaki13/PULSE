"""Pydantic DTOs for audit log rows."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class AuditLogPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    user_id: UUID | None
    action: str
    entity_type: str | None
    entity_id: UUID | None
    before_data: dict | None
    after_data: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    @field_validator("ip_address", mode="before")
    @classmethod
    def coerce_ip_address(cls, value):
        return None if value is None else str(value)
