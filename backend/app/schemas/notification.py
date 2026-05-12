"""Pydantic DTOs for notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

NotificationTypeLit = Literal[
    "assessment_due",
    "review_pending",
    "recommendation_assigned",
    "deadline_approaching",
    "periode_closed",
    "system_announcement",
]


class NotificationPublic(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    user_id: UUID
    type: NotificationTypeLit
    title: str
    body: str
    payload: dict
    read_at: datetime | None
    created_at: datetime
