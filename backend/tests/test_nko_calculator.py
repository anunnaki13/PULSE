"""Unit-mode checks for Phase 3 NKO calculation primitives."""

from decimal import Decimal
from uuid import uuid4

from app.models.assessment_session import AssessmentSession
from app.models.indikator import Indikator
from app.services.nko_calculator import calculate_kpi_score, calculate_stream_score, fallback_breakdown


def test_nko_kpi_formula_semantics_are_stream_specific():
    assert calculate_kpi_score(Decimal("106.5"), Decimal("100"), "positif") == Decimal("106.5000")
    assert calculate_kpi_score(Decimal("4"), Decimal("5"), "negatif") == Decimal("120.0000")
    assert calculate_kpi_score(Decimal("8"), Decimal("5"), "negatif") == Decimal("40.0000")
    assert calculate_kpi_score(Decimal("102"), Decimal("100"), "range") == Decimal("100.0000")
    assert calculate_kpi_score(Decimal("112"), Decimal("100"), "range") == Decimal("86.0000")


def test_maturity_payload_average_ignores_tidak_dinilai():
    indikator = Indikator(
        id=uuid4(),
        perspektif_id=uuid4(),
        kode="OUTAGE",
        nama="Outage Management",
        bobot=Decimal("10.00"),
        polaritas="positif",
        formula="Rubrik L0..L4",
    )
    session = AssessmentSession(
        id=uuid4(),
        periode_id=uuid4(),
        indikator_id=indikator.id,
        bidang_id=None,
        payload={
            "a": {"value": 3.5},
            "b": {"value": 4},
            "c": {"value": None, "tidak_dinilai": True, "tidak_dinilai_reason": "Tidak berlaku untuk periode ini"},
        },
        realisasi=None,
        target=None,
        pencapaian=None,
        nilai=None,
        nilai_final=None,
    )

    score, trace = calculate_stream_score(session, indikator)

    assert score == Decimal("3.7500")
    assert trace["unit"] == "level"
    assert trace["calculator"] == "maturity_average"


def test_generic_phase6_maturity_stream_uses_payload_average():
    indikator = Indikator(
        id=uuid4(),
        perspektif_id=uuid4(),
        kode="RELIABILITY",
        nama="Reliability Management",
        bobot=Decimal("0.00"),
        polaritas="positif",
        formula="Rubrik L0..L4 placeholder",
    )
    session = AssessmentSession(
        id=uuid4(),
        periode_id=uuid4(),
        indikator_id=indikator.id,
        bidang_id=None,
        payload={"rel-1": {"value": 3.0}, "rel-2": {"value": 4.0}},
        realisasi=None,
        target=None,
        pencapaian=None,
        nilai=None,
        nilai_final=None,
    )

    score, trace = calculate_stream_score(session, indikator)

    assert score == Decimal("3.5000")
    assert trace["unit"] == "level"
    assert trace["calculator"] == "maturity_average"


def test_ocr_weighted_maturity_normalizes_assessed_weights():
    indikator = Indikator(
        id=uuid4(),
        perspektif_id=uuid4(),
        kode="OCR",
        nama="Organization Capital Readiness",
        bobot=Decimal("0.00"),
        polaritas="positif",
        formula="Rubrik L0..L4 placeholder",
    )
    session = AssessmentSession(
        id=uuid4(),
        periode_id=uuid4(),
        indikator_id=indikator.id,
        bidang_id=None,
        payload={
            "OCR-OWM-01": {"value": 4.0, "weight": 0.55},
            "OCR-OWM-02": {"value": 2.0, "weight": 0.45},
            "OCR-05-01": {"value": 1.0, "weight": 1.0, "tidak_dinilai": True},
        },
        realisasi=None,
        target=None,
        pencapaian=None,
        nilai=None,
        nilai_final=None,
    )

    score, trace = calculate_stream_score(session, indikator)

    assert score == Decimal("3.1000")
    assert trace["unit"] == "level"
    assert trace["calculator"] == "maturity_weighted_average"


def test_fallback_breakdown_keeps_demo_reconciliation_anchor():
    data = fallback_breakdown(uuid4())

    assert data["gross_pilar_total"] == 106.12
    assert data["compliance_deduction"] == 2.76
    assert data["nko_total"] == 103.36
    assert {stream["kode"] for stream in data["streams"]} == {"EAF", "EFOR", "OUTAGE", "SMAP"}


def test_phase3_dashboard_routes_registered():
    from app.routers import api_router

    paths = {getattr(route, "path", None) for route in api_router.routes}
    assert "/api/v1/dashboard/executive" in paths
    assert "/api/v1/dashboard/maturity-heatmap" in paths
    assert "/api/v1/dashboard/trend" in paths
