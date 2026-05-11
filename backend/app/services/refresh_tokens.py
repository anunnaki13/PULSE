"""Redis-backed refresh-token revocation set (REQ-auth-jwt, T-05-S-03).

When a refresh token is rotated (or the user logs out), the old token's
``jti`` is recorded under key ``revoked:{user_id}:{jti}`` with TTL equal to
the token's remaining lifetime. Any subsequent ``/auth/refresh`` request that
presents a revoked refresh token is rejected.

TTL math: ``max(1, int((exp - now).total_seconds()))``. The 1-second floor
prevents ``redis.set(... ex=0)`` (which deletes the key immediately) when the
caller passes an already-expired token.
"""

from __future__ import annotations

from datetime import datetime, timezone

from redis.asyncio import Redis


def _key(user_id: str, jti: str) -> str:
    return f"revoked:{user_id}:{jti}"


async def revoke_jti(r: Redis, user_id: str, jti: str, exp: datetime) -> None:
    """Mark a refresh-token ``jti`` revoked until its original expiration."""
    now = datetime.now(timezone.utc)
    # Ensure exp is timezone-aware (defensive — decode_token always returns aware datetimes).
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    ttl = max(1, int((exp - now).total_seconds()))
    await r.set(_key(user_id, jti), "1", ex=ttl)


async def is_revoked(r: Redis, user_id: str, jti: str) -> bool:
    """Return True iff the (user_id, jti) pair is in the revocation set."""
    return bool(await r.exists(_key(user_id, jti)))
