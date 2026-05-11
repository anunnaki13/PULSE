"""Alembic env.py — async-aware, sources URL from app.core.config.settings.

Pattern: use `connection.run_sync(do_migrations)` so Alembic's sync-style
`MigrationContext` runs over an `AsyncConnection` from the SQLAlchemy 2.x
async engine. Importing `app.db.base` pulls in `Base` AND triggers the
auto-import walk over `app/models/` so `target_metadata` sees every table
that has been declared by Plan 05 / Plan 06 by the time autogenerate runs.

CITED: https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base  # noqa: F401 — triggers auto-import of all models

# Alembic Config object provides access to values within the .ini file in use.
config = context.config

# Inject the SQLAlchemy URL from settings so .env / pydantic-settings owns it.
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URL)

# Configure Python logging according to alembic.ini logger sections.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (emits SQL to stdout)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
