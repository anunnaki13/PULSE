from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.assessment_session import AssessmentSession
from app.models.assessment_session_bidang import AssessmentSessionBidang
from app.models.notification import Notification, NotificationType
from app.models.role import Role
from app.models.user import User
from app.services.ws_manager import ws_manager

log = get_logger("pulse.notification.dispatcher")

WS_ENABLED_TYPES = {
    NotificationType.ASSESSMENT_DUE,
    NotificationType.REVIEW_PENDING,
    NotificationType.RECOMMENDATION_ASSIGNED,
    NotificationType.DEADLINE_APPROACHING,
    NotificationType.PERIODE_CLOSED,
}


async def dispatch(
    db: AsyncSession,
    *,
    user_id: UUID,
    type_: NotificationType,
    title: str,
    body: str,
    payload: dict | None = None,
) -> Notification:
    """Create exactly one notification row and one best-effort WS push."""
    notif = Notification(
        user_id=user_id,
        type=type_,
        title=title,
        body=body,
        payload=payload or {},
    )
    db.add(notif)
    await db.flush()
    await db.commit()
    await db.refresh(notif)

    if type_ in WS_ENABLED_TYPES:
        try:
            await ws_manager.send_to_user(
                str(user_id),
                {
                    "id": str(notif.id),
                    "type": type_.value,
                    "title": title,
                    "body": body,
                    "payload": notif.payload,
                    "created_at": notif.created_at.isoformat() if notif.created_at else None,
                },
            )
        except Exception as exc:
            log.warning("ws_push_failed", user_id=str(user_id), type=type_.value, error=str(exc))
    return notif


async def dispatch_assessment_due_for_periode(db: AsyncSession, periode_id: UUID) -> int:
    sessions = (
        await db.scalars(select(AssessmentSession).where(AssessmentSession.periode_id == periode_id))
    ).all()
    count = 0
    for session in sessions:
        if session.bidang_id is None:
            bidang_ids = (
                await db.scalars(
                    select(AssessmentSessionBidang.bidang_id).where(
                        AssessmentSessionBidang.session_id == session.id
                    )
                )
            ).all()
            targets = (
                await db.scalars(
                    select(User).where(User.bidang_id.in_(bidang_ids), User.is_active.is_(True))
                )
            ).all()
        else:
            targets = (
                await db.scalars(
                    select(User).where(User.bidang_id == session.bidang_id, User.is_active.is_(True))
                )
            ).all()
        for target in targets:
            await dispatch(
                db,
                user_id=target.id,
                type_=NotificationType.ASSESSMENT_DUE,
                title="Self-assessment baru tersedia",
                body="Periode baru aktif. Silakan isi self-assessment.",
                payload={"periode_id": str(periode_id), "session_id": str(session.id)},
            )
            count += 1
    return count


async def dispatch_review_pending(db: AsyncSession, session: AssessmentSession) -> int:
    asesors = (
        await db.scalars(
            select(User).join(User.roles).where(Role.name == "asesor", User.is_active.is_(True))
        )
    ).all()
    for asesor in asesors:
        await dispatch(
            db,
            user_id=asesor.id,
            type_=NotificationType.REVIEW_PENDING,
            title="Submission baru menunggu review",
            body="Self-assessment submitted. Silakan review.",
            payload={"session_id": str(session.id), "periode_id": str(session.periode_id)},
        )
    return len(asesors)


async def dispatch_review_finished(
    db: AsyncSession,
    session: AssessmentSession,
    *,
    decision: str,
) -> int:
    if session.bidang_id is None:
        bidang_ids = (
            await db.scalars(
                select(AssessmentSessionBidang.bidang_id).where(
                    AssessmentSessionBidang.session_id == session.id
                )
            )
        ).all()
        targets = (
            await db.scalars(
                select(User).where(User.bidang_id.in_(bidang_ids), User.is_active.is_(True))
            )
        ).all()
    else:
        targets = (
            await db.scalars(
                select(User).where(User.bidang_id == session.bidang_id, User.is_active.is_(True))
            )
        ).all()

    label = {
        "approve": "disetujui",
        "override": "di-override",
        "request_revision": "perlu revisi",
    }.get(decision, decision)
    for target in targets:
        await dispatch(
            db,
            user_id=target.id,
            type_=NotificationType.REVIEW_PENDING,
            title=f"Submission Anda {label}",
            body=f"Asesor telah menyelesaikan review: {decision}.",
            payload={"session_id": str(session.id), "decision": decision},
        )
    return len(targets)


async def dispatch_recommendation_assigned(
    db: AsyncSession,
    recommendation_id: UUID | str,
) -> int:
    from app.models.recommendation import Recommendation

    rec_id = uuid.UUID(str(recommendation_id))
    rec = await db.get(Recommendation, rec_id)
    if rec is None:
        return 0
    owners = {
        item.get("owner_user_id")
        for item in rec.action_items or []
        if item.get("owner_user_id")
    }
    count = 0
    for owner_id in owners:
        try:
            await dispatch(
                db,
                user_id=uuid.UUID(str(owner_id)),
                type_=NotificationType.RECOMMENDATION_ASSIGNED,
                title="Rekomendasi baru di-assign",
                body=rec.deskripsi[:200],
                payload={
                    "recommendation_id": str(rec.id),
                    "severity": rec.severity.value if hasattr(rec.severity, "value") else rec.severity,
                },
            )
            count += 1
        except (ValueError, TypeError):
            continue
    return count


async def dispatch_periode_closed(db: AsyncSession, periode_id: UUID) -> int:
    users = (await db.scalars(select(User).where(User.is_active.is_(True)))).all()
    for user in users:
        await dispatch(
            db,
            user_id=user.id,
            type_=NotificationType.PERIODE_CLOSED,
            title="Periode ditutup",
            body="Periode telah difinalisasi dan ditutup.",
            payload={"periode_id": str(periode_id)},
        )
    return len(users)
