"""Security primitives: password hashing + JWT signing/decoding (REQ-auth-jwt).

RESEARCH.md Pattern 3 verbatim. Three guarantees:

1. **Bcrypt for password hashing** — passlib's `CryptContext` with the
   `bcrypt` scheme. `verify_password` is constant-time by passlib.

2. **Explicit algorithm allow-list on decode** — `jwt.decode(...,
   algorithms=[settings.JWT_ALGORITHM])`. This is the canonical mitigation
   for the `alg: none` and HS/RS confusion classes of attacks
   (T-05-S-01 in the plan threat register). Never pass `algorithms=None`
   or rely on the algorithm header from the token itself.

3. **Token typing via `typ` claim** — access tokens carry `typ="access"`,
   refresh tokens carry `typ="refresh"`. The dependency layer enforces
   the right `typ` per endpoint so a refresh token cannot be used as an
   access token and vice versa (RESEARCH.md "refresh rotation").

Refresh tokens also embed a random `jti` so revocation can be tracked
per-token in Redis (see `app.services.refresh_tokens`).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
from jose import jwt

from app.core.config import settings

# Note: RESEARCH.md asked for passlib[bcrypt]==1.7.4 + bcrypt==5.0.0. Those
# two are mutually incompatible: passlib 1.7.4's bcrypt backend introspects
# `bcrypt.__about__.__version__`, which bcrypt 5.x removed, and then its
# stub probe trips bcrypt's new "password > 72 bytes" check with
# ValueError. We use the native `bcrypt` API directly — same algorithm,
# same hash format (PHC `$2b$...`), no extra dependency, and no shim layer
# to break on the next bcrypt minor. This is a Rule-1 bug fix vs. the
# pinned stack; passlib is kept on the dependency list as a transitive
# (FastAPI tutorials still reference it) but is not imported by code.

# bcrypt's own enforcement: passwords > 72 bytes raise ValueError. We
# truncate at 72 bytes deliberately so the API can't be tripped by a
# pathological input (bcrypt's 72-byte effective limit is a feature, not
# a bug). UTF-8 encode → truncate → encode-back is idempotent for
# ASCII-only passwords and safely lossy for multi-byte ones; this matches
# what every modern bcrypt-backed framework does.
_BCRYPT_MAX_BYTES = 72


def _safe_bytes(plain: str) -> bytes:
    b = plain.encode("utf-8")
    return b[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt (work factor default = 12)."""
    return bcrypt.hashpw(_safe_bytes(plain), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time bcrypt verify. Returns False on mismatch or malformed hash."""
    try:
        return bcrypt.checkpw(_safe_bytes(plain), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    sub: str, roles: list[str], bidang_id: str | None
) -> tuple[str, datetime]:
    """Build an access JWT.

    Claims: ``{sub, roles, bidang_id, iat, exp, typ="access"}``.
    Returns ``(token, exp)`` so callers can set cookie ``expires=`` to match.
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.JWT_ACCESS_TTL_MIN)
    payload = {
        "sub": sub,
        "roles": roles,
        "bidang_id": bidang_id,
        "iat": now,
        "exp": exp,
        "typ": "access",
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, exp


def create_refresh_token(sub: str) -> tuple[str, str, datetime]:
    """Build a refresh JWT.

    Claims: ``{sub, jti, iat, exp, typ="refresh"}``.
    Returns ``(token, jti, exp)`` — ``jti`` is the revocation key.
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    jti = uuid4().hex
    payload = {
        "sub": sub,
        "jti": jti,
        "iat": now,
        "exp": exp,
        "typ": "refresh",
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, jti, exp


def decode_token(token: str) -> dict:
    """Decode any JWT (access or refresh) with the explicit algorithm allow-list.

    Raises ``jose.JWTError`` (or subclass like ``ExpiredSignatureError``) on
    malformed / expired / wrong-signature tokens.

    The ``algorithms=[settings.JWT_ALGORITHM]`` allow-list is the canonical
    defense against ``alg: none`` and HS↔RS confusion attacks (T-05-S-01).
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithms=[settings.JWT_ALGORITHM],
    )
