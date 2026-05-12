from __future__ import annotations

from jose import JWTError
from redis.asyncio import from_url

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import decode_token
from app.services.refresh_tokens import is_revoked

log = get_logger("pulse.ws.auth")


class WsAuthFailed(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason


async def validate_ws_token(token: str) -> str:
    """Return user_id for a valid access token; raise on invalid/revoked token."""
    try:
        claims = decode_token(token)
    except JWTError as exc:
        log.warning("ws_token_invalid", error=str(exc))
        raise WsAuthFailed("invalid_token") from exc
    if claims.get("typ") != "access":
        raise WsAuthFailed("wrong_token_type")
    user_id = claims.get("sub")
    jti = claims.get("jti")
    if not user_id or not jti:
        raise WsAuthFailed("missing_claims")

    redis = from_url(settings.REDIS_URL, decode_responses=True)
    try:
        if await is_revoked(redis, str(user_id), str(jti)):
            raise WsAuthFailed("revoked")
    finally:
        await redis.aclose()
    return str(user_id)
