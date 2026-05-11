"""Double-submit CSRF dep for cookie-mode mutating routes (T-05-T-01).

Pattern: the server sets a non-httpOnly ``csrf_token`` cookie on login. The
frontend reads it (because it's NOT httpOnly) and echoes it back on every
mutating request via the ``X-CSRF-Token`` header. Server-side, this dep
asserts the cookie value equals the header value.

The check is SKIPPED for Bearer-mode requests (no cookies in play, so no CSRF
attack surface — the request can't be triggered by a malicious cross-site
form). This is the standard hybrid pattern for dual-mode (cookie + bearer)
APIs.

Wire on routes by adding ``dependencies=[Depends(require_csrf)]`` to any
mutating endpoint (login is exempt because there's no session yet to
hijack). Per CONTEXT.md API + B-07: the Plan-06 Excel import endpoint MUST
also include this dep.
"""

from __future__ import annotations

import hmac

from fastapi import Cookie, Header, HTTPException, status


async def require_csrf(
    csrf_token: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    authorization: str | None = Header(default=None),
) -> None:
    """Enforce double-submit CSRF on cookie-mode requests.

    - Bearer-mode (``Authorization: Bearer …``): skipped (no CSRF surface).
    - Cookie-mode: require both ``csrf_token`` cookie and ``X-CSRF-Token``
      header AND require they match exactly (constant-time compare).
    """
    if authorization and authorization.lower().startswith("bearer "):
        return
    if not csrf_token or not x_csrf_token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token missing")
    if not hmac.compare_digest(csrf_token, x_csrf_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token mismatch")
