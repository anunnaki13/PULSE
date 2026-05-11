"""FastAPI dependency: per-request async Redis client.

`decode_responses=True` keeps the surface dict-friendly (`info("memory")`
yields a `dict[str, str]` rather than bytes). Connection is closed on
generator exit, which honors the request scope.
"""

from typing import AsyncGenerator

from redis.asyncio import Redis, from_url

from app.core.config import settings


async def get_redis() -> AsyncGenerator[Redis, None]:
    client = from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()
