"""Auth request / response DTOs (Pydantic v2).

``TokenPair`` is the response shape of both ``POST /auth/login`` and
``POST /auth/refresh``. The frontend (Plan 07) consumes this verbatim — its
React Query types mirror these fields.

``LoginRequest`` accepts JSON body. The auth router additionally accepts
form-encoded body for OpenAPI / Swagger-UI compatibility (per the plan's
"JSON or form" must_have).
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserPublic


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


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
