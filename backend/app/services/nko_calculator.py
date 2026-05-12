"""NKO snapshot calculation service."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_session import AssessmentSession, SessionState
from app.models.indikator import Indikator
from app.models.nko_snapshot import NkoSnapshot
from app.models.periode import Periode
from app.models.perspektif import Perspektif
from app.services.compliance_summary import ComplianceSummary, compute_compliance_summary


Q = Decimal("0.0001")


def _q(value: Decimal) -> Decimal:
    return value.quantize(Q, rounding=ROUND_HALF_UP)


def _clamp_score(value: Decimal) -> Decimal:
    return _q(max(Decimal("0"), min(value, Decimal("120"))))


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _num(value: Decimal | None) -> float | None:
    return float(_q(value)) if value is not None else None


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return _num(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _average(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return _q(sum(values, Decimal("0")) / Decimal(len(values)))


def _extract_ml_values(node: Any) -> list[Decimal]:
    values: list[Decimal] = []
    if isinstance(node, dict):
        if node.get("tidak_dinilai") is True:
            return values
        direct = _dec(node.get("value"))
        if direct is not None:
            values.append(direct)
        for value in node.values():
            values.extend(_extract_ml_values(value))
    elif isinstance(node, list):
        for value in node:
            values.extend(_extract_ml_values(value))
    return values


def _extract_ml_weighted_values(node: Any) -> list[tuple[Decimal, Decimal]]:
    values: list[tuple[Decimal, Decimal]] = []
    if isinstance(node, dict):
        if node.get("tidak_dinilai") is True:
            return values
        direct = _dec(node.get("value"))
        weight = _dec(node.get("weight"))
        if direct is not None and weight is not None and weight > 0:
            values.append((direct, weight))
        for value in node.values():
            values.extend(_extract_ml_weighted_values(value))
    elif isinstance(node, list):
        for value in node:
            values.extend(_extract_ml_weighted_values(value))
    return values


def _weighted_average(values: list[tuple[Decimal, Decimal]]) -> Decimal | None:
    if not values:
        return None
    total_weight = sum((weight for _, weight in values), Decimal("0"))
    if total_weight == 0:
        return None
    return _q(sum((value * weight for value, weight in values), Decimal("0")) / total_weight)


def calculate_kpi_score(realisasi: Decimal | None, target: Decimal | None, polaritas: str) -> Decimal | None:
    if realisasi is None or target is None or target == 0:
        return None
    if polaritas == "negatif":
        return _clamp_score((Decimal("2") - (realisasi / target)) * Decimal("100"))
    if polaritas == "range":
        deviation_pct = abs(realisasi - target) / abs(target) * Decimal("100")
        if deviation_pct <= Decimal("5"):
            return Decimal("100.0000")
        return _clamp_score(Decimal("100") - ((deviation_pct - Decimal("5")) * Decimal("2")))
    return _clamp_score((realisasi / target) * Decimal("100"))


def calculate_stream_score(session: AssessmentSession, indikator: Indikator) -> tuple[Decimal | None, dict[str, Any]]:
    kode = indikator.kode.upper()
    realisasi = _dec(session.realisasi)
    target = _dec(session.target)
    formula = indikator.formula
    unit = "%"
    polarity = indikator.polaritas
    calculator = "kpi_positive"

    ml_values = _extract_ml_values(session.payload or {})
    weighted_ml_values = _extract_ml_weighted_values(session.payload or {})

    if kode == "EFOR":
        polarity = "negatif"
        calculator = "kpi_negative"
        formula = "(2 - realisasi / target) * 100"
        score = calculate_kpi_score(realisasi, target, "negatif")
    elif kode in {"OUTAGE", "OM", "SMAP"} or ml_values or (formula and "Rubrik" in formula):
        unit = "level"
        if weighted_ml_values:
            calculator = "maturity_weighted_average"
            score = _weighted_average(weighted_ml_values)
        else:
            calculator = "maturity_average"
            score = _average(ml_values)
        formula = "average assessed maturity sub-area values"
    else:
        if kode == "EAF":
            formula = "(realisasi / target) * 100"
        score = calculate_kpi_score(realisasi, target, indikator.polaritas)

    if session.nilai_final is not None and kode not in {"EAF", "EFOR", "OUTAGE", "OM", "SMAP"}:
        score = _dec(session.nilai_final)

    return score, {
        "kode": kode,
        "nama": indikator.nama,
        "unit": unit,
        "polarity": polarity,
        "calculator": calculator,
        "formula": formula,
        "realisasi": _num(realisasi),
        "target": _num(target),
        "score": _num(score),
    }


def _compliance_deduction(score: Decimal | None, cap: Decimal | None) -> Decimal:
    cap = cap or Decimal("10")
    if score is None:
        return Decimal("0")
    if score <= Decimal("4"):
        return _q(max(Decimal("0"), (Decimal("4") - score) / Decimal("4") * cap))
    return _q(max(Decimal("0"), Decimal("100") - score) / Decimal("100") * cap)


def fallback_breakdown(periode_id: uuid.UUID, compliance_deduction: Decimal | None = None) -> dict[str, Any]:
    deduction = _q(compliance_deduction or Decimal("2.76"))
    gross = Decimal("106.12")
    nko_total = _q(gross - deduction)
    return {
        "periode_id": str(periode_id),
        "source": "fallback",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gross_pilar_total": _num(gross),
        "compliance_deduction": _num(deduction),
        "nko_total": _num(nko_total),
        "pilar": [
            {"kode": "I", "nama": "Operational Excellence", "score": 108.4, "contribution": 49.86, "trend": 1.2},
            {"kode": "II", "nama": "Reliability & Maturity", "score": 103.2, "contribution": 25.8, "trend": 0.7},
            {"kode": "III", "nama": "Customer & Stakeholder", "score": 101.5, "contribution": 6.09, "trend": -0.2},
            {"kode": "IV", "nama": "Investment & Project", "score": 104.1, "contribution": 8.33, "trend": 0.4},
            {"kode": "V", "nama": "Culture & HSE", "score": 106.9, "contribution": 16.04, "trend": 0.9},
        ],
        "streams": [
            {"kode": "EAF", "nama": "Equivalent Availability Factor", "unit": "%", "polarity": "positif", "score": 106.5, "formula": "(realisasi / target) * 100"},
            {"kode": "EFOR", "nama": "Equivalent Forced Outage Rate", "unit": "%", "polarity": "negatif", "score": 104.2, "formula": "(2 - realisasi / target) * 100"},
            {"kode": "OUTAGE", "nama": "Outage Management", "unit": "level", "polarity": "positif", "score": 3.46, "formula": "average assessed maturity sub-area values"},
            {"kode": "SMAP", "nama": "SMAP Compliance", "unit": "level", "polarity": "positif", "score": 3.31, "formula": "average assessed maturity sub-area values"},
        ],
        "formula_ledger": [
            {"label": "Gross Pilar", "value": _num(gross)},
            {"label": "Compliance Deduction", "value": _num(-deduction)},
            {"label": "NKO Final", "value": _num(nko_total)},
        ],
    }


def _effective_compliance_deduction(summary: ComplianceSummary, fallback: Decimal) -> Decimal:
    return summary.total_pengurang if summary.has_records else _q(fallback)


async def recompute_nko_snapshot(
    db: AsyncSession,
    periode_id: uuid.UUID,
    *,
    source: str = "live",
    changed_indikator_id: uuid.UUID | None = None,
) -> NkoSnapshot:
    compliance_summary = await compute_compliance_summary(db, periode_id)
    rows = (
        await db.execute(
            select(AssessmentSession, Indikator, Perspektif)
            .join(Indikator, AssessmentSession.indikator_id == Indikator.id)
            .join(Perspektif, Indikator.perspektif_id == Perspektif.id)
            .where(
                AssessmentSession.periode_id == periode_id,
                AssessmentSession.deleted_at.is_(None),
                AssessmentSession.state.in_([SessionState.APPROVED, SessionState.OVERRIDDEN]),
            )
        )
    ).all()

    if not rows:
        compliance_deduction = _effective_compliance_deduction(compliance_summary, Decimal("2.76"))
        breakdown = fallback_breakdown(periode_id, compliance_deduction)
        breakdown["compliance_summary"] = _jsonable(compliance_summary.as_dict())
        nko_total = _q(Decimal("106.12") - compliance_deduction)
        return await upsert_snapshot(
            db,
            periode_id,
            nko_total,
            Decimal("106.12"),
            compliance_deduction,
            breakdown,
            "fallback" if source == "live" else source,
        )

    pilar_groups: dict[str, dict[str, Any]] = {}
    stream_rows: list[dict[str, Any]] = []
    compliance_deduction = Decimal("0")

    for session, indikator, perspektif in rows:
        score, trace = calculate_stream_score(session, indikator)
        trace["indikator_id"] = str(indikator.id)
        trace["session_id"] = str(session.id)
        trace["pilar_kode"] = perspektif.kode
        trace["bobot_indikator"] = float(indikator.bobot)
        stream_rows.append(trace)

        if perspektif.is_pengurang:
            compliance_deduction += _compliance_deduction(score, perspektif.pengurang_cap)
            continue

        group = pilar_groups.setdefault(
            perspektif.kode,
            {
                "kode": perspektif.kode,
                "nama": perspektif.nama,
                "bobot": float(perspektif.bobot),
                "weighted_score": Decimal("0"),
                "weight_sum": Decimal("0"),
                "streams": [],
            },
        )
        if score is None:
            continue
        weight = Decimal(indikator.bobot or 0) / Decimal("100")
        group["weighted_score"] += score * weight
        group["weight_sum"] += Decimal(indikator.bobot or 0)
        group["streams"].append(trace)

    pilar_breakdown: list[dict[str, Any]] = []
    gross = Decimal("0")
    for group in sorted(pilar_groups.values(), key=lambda item: item["kode"]):
        pilar_score = _q(group["weighted_score"])
        contribution = _q(pilar_score * (Decimal(str(group["bobot"])) / Decimal("100")))
        gross += contribution
        pilar_breakdown.append(
            {
                "kode": group["kode"],
                "nama": group["nama"],
                "bobot": group["bobot"],
                "score": _num(pilar_score),
                "contribution": _num(contribution),
                "assessed_weight": _num(group["weight_sum"]),
                "streams": group["streams"],
            }
        )

    gross = _q(gross)
    if not pilar_breakdown or gross == 0:
        compliance_deduction = _effective_compliance_deduction(compliance_summary, Decimal("2.76"))
        breakdown = fallback_breakdown(periode_id, compliance_deduction)
        breakdown["live_partial_streams"] = stream_rows
        breakdown["compliance_summary"] = _jsonable(compliance_summary.as_dict())
        nko_total = _q(Decimal("106.12") - compliance_deduction)
        return await upsert_snapshot(
            db,
            periode_id,
            nko_total,
            Decimal("106.12"),
            compliance_deduction,
            breakdown,
            "fallback",
        )

    compliance_deduction = _effective_compliance_deduction(compliance_summary, compliance_deduction)
    nko_total = _q(gross - compliance_deduction)
    breakdown = {
        "periode_id": str(periode_id),
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "changed_indikator_id": str(changed_indikator_id) if changed_indikator_id else None,
        "gross_pilar_total": _num(gross),
        "compliance_deduction": _num(compliance_deduction),
        "nko_total": _num(nko_total),
        "pilar": pilar_breakdown,
        "streams": stream_rows,
        "compliance_summary": _jsonable(compliance_summary.as_dict()),
        "formula_ledger": [
            {"label": "Gross Pilar", "value": _num(gross)},
            {"label": "Compliance Deduction", "value": _num(-compliance_deduction)},
            {"label": "NKO Final", "value": _num(nko_total)},
        ],
    }
    return await upsert_snapshot(db, periode_id, nko_total, gross, compliance_deduction, breakdown, source)


async def upsert_snapshot(
    db: AsyncSession,
    periode_id: uuid.UUID,
    nko_total: Decimal,
    gross_pilar_total: Decimal,
    compliance_deduction: Decimal,
    breakdown: dict[str, Any],
    source: str,
) -> NkoSnapshot:
    snapshot = await db.scalar(select(NkoSnapshot).where(NkoSnapshot.periode_id == periode_id))
    if snapshot is None:
        snapshot = NkoSnapshot(periode_id=periode_id)
        db.add(snapshot)
    snapshot.nko_total = _q(nko_total)
    snapshot.gross_pilar_total = _q(gross_pilar_total)
    snapshot.compliance_deduction = _q(compliance_deduction)
    snapshot.breakdown = breakdown
    snapshot.source = source
    await db.flush()
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


async def get_or_create_snapshot(db: AsyncSession, periode_id: uuid.UUID) -> NkoSnapshot:
    snapshot = await db.scalar(select(NkoSnapshot).where(NkoSnapshot.periode_id == periode_id))
    if snapshot is not None:
        if snapshot.source == "live" and not snapshot.breakdown.get("pilar"):
            return await recompute_nko_snapshot(db, periode_id)
        return snapshot
    return await recompute_nko_snapshot(db, periode_id)


async def maturity_heatmap(db: AsyncSession, tahun: int) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(NkoSnapshot, Periode)
            .join(Periode, NkoSnapshot.periode_id == Periode.id)
            .where(Periode.tahun == tahun)
            .order_by(Periode.triwulan)
        )
    ).all()
    matrix: dict[str, dict[str, Any]] = defaultdict(lambda: {"stream": "", "quarters": {}})
    for snapshot, periode in rows:
        for stream in snapshot.breakdown.get("streams", []):
            if stream.get("unit") != "level":
                continue
            code = str(stream.get("kode"))
            matrix[code]["stream"] = code
            matrix[code]["quarters"][f"TW{periode.triwulan}"] = stream.get("score")
    return list(matrix.values())


async def trend_for_indikator(db: AsyncSession, indikator_id: uuid.UUID, tahun: int) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(NkoSnapshot, Periode)
            .join(Periode, NkoSnapshot.periode_id == Periode.id)
            .where(Periode.tahun == tahun)
            .order_by(Periode.triwulan)
        )
    ).all()
    data: list[dict[str, Any]] = []
    needle = str(indikator_id)
    for snapshot, periode in rows:
        for stream in snapshot.breakdown.get("streams", []):
            if stream.get("indikator_id") == needle:
                data.append({"triwulan": periode.triwulan, "score": stream.get("score"), "unit": stream.get("unit")})
    return data
