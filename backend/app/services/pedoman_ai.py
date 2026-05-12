"""Pedoman Konkin grounded AI helpers for Phase 6b."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from hashlib import sha256

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.ai import AiDraftRecommendation, AiSourceCitation
from app.services.ai_features import log_ai_result
from app.services.nko_calculator import get_or_create_snapshot
from app.services.openrouter_client import complete_chat
from app.services.pii_masking import mask_pii


@dataclass(frozen=True)
class PedomanChunk:
    source_id: str
    title: str
    section: str
    page: int
    text: str


PEDOMAN_CHUNKS: tuple[PedomanChunk, ...] = (
    PedomanChunk(
        "pedoman-nko-formula",
        "Pedoman Konkin 2026",
        "NKO dan bobot pilar",
        5,
        "NKO dihitung dari kontribusi Pilar I sampai Pilar V kemudian dikurangi komponen Compliance. Bobot penambah adalah 46, 25, 6, 8, dan 15.",
    ),
    PedomanChunk(
        "pedoman-polaritas",
        "Pedoman Konkin 2026",
        "Formula KPI kuantitatif",
        6,
        "Indikator positif memakai realisasi dibagi target. Indikator negatif memakai dua dikurangi realisasi dibagi target. Range based menilai kedekatan terhadap target.",
    ),
    PedomanChunk(
        "pedoman-maturity",
        "Pedoman Konkin 2026",
        "Maturity level",
        12,
        "Maturity level dinilai dari sub-area dengan level 0 sampai 4. Jika sub-area tidak dinilai, agregasi harus menormalisasi komponen yang dinilai.",
    ),
    PedomanChunk(
        "pedoman-hcr-ocr",
        "Pedoman Konkin 2026",
        "HCR dan OCR",
        20,
        "HCR mencakup Strategic Workforce Planning, Talent, Performance, Reward, Industrial Relation, dan HC Operations. OCR memiliki sub-area organisasi termasuk OWM dengan bobot 55 dan 45.",
    ),
    PedomanChunk(
        "pedoman-rekomendasi",
        "Pedoman Konkin 2026",
        "Tindak lanjut rekomendasi",
        30,
        "Rekomendasi harus spesifik, terukur, memiliki PIC, deadline, dan target outcome. Tindak lanjut dipantau sampai close atau carry-over.",
    ),
)


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_]+", text.lower()) if len(token) >= 3}


def source_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def embedding_literal(text: str, *, dimensions: int = 16) -> str:
    vector = [0.0] * dimensions
    for token in _tokens(text):
        digest = sha256(token.encode("utf-8")).digest()
        index = digest[0] % dimensions
        sign = -1.0 if digest[1] % 2 else 1.0
        vector[index] += sign
    norm = sum(value * value for value in vector) ** 0.5 or 1.0
    normalized = [round(value / norm, 6) for value in vector]
    return "[" + ",".join(str(value) for value in normalized) + "]"


def retrieve_pedoman_chunks(query: str, *, k: int = 5) -> list[tuple[PedomanChunk, float]]:
    query_tokens = _tokens(query)
    scored: list[tuple[PedomanChunk, float]] = []
    for chunk in PEDOMAN_CHUNKS:
        haystack = _tokens(f"{chunk.title} {chunk.section} {chunk.text}")
        if not query_tokens:
            score = 0.0
        else:
            score = len(query_tokens & haystack) / max(1, len(query_tokens))
        scored.append((chunk, min(1.0, score)))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]


async def retrieve_pedoman_chunks_db(
    db: AsyncSession,
    query: str,
    *,
    k: int = 5,
) -> list[tuple[PedomanChunk, float]]:
    try:
        rows = (
            await db.execute(
                text(
                    """
                    SELECT
                        source_id,
                        title,
                        section,
                        page,
                        content,
                        GREATEST(0, LEAST(1, 1 - (embedding <=> (:embedding)::vector))) AS score
                    FROM pedoman_chunks
                    ORDER BY embedding <=> (:embedding)::vector
                    LIMIT :limit
                    """
                ),
                {"embedding": embedding_literal(query), "limit": k},
            )
        ).mappings().all()
    except SQLAlchemyError:
        return retrieve_pedoman_chunks(query, k=k)

    if not rows:
        return retrieve_pedoman_chunks(query, k=k)
    return [
        (
            PedomanChunk(
                source_id=str(row["source_id"]),
                title=str(row["title"]),
                section=str(row["section"]),
                page=int(row["page"]) if row["page"] is not None else 0,
                text=str(row["content"]),
            ),
            float(row["score"] or 0.0),
        )
        for row in rows
    ]


def _citations(scored: list[tuple[PedomanChunk, float]]) -> list[AiSourceCitation]:
    return [
        AiSourceCitation(
            source_id=chunk.source_id,
            title=chunk.title,
            section=chunk.section,
            page=chunk.page,
            score=round(score, 3),
        )
        for chunk, score in scored
    ]


def _context(scored: list[tuple[PedomanChunk, float]]) -> str:
    return "\n".join(f"[{chunk.source_id}] {chunk.section}: {chunk.text}" for chunk, _ in scored)


async def rag_chat(db: AsyncSession, *, user: User, question: str):
    scored = await retrieve_pedoman_chunks_db(db, question)
    citations = _citations(scored)
    masked = mask_pii(json.dumps({"question": question, "sources": _context(scored)}, ensure_ascii=False))
    result = await complete_chat(
        use_case="rag_chat",
        complex=True,
        messages=[
            {"role": "system", "content": "Jawab berdasarkan sumber Pedoman Konkin yang diberikan. Jangan mengarang sumber baru."},
            {"role": "user", "content": masked.text},
        ],
    )
    log = await log_ai_result(
        db,
        user=user,
        suggestion_type="rag_chat",
        context_entity_type="pedoman",
        context_entity_id=None,
        masked_prompt=masked.text,
        result=result,
        pii_masked=masked.masked,
        structured_payload={"sources": [citation.model_dump() for citation in citations]},
    )
    return log, result, citations


async def summarize_periode(db: AsyncSession, *, user: User, periode_id: uuid.UUID):
    snapshot = await get_or_create_snapshot(db, periode_id)
    scored = await retrieve_pedoman_chunks_db(db, "ringkasan periode nko pilar compliance rekomendasi")
    citations = _citations(scored)
    prompt = {
        "periode_id": str(periode_id),
        "snapshot": snapshot.breakdown,
        "instruction": "Tulis ringkasan eksekutif 400-600 kata Bahasa Indonesia. Fokus pada NKO, pilar, compliance, dan tindak lanjut.",
        "sources": _context(scored),
    }
    masked = mask_pii(json.dumps(prompt, ensure_ascii=False, default=str))
    result = await complete_chat(use_case="periode_summary", complex=True, messages=[{"role": "user", "content": masked.text}])
    log = await log_ai_result(
        db,
        user=user,
        suggestion_type="periode_summary",
        context_entity_type="periode",
        context_entity_id=periode_id,
        masked_prompt=masked.text,
        result=result,
        pii_masked=masked.masked,
        structured_payload={"sources": [citation.model_dump() for citation in citations]},
    )
    return log, result, citations


async def generate_action_plan(
    db: AsyncSession,
    *,
    user: User,
    periode_id: uuid.UUID,
    assessment_session_id: uuid.UUID | None,
    focus: str | None,
):
    snapshot = await get_or_create_snapshot(db, periode_id)
    scored = await retrieve_pedoman_chunks_db(db, f"rekomendasi SMART action plan {focus or ''}")
    citations = _citations(scored)
    prompt = {
        "periode_id": str(periode_id),
        "assessment_session_id": str(assessment_session_id) if assessment_session_id else None,
        "focus": focus,
        "snapshot": snapshot.breakdown,
        "instruction": "Return JSON SMART action plan: severity, deskripsi, action_items, target_outcome.",
        "sources": _context(scored),
    }
    masked = mask_pii(json.dumps(prompt, ensure_ascii=False, default=str))
    result = await complete_chat(
        use_case="action_plan",
        complex=True,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": masked.text}],
    )
    try:
        structured = AiDraftRecommendation.model_validate(json.loads(result.text))
    except Exception:
        structured = AiDraftRecommendation(
            severity="medium",
            deskripsi="Susun rencana aksi korektif berbasis gap kinerja periode berjalan.",
            action_items=[{"action": "Tetapkan PIC, deadline, dan milestone tindak lanjut.", "deadline": None, "owner_user_id": None}],
            target_outcome="Gap kinerja menurun dan tindak lanjut terdokumentasi.",
        )
    log = await log_ai_result(
        db,
        user=user,
        suggestion_type="action_plan",
        context_entity_type="periode",
        context_entity_id=periode_id,
        masked_prompt=masked.text,
        result=result,
        pii_masked=masked.masked,
        structured_payload={"action_plan": structured.model_dump(mode="json"), "sources": [citation.model_dump() for citation in citations]},
    )
    return log, result, structured, citations
