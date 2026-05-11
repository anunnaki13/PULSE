"""Pytest fixtures shared by Plans 03/05/06.

Provides:

- `client` — `httpx.AsyncClient(transport=ASGITransport(app))` so tests hit
  the FastAPI app in-process (no real network, no docker container needed
  for unit tests). Reused by Plan 05 (auth) and Plan 06 (master data).

- `db_session` — `AsyncSession` wrapped in a transaction that rolls back at
  teardown. Engine is lazy-imported so `pytest --collect-only` (and any
  pure-import test like `test_no_upload_policy.py`) does NOT require a
  live Postgres. Only tests that actually consume `db_session` open a
  connection — those will fail with a connection error when no Postgres
  is available, which is acceptable for the unit suite. Plan 07's
  container e2e is where the live-DB path is exercised end-to-end.
"""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    # Transactional fixture: every test runs inside a SAVEPOINT and rolls back.
    # Lazy-import engine to avoid forcing a DB connection during pytest --collect-only.
    from app.db.session import engine as _engine

    async with _engine.connect() as conn:
        trans = await conn.begin()
        SessionFactory = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with SessionFactory() as s:
            try:
                yield s
            finally:
                await trans.rollback()
