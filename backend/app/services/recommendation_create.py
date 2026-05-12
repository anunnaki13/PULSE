"""Recommendation creation helpers with service-layer owner resolution."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_session import AssessmentSession
from app.models.assessment_session_bidang import AssessmentSessionBidang
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.recommendation import ActionItem


class OwnerRequired(ValueError):
    def __init__(self, index: int):
        super().__init__(f"owner_required_for_action_item_{index}")
        self.index = index


async def lookup_source_pic(db: AsyncSession, source_assessment_id: UUID) -> UUID | None:
    session = await db.get(AssessmentSession, source_assessment_id)
    if session is None:
        return None
    if session.bidang_id is not None:
        user = await db.scalar(
            select(User)
            .where(User.bidang_id == session.bidang_id, User.is_active.is_(True), User.deleted_at.is_(None))
            .order_by(User.created_at.asc())
        )
        return user.id if user else None
    bidang_ids = (
        await db.scalars(select(AssessmentSessionBidang.bidang_id).where(AssessmentSessionBidang.session_id == source_assessment_id))
    ).all()
    if not bidang_ids:
        return None
    user = await db.scalar(
        select(User)
        .where(User.bidang_id.in_(bidang_ids), User.is_active.is_(True), User.deleted_at.is_(None))
        .order_by(User.created_at.asc())
    )
    return user.id if user else None


async def resolve_default_owners(db: AsyncSession, items: list[ActionItem], source_assessment_id: UUID) -> list[ActionItem]:
    default_owner: UUID | None = None
    looked_up = False
    for i, item in enumerate(items):
        if item.owner_user_id is None:
            if not looked_up:
                default_owner = await lookup_source_pic(db, source_assessment_id)
                looked_up = True
            if default_owner is None:
                raise OwnerRequired(i)
            item.owner_user_id = default_owner
    return items


async def create_recommendation_with_owner_resolution(
    db: AsyncSession,
    *,
    source_assessment_id: UUID,
    source_periode_id: UUID,
    severity: str,
    deskripsi: str,
    action_items: list[ActionItem],
    target_periode_id: UUID,
    created_by: UUID,
) -> Recommendation:
    resolved = await resolve_default_owners(db, action_items, source_assessment_id)
    rec = Recommendation(
        source_assessment_id=source_assessment_id,
        source_periode_id=source_periode_id,
        target_periode_id=target_periode_id,
        severity=severity,
        deskripsi=deskripsi,
        action_items=[it.model_dump(mode="json") for it in resolved],
        created_by=created_by,
    )
    db.add(rec)
    await db.flush()
    return rec
