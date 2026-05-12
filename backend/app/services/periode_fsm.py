"""Hand-rolled periode lifecycle state machine."""

from __future__ import annotations

from app.models.periode import PeriodeStatus

FORWARD: dict[PeriodeStatus, dict[PeriodeStatus, str]] = {
    PeriodeStatus.DRAFT: {PeriodeStatus.AKTIF: "drain_pending_carry_overs"},
    PeriodeStatus.AKTIF: {PeriodeStatus.SELF_ASSESSMENT: "create_sessions"},
    PeriodeStatus.SELF_ASSESSMENT: {PeriodeStatus.ASESMEN: "noop"},
    PeriodeStatus.ASESMEN: {PeriodeStatus.FINALISASI: "noop"},
    PeriodeStatus.FINALISASI: {PeriodeStatus.CLOSED: "close_with_carry_over"},
    PeriodeStatus.CLOSED: {},
}
ORDER = [
    PeriodeStatus.DRAFT,
    PeriodeStatus.AKTIF,
    PeriodeStatus.SELF_ASSESSMENT,
    PeriodeStatus.ASESMEN,
    PeriodeStatus.FINALISASI,
    PeriodeStatus.CLOSED,
]


class InvalidTransition(ValueError):
    pass


class RollbackRequiresSuperAdmin(PermissionError):
    pass


class RollbackRequiresReason(ValueError):
    pass


def _coerce(value: PeriodeStatus | str) -> PeriodeStatus:
    return value if isinstance(value, PeriodeStatus) else PeriodeStatus(value)


def is_rollback(current: PeriodeStatus | str, target: PeriodeStatus | str) -> bool:
    return ORDER.index(_coerce(target)) < ORDER.index(_coerce(current))


def assert_transition_allowed(
    current: PeriodeStatus | str,
    target: PeriodeStatus | str,
    role_names: set[str],
    reason: str | None,
) -> str:
    """Return the side-effect token to dispatch."""
    current_s = _coerce(current)
    target_s = _coerce(target)
    if target_s == current_s:
        return "noop"
    fwd = FORWARD.get(current_s, {})
    if target_s in fwd:
        return fwd[target_s]
    if is_rollback(current_s, target_s):
        if "super_admin" not in role_names:
            raise RollbackRequiresSuperAdmin("Only super_admin can rollback periode")
        if not reason or len(reason) < 20:
            raise RollbackRequiresReason("reason must be >= 20 chars on rollback")
        return "rollback"
    raise InvalidTransition(f"Invalid periode transition {current_s.value} -> {target_s.value}")
