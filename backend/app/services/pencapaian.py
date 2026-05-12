"""Server-authoritative pencapaian and nilai calculations."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def compute_pencapaian(realisasi: Decimal | None, target: Decimal | None, polaritas: str) -> Decimal | None:
    if realisasi is None or target is None or target == 0:
        return None
    if polaritas == "negatif":
        return _q((target / realisasi) * Decimal("100")) if realisasi != 0 else None
    # Phase 2 treats range like positif until Phase 3 ships richer formula semantics.
    return _q((realisasi / target) * Decimal("100"))


def compute_nilai(pencapaian: Decimal | None) -> Decimal | None:
    if pencapaian is None:
        return None
    return _q(max(Decimal("0"), min(pencapaian, Decimal("120"))))


def compute_pair(realisasi: Decimal | None, target: Decimal | None, polaritas: str) -> tuple[Decimal | None, Decimal | None]:
    pencapaian = compute_pencapaian(realisasi, target, polaritas)
    return pencapaian, compute_nilai(pencapaian)
