"""Unit-mode checks for Phase 5 AI backend foundations."""

from uuid import uuid4

from app.schemas.ai import AiDraftRecommendation
from app.services.openrouter_client import ai_available, ai_mode
from app.services.pii_masking import mask_pii


def test_pii_masking_removes_email_nip_long_id_and_vendor():
    raw = "PIC budi@example.com NIP 199901012020011234 vendor PT Maju Jaya Abadi no 1234567890123456"
    masked = mask_pii(raw)

    assert masked.masked is True
    assert "budi@example.com" not in masked.text
    assert "199901012020011234" not in masked.text
    assert "1234567890123456" not in masked.text
    assert "PT Maju Jaya Abadi" not in masked.text
    assert "[MASKED_EMAIL]" in masked.text


def test_mock_mode_makes_ai_available_for_local_uat():
    assert ai_mode() in {"mock", "openrouter", "unavailable"}
    assert ai_available() is True


def test_draft_recommendation_schema_accepts_smart_shape():
    parsed = AiDraftRecommendation.model_validate(
        {
            "severity": "medium",
            "deskripsi": "Perkuat tindak lanjut gap EAF melalui review mingguan.",
            "action_items": [{"action": "Susun rencana korektif mingguan", "deadline": None, "owner_user_id": None}],
            "target_outcome": "Gap menurun pada periode berikutnya.",
        }
    )

    assert parsed.severity == "medium"
    assert parsed.action_items[0].action.startswith("Susun")


def test_phase5_ai_routes_registered():
    from app.routers import api_router

    paths = {getattr(route, "path", None) for route in api_router.routes}
    assert "/api/v1/ai/status" in paths
    assert "/api/v1/ai/draft-justification" in paths
    assert "/api/v1/ai/draft-recommendation" in paths
    assert "/api/v1/ai/anomaly-check" in paths
    assert "/api/v1/ai/inline-help/{indikator_id}" in paths
    assert "/api/v1/ai/comparative-analysis" in paths
    assert "/api/v1/ai/chat" in paths
    assert "/api/v1/ai/summarize-periode" in paths
    assert "/api/v1/ai/generate-action-plan" in paths
    assert f"/api/v1/ai/suggestions/{uuid4()}/feedback" not in paths


def test_pedoman_retrieval_returns_sources():
    from app.services.pedoman_ai import embedding_literal, retrieve_pedoman_chunks

    chunks = retrieve_pedoman_chunks("bagaimana formula polaritas negatif dan range")

    assert len(chunks) >= 1
    assert chunks[0][0].source_id.startswith("pedoman-")
    assert 0 <= chunks[0][1] <= 1
    assert embedding_literal("formula polaritas").startswith("[")


def test_periode_summary_mock_respects_word_count_contract():
    from app.services.openrouter_client import _mock_response

    summary = _mock_response("periode_summary")

    assert 400 <= len(summary.split()) <= 600
