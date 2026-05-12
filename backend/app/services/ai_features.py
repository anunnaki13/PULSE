"""AI feature orchestration for bounded Phase 5 use cases."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AiInlineHelp, AiSuggestionLog
from app.models.assessment_session import AssessmentSession
from app.models.indikator import Indikator
from app.models.user import User
from app.schemas.ai import AiDraftRecommendation
from app.services.openrouter_client import LlmResult, complete_chat
from app.services.pii_masking import mask_pii


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(Decimal(value))
    except Exception:
        return None


async def session_context(db: AsyncSession, session_id: uuid.UUID) -> tuple[AssessmentSession, Indikator]:
    session = await db.get(AssessmentSession, session_id)
    if session is None or session.deleted_at is not None:
        raise LookupError("assessment_session_not_found")
    indikator = await db.get(Indikator, session.indikator_id)
    if indikator is None:
        raise LookupError("indikator_not_found")
    return session, indikator


def build_prompt(session: AssessmentSession, indikator: Indikator, user_note: str | None = None) -> str:
    return json.dumps(
        {
            "indikator": {"kode": indikator.kode, "nama": indikator.nama, "polaritas": indikator.polaritas, "formula": indikator.formula},
            "assessment": {
                "state": session.state.value,
                "target": _num(session.target),
                "realisasi": _num(session.realisasi),
                "nilai": _num(session.nilai),
                "nilai_final": _num(session.nilai_final),
                "catatan_pic": session.catatan_pic,
                "catatan_asesor": session.catatan_asesor,
                "payload": session.payload,
            },
            "user_note": user_note,
            "instruction": "Berikan output Bahasa Indonesia formal. Jangan membuat evidence atau fakta baru.",
        },
        ensure_ascii=False,
        default=str,
    )


async def log_ai_result(
    db: AsyncSession,
    *,
    user: User,
    suggestion_type: str,
    context_entity_type: str,
    context_entity_id: uuid.UUID | None,
    masked_prompt: str,
    result: LlmResult,
    pii_masked: bool,
    structured_payload: dict | None = None,
) -> AiSuggestionLog:
    row = AiSuggestionLog(
        user_id=user.id,
        suggestion_type=suggestion_type,
        context_entity_type=context_entity_type,
        context_entity_id=context_entity_id,
        prompt=masked_prompt,
        suggestion_text=result.text,
        structured_payload=structured_payload or {},
        model_used=result.model,
        pii_masked=pii_masked,
        fallback_used=result.fallback_used,
        latency_ms=result.latency_ms,
        estimated_cost_usd=Decimal(str(result.estimated_cost_usd)),
        error=result.error,
    )
    db.add(row)
    await db.flush()
    await db.commit()
    await db.refresh(row)
    return row


async def run_assessment_ai(
    db: AsyncSession,
    *,
    user: User,
    session_id: uuid.UUID,
    use_case: str,
    user_note: str | None = None,
    complex: bool = False,
    response_format: dict | None = None,
) -> tuple[AiSuggestionLog, LlmResult, AssessmentSession, Indikator]:
    session, indikator = await session_context(db, session_id)
    masked = mask_pii(build_prompt(session, indikator, user_note))
    result = await complete_chat(
        use_case=use_case,
        complex=complex,
        response_format=response_format,
        messages=[
            {"role": "system", "content": "Anda adalah asisten Konkin PLTU Tenayan. Jawab singkat, formal, dan berbasis konteks."},
            {"role": "user", "content": masked.text},
        ],
    )
    structured: dict | None = None
    if use_case in {"draft_recommendation", "anomaly_check"} and result.text:
        try:
            structured = json.loads(result.text)
        except json.JSONDecodeError:
            structured = {}
    log = await log_ai_result(
        db,
        user=user,
        suggestion_type=use_case,
        context_entity_type="assessment_session",
        context_entity_id=session.id,
        masked_prompt=masked.text,
        result=result,
        pii_masked=masked.masked,
        structured_payload=structured,
    )
    return log, result, session, indikator


async def get_or_generate_inline_help(db: AsyncSession, *, user: User, indikator_id: uuid.UUID, force: bool = False) -> AiInlineHelp:
    indikator = await db.get(Indikator, indikator_id)
    if indikator is None or indikator.deleted_at is not None:
        raise LookupError("indikator_not_found")
    existing = await db.scalar(select(AiInlineHelp).where(AiInlineHelp.indikator_id == indikator_id))
    if existing is not None and not force:
        return existing

    prompt = json.dumps({"indikator": {"kode": indikator.kode, "nama": indikator.nama, "formula": indikator.formula, "polaritas": indikator.polaritas}}, ensure_ascii=False)
    masked = mask_pii(prompt)
    result = await complete_chat(
        use_case="inline_help",
        messages=[{"role": "system", "content": "Buat inline help indikator Konkin dalam JSON."}, {"role": "user", "content": masked.text}],
        response_format={"type": "json_object"},
    )
    try:
        payload = json.loads(result.text)
    except json.JSONDecodeError:
        payload = {}
    if existing is None:
        existing = AiInlineHelp(indikator_id=indikator_id)
        db.add(existing)
    existing.apa_itu = str(payload.get("apa_itu") or f"{indikator.kode} adalah indikator Konkin untuk {indikator.nama}.")
    existing.formula_explanation = str(payload.get("formula_explanation") or (indikator.formula or "Formula mengikuti master indikator."))
    existing.best_practice = str(payload.get("best_practice") or "Gunakan data resmi dan catatan yang dapat diverifikasi.")
    existing.common_pitfalls = str(payload.get("common_pitfalls") or "Hindari tertukar target dan realisasi.")
    existing.related_indikator = payload.get("related_indikator") if isinstance(payload.get("related_indikator"), list) else []
    existing.generated_by_model = result.model
    existing.generated_at = datetime.now(timezone.utc)
    await log_ai_result(
        db,
        user=user,
        suggestion_type="inline_help",
        context_entity_type="indikator",
        context_entity_id=indikator_id,
        masked_prompt=masked.text,
        result=result,
        pii_masked=masked.masked,
        structured_payload=payload if isinstance(payload, dict) else {},
    )
    await db.flush()
    await db.commit()
    await db.refresh(existing)
    return existing


def parse_recommendation(text: str) -> AiDraftRecommendation:
    return AiDraftRecommendation.model_validate(json.loads(text))
