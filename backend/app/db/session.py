"""Async SQLAlchemy 2.0 engine + sessionmaker.

`expire_on_commit=False` is **mandatory** for async sessions — without it,
`await session.commit()` invalidates the loaded ORM instances and the next
attribute access triggers an implicit IO load that fails in async context.
See RESEARCH.md Pattern 1 and Pitfall 4, and the canonical SQLAlchemy docs:
https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# expire_on_commit=False is required for async sessions (Pitfall #4)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
