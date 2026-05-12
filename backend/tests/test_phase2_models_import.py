"""Phase 2 models and schemas import smoke tests."""

import importlib
from decimal import Decimal
from uuid import uuid4

import pydantic


def test_phase2_models_import():
    for mod in [
        "app.models.periode",
        "app.models.assessment_session",
        "app.models.assessment_session_bidang",
        "app.models.indikator_applicable_bidang",
        "app.models.recommendation",
        "app.models.notification",
        "app.models.audit_log",
    ]:
        importlib.import_module(mod)


def test_phase2_schemas_import():
    for mod in [
        "app.schemas.periode",
        "app.schemas.assessment",
        "app.schemas.recommendation",
        "app.schemas.notification",
        "app.schemas.audit",
    ]:
        importlib.import_module(mod)


def test_action_item_extra_forbid():
    from app.schemas.recommendation import ActionItem

    try:
        ActionItem(action="do x", unknown_field="boom")
    except pydantic.ValidationError as exc:
        assert "extra" in str(exc).lower()
        return
    raise AssertionError("extra='forbid' not enforced on ActionItem")


def test_asesor_review_override_min20_chars():
    from app.schemas.assessment import AsesorReview

    try:
        AsesorReview(
            decision="override",
            nilai_final=Decimal("85.50"),
            catatan_asesor="x" * 19,
        )
    except pydantic.ValidationError:
        pass
    else:
        raise AssertionError("override with <20 chars must reject")

    AsesorReview(
        decision="override",
        nilai_final=Decimal("85.50"),
        catatan_asesor="x" * 20,
    )

    try:
        AsesorReview(decision="override", catatan_asesor="x" * 25)
    except pydantic.ValidationError:
        pass
    else:
        raise AssertionError("override without nilai_final must reject")


def test_recommendation_action_items_min_length():
    from app.schemas.recommendation import RecommendationCreate

    try:
        RecommendationCreate(
            source_assessment_id=uuid4(),
            severity="medium",
            deskripsi="x" * 10,
            action_items=[],
            target_periode_id=uuid4(),
        )
    except pydantic.ValidationError:
        pass
    else:
        raise AssertionError("action_items must reject empty list")
