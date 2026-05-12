from __future__ import annotations

import uuid

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def audit_emit_immediately(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    action: str,
    before: dict | None,
    after: dict | None,
    entity_type: str | None,
    entity_id: uuid.UUID | None,
    request: Request | None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_data=before,
            after_data=after,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    )
    await db.commit()
