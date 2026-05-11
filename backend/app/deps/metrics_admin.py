"""Admin gate for /health/detail and /metrics (W-02 fix).

Pre-Plan-05 placeholder: rejects every request with 401 so the endpoints
appear in OpenAPI (consumers can discover them) but cannot be invoked from
an anonymous probe. Plan 05 will REPLACE this entire file with::

    from app.deps.auth import require_role
    metrics_admin_dep = require_role("super_admin", "admin_unit")

Health endpoints import `metrics_admin_dep` by name and do not change.
"""

from fastapi import Header, HTTPException, status


async def metrics_admin_dep(authorization: str | None = Header(default=None)) -> None:
    """Deny all requests until Plan 05 wires `require_role`.

    The `authorization` argument is declared so the dependency renders in
    OpenAPI as Bearer-auth-aware once Plan 05 swaps the implementation.
    Currently unused — the raise happens unconditionally.
    """
    # Plan 05 replaces this implementation with require_role("super_admin", "admin_unit").
    raise HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Admin auth required (Plan 05 wires require_role)",
    )
