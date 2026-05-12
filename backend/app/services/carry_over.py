"""Recommendation carry-over and periode-close side effects."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_session import AssessmentSession, SessionState
from app.models.periode import Periode
from app.models.recommendation import Recommendation, RecommendationStatus


ACTIVE_RECOMMENDATION_STATES = {
    RecommendationStatus.OPEN,
    RecommendationStatus.IN_PROGRESS,
    RecommendationStatus.PENDING_REVIEW,
}


def _status_value(status: RecommendationStatus | str) -> str:
    return status.value if isinstance(status, RecommendationStatus) else status


async def resolve_next_periode(db: AsyncSession, periode: Periode) -> Periode | None:
    stmt = (
        select(Periode)
        .where(
            Periode.deleted_at.is_(None),
            ((Periode.tahun > periode.tahun) | ((Periode.tahun == periode.tahun) & (Periode.triwulan > periode.triwulan))),
        )
        .order_by(Periode.tahun.asc(), Periode.triwulan.asc())
    )
    return await db.scalar(stmt)


async def close_periode_with_carry_over(db: AsyncSession, periode: Periode) -> dict:
    abandoned = 0
    sessions = (
        await db.scalars(
            select(AssessmentSession).where(
                AssessmentSession.periode_id == periode.id,
                AssessmentSession.state == SessionState.DRAFT,
            )
        )
    ).all()
    for session in sessions:
        session.state = SessionState.ABANDONED
        abandoned += 1

    next_periode = await resolve_next_periode(db, periode)
    carried = 0
    if next_periode is not None:
        recs = (
            await db.scalars(
                select(Recommendation).where(
                    Recommendation.source_periode_id == periode.id,
                    Recommendation.carried_to_id.is_(None),
                )
            )
        ).all()
        for rec in recs:
            if _status_value(rec.status) not in {s.value for s in ACTIVE_RECOMMENDATION_STATES}:
                continue
            new_rec = Recommendation(
                source_assessment_id=rec.source_assessment_id,
                source_periode_id=rec.source_periode_id,
                target_periode_id=next_periode.id,
                carried_from_id=rec.id,
                status=rec.status,
                severity=rec.severity,
                deskripsi=rec.deskripsi,
                action_items=rec.action_items,
                progress_percent=rec.progress_percent,
                progress_notes=rec.progress_notes,
                created_by=rec.created_by,
            )
            db.add(new_rec)
            await db.flush()
            rec.carried_to_id = new_rec.id
            rec.status = RecommendationStatus.CARRIED_OVER
            carried += 1
    await db.flush()
    return {"abandoned": abandoned, "carried": carried}


async def drain_pending_carry_overs(db: AsyncSession, _periode: Periode) -> int:
    return 0
