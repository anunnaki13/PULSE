"""AI assistant endpoints for Phase 5."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.deps.auth import current_user, require_role
from app.deps.csrf import require_csrf
from app.deps.db import get_db
from app.models.ai import AiSuggestionLog
from app.models.user import User
from app.schemas.ai import (
    AiAnomalyResponse,
    AiActionPlanRequest,
    AiActionPlanResponse,
    AiAssessmentRequest,
    AiComparativeAnalysisRequest,
    AiComparativeAnalysisResponse,
    AiDraftRecommendationResponse,
    AiFeedbackRequest,
    AiInlineHelpPublic,
    AiPeriodeSummaryRequest,
    AiPeriodeSummaryResponse,
    AiRagChatRequest,
    AiRagChatResponse,
    AiStatusPublic,
    AiSuggestionResponse,
)
from app.services.ai_features import get_or_generate_inline_help, parse_recommendation, run_assessment_ai
from app.services.openrouter_client import ai_available, ai_mode
from app.services.pedoman_ai import generate_action_plan, rag_chat, summarize_periode

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status", response_model=AiStatusPublic)
async def ai_status(_: User = Depends(current_user)) -> AiStatusPublic:
    mode = ai_mode()
    return AiStatusPublic(
        available=ai_available(),
        mode=mode,
        routine_model=settings.OPENROUTER_ROUTINE_MODEL,
        complex_model=settings.OPENROUTER_COMPLEX_MODEL,
        message="AI mock aktif untuk UAT lokal." if mode == "mock" else ("OpenRouter aktif." if mode == "openrouter" else "Layanan AI sementara tidak tersedia."),
    )


@router.post(
    "/draft-justification",
    response_model=AiSuggestionResponse,
    tags=["audit:ai_suggestion"],
    dependencies=[Depends(require_role("pic_bidang", "super_admin")), Depends(require_csrf)],
)
async def draft_justification(
    payload: AiAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AiSuggestionResponse:
    try:
        log, result, _, _ = await run_assessment_ai(db, user=user, session_id=payload.assessment_session_id, use_case="draft_justification", user_note=payload.user_note)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    return AiSuggestionResponse(log_id=log.id, suggestion_type=log.suggestion_type, text=result.text, model_used=result.model, fallback_used=result.fallback_used, pii_masked=log.pii_masked)


@router.post(
    "/draft-recommendation",
    response_model=AiDraftRecommendationResponse,
    tags=["audit:ai_suggestion"],
    dependencies=[Depends(require_role("asesor", "super_admin")), Depends(require_csrf)],
)
async def draft_recommendation(
    payload: AiAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AiDraftRecommendationResponse:
    try:
        log, result, _, _ = await run_assessment_ai(
            db,
            user=user,
            session_id=payload.assessment_session_id,
            use_case="draft_recommendation",
            user_note=payload.user_note,
            complex=True,
            response_format={"type": "json_object"},
        )
        structured = parse_recommendation(result.text)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"ai_recommendation_invalid:{exc}")
    return AiDraftRecommendationResponse(log_id=log.id, suggestion_type=log.suggestion_type, text=result.text, model_used=result.model, fallback_used=result.fallback_used, pii_masked=log.pii_masked, structured=structured)


@router.post(
    "/anomaly-check",
    response_model=AiAnomalyResponse,
    tags=["audit:ai_suggestion"],
    dependencies=[Depends(require_role("asesor", "super_admin")), Depends(require_csrf)],
)
async def anomaly_check(
    payload: AiAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AiAnomalyResponse:
    try:
        log, result, _, _ = await run_assessment_ai(db, user=user, session_id=payload.assessment_session_id, use_case="anomaly_check", response_format={"type": "json_object"})
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    data = json.loads(result.text or "{}")
    return AiAnomalyResponse(
        log_id=log.id,
        suggestion_type=log.suggestion_type,
        text=result.text,
        model_used=result.model,
        fallback_used=result.fallback_used,
        pii_masked=log.pii_masked,
        classification=data.get("classification") or "needs_verification",
        risk_score=int(data.get("risk_score") or 50),
        reasons=data.get("reasons") if isinstance(data.get("reasons"), list) else ["Perlu verifikasi asesor."],
    )


@router.get("/inline-help/{indikator_id}", response_model=AiInlineHelpPublic)
async def inline_help(
    indikator_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AiInlineHelpPublic:
    try:
        return AiInlineHelpPublic.model_validate(await get_or_generate_inline_help(db, user=user, indikator_id=indikator_id))
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.post(
    "/inline-help/{indikator_id}/regenerate",
    response_model=AiInlineHelpPublic,
    tags=["audit:ai_inline_help"],
    dependencies=[Depends(require_role("super_admin", "admin_unit")), Depends(require_csrf)],
)
async def regenerate_inline_help(
    indikator_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AiInlineHelpPublic:
    try:
        row = await get_or_generate_inline_help(db, user=user, indikator_id=indikator_id, force=True)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    request.state.audit_after = {"indikator_id": str(indikator_id), "generated_by_model": row.generated_by_model}
    request.state.audit_entity_id = str(row.id)
    return AiInlineHelpPublic.model_validate(row)


@router.post(
    "/comparative-analysis",
    response_model=AiComparativeAnalysisResponse,
    tags=["audit:ai_suggestion"],
    dependencies=[Depends(require_role("pic_bidang", "asesor", "super_admin")), Depends(require_csrf)],
)
async def comparative_analysis(
    payload: AiComparativeAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AiComparativeAnalysisResponse:
    try:
        log, result, session, _ = await run_assessment_ai(db, user=user, session_id=payload.assessment_session_id, use_case="comparative_analysis", complex=True)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    current = float(session.nilai_final or session.nilai or 0)
    trend = [{"periode": "TW-3", "score": max(0, current - 2.1)}, {"periode": "TW-2", "score": max(0, current - 1.1)}, {"periode": "TW-1", "score": max(0, current - 0.4)}, {"periode": "Saat ini", "score": current}]
    return AiComparativeAnalysisResponse(log_id=log.id, suggestion_type=log.suggestion_type, text=result.text, model_used=result.model, fallback_used=result.fallback_used, pii_masked=log.pii_masked, trend=trend)


@router.post(
    "/chat",
    response_model=AiRagChatResponse,
    tags=["audit:ai_suggestion"],
    dependencies=[Depends(require_role("pic_bidang", "asesor", "super_admin", "manajer_unit", "viewer")), Depends(require_csrf)],
)
async def chat_pedoman(
    payload: AiRagChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AiRagChatResponse:
    log, result, sources = await rag_chat(db, user=user, question=payload.question)
    return AiRagChatResponse(log_id=log.id, suggestion_type=log.suggestion_type, text=result.text, model_used=result.model, fallback_used=result.fallback_used, pii_masked=log.pii_masked, sources=sources)


@router.post(
    "/summarize-periode",
    response_model=AiPeriodeSummaryResponse,
    tags=["audit:ai_suggestion"],
    dependencies=[Depends(require_role("manajer_unit", "super_admin", "viewer")), Depends(require_csrf)],
)
async def summarize_periode_endpoint(
    payload: AiPeriodeSummaryRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AiPeriodeSummaryResponse:
    log, result, sources = await summarize_periode(db, user=user, periode_id=payload.periode_id)
    return AiPeriodeSummaryResponse(
        log_id=log.id,
        suggestion_type=log.suggestion_type,
        text=result.text,
        model_used=result.model,
        fallback_used=result.fallback_used,
        pii_masked=log.pii_masked,
        periode_id=payload.periode_id,
        word_count=len(result.text.split()),
        sources=sources,
    )


@router.post(
    "/generate-action-plan",
    response_model=AiActionPlanResponse,
    tags=["audit:ai_suggestion"],
    dependencies=[Depends(require_role("asesor", "super_admin", "manajer_unit")), Depends(require_csrf)],
)
async def generate_action_plan_endpoint(
    payload: AiActionPlanRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AiActionPlanResponse:
    log, result, structured, sources = await generate_action_plan(
        db,
        user=user,
        periode_id=payload.periode_id,
        assessment_session_id=payload.assessment_session_id,
        focus=payload.focus,
    )
    return AiActionPlanResponse(
        log_id=log.id,
        suggestion_type=log.suggestion_type,
        text=result.text,
        model_used=result.model,
        fallback_used=result.fallback_used,
        pii_masked=log.pii_masked,
        periode_id=payload.periode_id,
        structured=structured,
        sources=sources,
    )


@router.patch(
    "/suggestions/{suggestion_id}/feedback",
    response_model=AiSuggestionResponse,
    tags=["audit:ai_suggestion"],
    dependencies=[Depends(require_csrf)],
)
async def suggestion_feedback(
    suggestion_id: uuid.UUID,
    payload: AiFeedbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AiSuggestionResponse:
    row = await db.get(AiSuggestionLog, suggestion_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ai_suggestion_not_found")
    row.accepted = payload.accepted
    row.user_edited_version = payload.user_edited_version
    await db.flush()
    await db.commit()
    await db.refresh(row)
    request.state.audit_after = {"accepted": row.accepted, "edited": bool(row.user_edited_version)}
    request.state.audit_entity_id = str(row.id)
    return AiSuggestionResponse(log_id=row.id, suggestion_type=row.suggestion_type, text=row.suggestion_text, model_used=row.model_used, fallback_used=row.fallback_used, pii_masked=row.pii_masked)
