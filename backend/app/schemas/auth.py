"""Auth request / response DTOs (Pydantic v2).

``TokenPair`` is the response shape of both ``POST /auth/login`` and
``POST /auth/refresh``. The frontend (Plan 07) consumes this verbatim — its
React Query types mirror these fields.

``LoginRequest`` accepts JSON body. The auth router additionally accepts
form-encoded body for OpenAPI / Swagger-UI compatibility (per the plan's
"JSON or form" must_have).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserPublic

# RFC 5322 cheap-shape regex. We deliberately don't use pydantic.EmailStr
# (email-validator) because it rejects the `.local` TLD that the production
# deployment uses (CONTEXT.md: INITIAL_ADMIN_EMAIL=admin@pulse.local —
# RFC 6762 mDNS reserved, but legitimate for our internal hostname scheme).
# This regex matches `local-part@domain.tld` with at least one dot in the
# domain part — sufficient validation for the login path. Final deliverability
# is gated by Postgres uniqueness + bcrypt verify, not by client-side regex.
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def _email_shape(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email format")
        return v


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserPublic


class RefreshRequest(BaseModel):
    """Optional body for POST /auth/refresh.

    The refresh route ALSO accepts the refresh token from the
    ``refresh_token`` cookie or an ``Authorization: Bearer`` header, so the
    body is optional. When present, it takes precedence over header+cookie.
    """

    refresh_token: str | None = None
