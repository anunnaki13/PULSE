"""FastAPI dependency: per-request async SQLAlchemy session.

Verbatim RESEARCH.md Pattern 1: yields an `AsyncSession` and rolls back on
exception, then closes via `async with`. Every router that needs the DB
declares `db: AsyncSession = Depends(get_db)`.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
