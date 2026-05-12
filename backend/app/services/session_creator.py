"""Create assessment sessions from indikator-applicable-bidang mappings."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_session import AssessmentSession
from app.models.assessment_session_bidang import AssessmentSessionBidang
from app.models.indikator_applicable_bidang import IndikatorApplicableBidang


async def create_sessions_for_periode(db: AsyncSession, periode_id) -> int:
    """Idempotently create per-bidang and aggregate sessions for a periode."""
    rows = (
        await db.scalars(
            select(IndikatorApplicableBidang).order_by(
                IndikatorApplicableBidang.indikator_id,
                IndikatorApplicableBidang.bidang_id,
            )
        )
    ).all()
    grouped: dict[object, list[IndikatorApplicableBidang]] = defaultdict(list)
    for row in rows:
        grouped[row.indikator_id].append(row)

    created = 0
    for indikator_id, applicable in grouped.items():
        aggregate = [r for r in applicable if r.is_aggregate]
        per_bidang = [r for r in applicable if not r.is_aggregate]

        if aggregate:
            existing = await db.scalar(
                select(AssessmentSession).where(
                    AssessmentSession.periode_id == periode_id,
                    AssessmentSession.indikator_id == indikator_id,
                    AssessmentSession.bidang_id.is_(None),
                )
            )
            if existing is None:
                existing = AssessmentSession(periode_id=periode_id, indikator_id=indikator_id, bidang_id=None)
                db.add(existing)
                await db.flush()
                created += 1
            for r in aggregate:
                link = await db.get(AssessmentSessionBidang, {"session_id": existing.id, "bidang_id": r.bidang_id})
                if link is None:
                    db.add(AssessmentSessionBidang(session_id=existing.id, bidang_id=r.bidang_id))

        for r in per_bidang:
            existing = await db.scalar(
                select(AssessmentSession).where(
                    AssessmentSession.periode_id == periode_id,
                    AssessmentSession.indikator_id == indikator_id,
                    AssessmentSession.bidang_id == r.bidang_id,
                )
            )
            if existing is None:
                db.add(AssessmentSession(periode_id=periode_id, indikator_id=indikator_id, bidang_id=r.bidang_id))
                created += 1
    await db.flush()
    return created
