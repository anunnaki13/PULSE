"""FastAPI application entrypoint.

Boots the PULSE backend with:
- /api/v1 prefix on every router (delegated to `app.routers.api_router`)
- OpenAPI docs at /api/v1/docs, ReDoc at /api/v1/redoc
- structlog-backed JSON logging, level driven by `settings.DEBUG`
- A lifespan handler that records `app.state.startup_ts` so /health/detail
  and /metrics can report uptime without re-importing process time elsewhere.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app import __version__
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.routers import api_router
from app.routers.ws_dashboard import ws_router as dashboard_ws_router
from app.routers.ws_notifications import ws_router as notifications_ws_router
from app.services.audit_middleware import AuditMiddleware

configure_logging(debug=settings.DEBUG)
log = get_logger("pulse.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_ts = time.time()
    _audit_tag_startup_gate(app)
    log.info("startup", version=__version__)
    yield
    log.info("shutdown")


def _audit_tag_startup_gate(app: FastAPI) -> None:
    """Fail startup when mutating API routes lack an audit entity tag."""
    offenders: list[str] = []
    audit_exempt = {"/api/v1/auth/refresh"}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = (route.methods or set()) - {"GET", "HEAD", "OPTIONS"}
        if not methods or not route.path.startswith("/api/v1/"):
            continue
        if route.path in audit_exempt:
            continue
        if not any(isinstance(tag, str) and tag.startswith("audit:") for tag in route.tags or []):
            offenders.append(f"{sorted(methods)} {route.path}")
    if offenders:
        raise RuntimeError(
            "Mutating /api/v1 routes missing audit:<entity> tag:\n"
            + "\n".join(f"  - {item}" for item in offenders)
        )


app = FastAPI(
    title="PULSE — Performance & Unit Live Scoring Engine",
    version=__version__,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.include_router(api_router)
app.include_router(notifications_ws_router)
app.include_router(dashboard_ws_router)
app.add_middleware(AuditMiddleware)
