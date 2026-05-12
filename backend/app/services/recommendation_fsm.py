"""Recommendation lifecycle guards."""

from __future__ import annotations

from app.models.recommendation import RecommendationStatus

AUTO_ON_PROGRESS: set[RecommendationStatus] = {RecommendationStatus.OPEN}
AFTER_PROGRESS = RecommendationStatus.IN_PROGRESS
MARK_COMPLETED_ALLOWED_FROM = {RecommendationStatus.IN_PROGRESS, RecommendationStatus.OPEN}
VERIFY_CLOSE_ALLOWED_FROM = {RecommendationStatus.PENDING_REVIEW}


class InvalidLifecycle(ValueError):
    pass


def _coerce(value: RecommendationStatus | str) -> RecommendationStatus:
    return value if isinstance(value, RecommendationStatus) else RecommendationStatus(value)


def assert_mark_completed_allowed(current: RecommendationStatus | str) -> None:
    if _coerce(current) not in MARK_COMPLETED_ALLOWED_FROM:
        raise InvalidLifecycle(f"mark-completed not allowed from {_coerce(current).value}")


def assert_verify_close_allowed(current: RecommendationStatus | str) -> None:
    if _coerce(current) not in VERIFY_CLOSE_ALLOWED_FROM:
        raise InvalidLifecycle(f"verify-close requires pending_review; got {_coerce(current).value}")
