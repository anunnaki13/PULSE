"""Pytest fixtures shared by Plans 03/05/06.

Provides:

- ``client`` — ``httpx.AsyncClient(transport=ASGITransport(app))`` so tests
  hit the FastAPI app in-process (no real network, no docker container
  required for unit tests). Reused by Plan 05 (auth) and Plan 06
  (master data).

- ``db_session`` — ``AsyncSession`` wrapped in a transaction that rolls back
  at teardown. Engine is lazy-imported so ``pytest --collect-only`` (and
  any pure-import test like ``test_no_upload_policy.py``) does NOT require
  a live Postgres. Only tests that actually consume ``db_session`` open a
  connection — those will fail with a connection error when no Postgres
  is available, which is acceptable for the unit suite. Plan 07's
  container e2e exercises the live-DB path end-to-end.

- **Plan-05 extension (DB-app integration):** when a test uses BOTH
  ``client`` and ``db_session``, the app's ``get_db`` dependency is
  overridden to yield the SAME session bound to the SAME transaction the
  fixture set up. Without this override, the fixture's INSERTs are
  invisible to the app's separate sessionmaker (the fixture rolls back at
  teardown, the app would only see committed rows).

  Pattern: ``app.dependency_overrides[get_db] = lambda: yield <fixture
  session>``. We additionally call ``conn.begin_nested()`` after the outer
  transaction so the app's ``await session.commit()`` (used by the
  ``rollback-on-exception`` block in ``get_db``) commits the SAVEPOINT,
  not the outer transaction, and the outer rollback at teardown still
  scrubs everything.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.deps.db import get_db
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def _flush_redis():
    """Flush the test Redis DB between tests to keep counters / revocation
    sets isolated.

    Brute-force lockout counters (``login_fail:{email}``) and refresh-token
    revocation entries (``revoked:{user_id}:{jti}``) live in Redis with a
    TTL that outlasts a single test. Without flushing, test N's leftover
    state contaminates test N+1 (e.g. the brute-force lockout test leaves
    a counter at 5 for ``admin@pulse.local``, so the next test that
    logs in with that email immediately returns 429).

    Best-effort: if Redis isn't reachable (host-only tests like
    test_password_hash_roundtrip), the fixture silently no-ops. This
    preserves the Plan-03 unit-mode behavior where tests that don't need
    Redis don't fail just because no broker is running.
    """
    try:
        from redis.asyncio import from_url

        from app.core.config import settings

        client = from_url(settings.REDIS_URL, decode_responses=True)
        try:
            await client.flushdb()
        finally:
            await client.aclose()
    except Exception:
        # Redis offline → no state to clear → no problem.
        pass
    yield

# NOTE: the event loop is managed by pytest-asyncio via the
# `asyncio_default_fixture_loop_scope = "session"` config in pyproject.toml
# — do NOT define a custom session-scoped `event_loop` fixture here, that
# pattern is deprecated in pytest-asyncio 1.x and produces "Event loop is
# closed" failures with the SQLAlchemy async engine pool.


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Transactional async session bound to a single dedicated connection.

    Two-level transaction: the OUTER transaction lives for the test's
    lifetime and is rolled back at teardown. INNER work happens inside a
    SAVEPOINT (begin_nested) so that any commits issued by the app (or by
    Plan 06's import endpoint) don't escape the outer rollback — they
    just release the savepoint.
    """
    from app.db.session import engine as _engine

    async with _engine.connect() as conn:
        trans = await conn.begin()
        SessionFactory = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with SessionFactory() as s:
            # Inner savepoint — survives commits, dies on outer rollback.
            await s.begin_nested()
            try:
                yield s
            finally:
                await trans.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """AsyncClient that shares the test's ``db_session`` with the app.

    The ``get_db`` dependency override yields the SAME session the fixture
    set up. This is what makes a row INSERTed by the test fixture visible
    to the app handler inside the same test.

    The override is removed on fixture teardown so subsequent tests can
    install a fresh override against their own ``db_session``.
    """

    async def _override_get_db():
        # Re-open a savepoint per request so the handler's commit
        # (rollback-on-exception in app/deps/db.py's get_db) lives only
        # within this request — outer transaction is unaffected.
        async with db_session.begin_nested():
            yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
