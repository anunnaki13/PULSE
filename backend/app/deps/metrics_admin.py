"""Admin gate for /health/detail and /metrics — W-02 wiring (closed by Plan 05).

Plan 03 shipped a placeholder body here that returned 401 unconditionally so
the surface (OpenAPI discoverability + the 401 contract test) could land
before `require_role` existed. Plan 05 swaps the body to delegate to
``require_role("super_admin", "admin_unit")``.

The public symbol ``metrics_admin_dep`` is unchanged — ``backend/app/routers/health.py``
imports it by name and continues to wire it via ``Depends(metrics_admin_dep)``
on ``/health/detail`` and ``/metrics``. No edits required there.

Spec roles per REQ-user-roles (B-01/B-02): ``super_admin`` and ``admin_unit``
are the admin tier. ``pic_bidang``, ``asesor``, ``manajer_unit``, ``viewer``
remain locked out of these endpoints.
"""

from __future__ import annotations

from app.deps.auth import require_role

# W-02 closed: real admin gate. CONTEXT.md API: /health/detail and /metrics
# are admin-only and admin = super_admin OR admin_unit.
metrics_admin_dep = require_role("super_admin", "admin_unit")
