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

from app import __version__
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.routers import api_router

configure_logging(debug=settings.DEBUG)
log = get_logger("pulse.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_ts = time.time()
    log.info("startup", version=__version__)
    yield
    log.info("shutdown")


app = FastAPI(
    title="PULSE — Performance & Unit Live Scoring Engine",
    version=__version__,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.include_router(api_router)
