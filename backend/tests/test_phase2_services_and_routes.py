"""Unit-mode smoke tests for Phase 2 services and route registration."""

from decimal import Decimal
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.assessment_session import AssessmentSession
from app.models.indikator import Indikator
from app.models.ml_stream import MlStream
from app.routers.assessment_session import _session_detail
from app.services.pencapaian import compute_pair
from app.services.periode_fsm import (
    InvalidTransition,
    RollbackRequiresReason,
    RollbackRequiresSuperAdmin,
    assert_transition_allowed,
)
from app.services.recommendation_fsm import (
    InvalidLifecycle,
    assert_mark_completed_allowed,
    assert_verify_close_allowed,
)


def test_periode_fsm_forward_and_rollback_rules():
    assert (
        assert_transition_allowed("draft", "aktif", {"super_admin"}, None)
        == "drain_pending_carry_overs"
    )
    try:
        assert_transition_allowed("asesmen", "aktif", {"asesor"}, "x" * 25)
    except RollbackRequiresSuperAdmin:
        pass
    else:
        raise AssertionError("rollback must require super_admin")

    try:
        assert_transition_allowed("asesmen", "aktif", {"super_admin"}, "short")
    except RollbackRequiresReason:
        pass
    else:
        raise AssertionError("rollback must require reason >= 20 chars")

    try:
        assert_transition_allowed("draft", "asesmen", {"super_admin"}, None)
    except InvalidTransition:
        pass
    else:
        raise AssertionError("skipping forward states must reject")


def test_recommendation_fsm_rules():
    assert_mark_completed_allowed("open")
    assert_mark_completed_allowed("in_progress")
    try:
        assert_mark_completed_allowed("closed")
    except InvalidLifecycle:
        pass
    else:
        raise AssertionError("closed should reject mark-completed")

    assert_verify_close_allowed("pending_review")
    try:
        assert_verify_close_allowed("in_progress")
    except InvalidLifecycle:
        pass
    else:
        raise AssertionError("verify-close must require pending_review")


def test_pencapaian_compute_pair():
    pencapaian, nilai = compute_pair(Decimal("80"), Decimal("100"), "positif")
    assert pencapaian == Decimal("80.0000")
    assert nilai == Decimal("80.0000")

    pencapaian_neg, _ = compute_pair(Decimal("50"), Decimal("25"), "negatif")
    assert pencapaian_neg == Decimal("50.0000")


def test_phase2_routers_registered():
    from app.routers import api_router

    paths = {getattr(r, "path", None) for r in api_router.routes}
    assert "/api/v1/periode" in paths
    assert "/api/v1/assessment/sessions" in paths
    assert "/api/v1/recommendations" in paths


@pytest.mark.asyncio
async def test_session_detail_exposes_indikator_and_ml_stream_structure():
    indikator_id = uuid4()
    periode_id = uuid4()
    indikator = Indikator(
        id=indikator_id,
        perspektif_id=uuid4(),
        kode="OUTAGE",
        nama="Outage Management",
        bobot=Decimal("10.00"),
        polaritas="positif",
        formula="Rubrik L0..L4",
    )
    stream = MlStream(
        id=uuid4(),
        kode="OUTAGE",
        nama="Outage Management",
        version="test",
        structure={
            "areas": [
                {
                    "kode": "OM-P3",
                    "nama": "P3 Planning",
                    "sub_areas": [
                        {
                            "kode": "OM-P3-01",
                            "nama": "Meeting P2",
                            "criteria": {"level_4": "Continuous improvement"},
                        }
                    ],
                }
            ]
        },
    )
    session = AssessmentSession(
        id=uuid4(),
        periode_id=periode_id,
        indikator_id=indikator.id,
        bidang_id=None,
        payload={},
        state="draft",
        realisasi=None,
        target=None,
        pencapaian=None,
        nilai=None,
        nilai_final=None,
        catatan_pic=None,
        catatan_asesor=None,
        link_eviden=None,
        submitted_at=None,
        asesor_reviewed_at=None,
        updated_at=datetime.now(timezone.utc),
    )

    class FakeDb:
        async def get(self, model, key):
            assert model is Indikator
            assert key == indikator_id
            return indikator

        async def scalar(self, _stmt):
            return stream

    detail = await _session_detail(FakeDb(), session)

    assert detail.indikator is not None
    assert detail.indikator.kode == "OUTAGE"
    assert detail.ml_stream is not None
    assert detail.ml_stream.kode == "OUTAGE"
    assert detail.ml_stream.structure["areas"][0]["sub_areas"][0]["criteria"]["level_4"] == "Continuous improvement"
