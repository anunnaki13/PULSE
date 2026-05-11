"""Auto-discovery router aggregator.

`api_router` is the single `APIRouter` that `main.py` mounts at /api/v1.
This file walks every sibling module under `app/routers/` and includes any
that expose a top-level `router` attribute. Plans 05 (auth) and 06 (master
data) add new files here and they get picked up automatically — main.py
and this file never need to be edited.

Convention for privileged routes (admin-only): each endpoint should list
`dependencies=[Depends(require_role("super_admin", "admin_unit"))]` once
Plan 05 ships `require_role`. Until then, Plan 03 uses the placeholder
`metrics_admin_dep` from `app.deps.metrics_admin` which always returns 401.
"""

import importlib
import pathlib
import pkgutil

from fastapi import APIRouter

from app.core.logging import get_logger

log = get_logger("pulse.routers")

api_router = APIRouter(prefix="/api/v1")

_here = pathlib.Path(__file__).parent
for _mi in pkgutil.iter_modules([str(_here)]):
    if _mi.name.startswith("_"):
        continue
    _mod = importlib.import_module(f"{__name__}.{_mi.name}")
    _router = getattr(_mod, "router", None)
    if _router is not None:
        api_router.include_router(_router)
        log.info("router_included", module=_mi.name)
