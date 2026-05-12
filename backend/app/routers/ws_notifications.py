from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.logging import get_logger
from app.deps.ws_auth import WsAuthFailed, validate_ws_token
from app.services.ws_manager import ws_manager

log = get_logger("pulse.ws.notifications")

ws_router = APIRouter()


@ws_router.websocket("/ws/notifications")
async def notifications_ws(websocket: WebSocket, token: str = Query(...)) -> None:
    try:
        user_id = await validate_ws_token(token)
    except WsAuthFailed as exc:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=exc.reason,
        )
        return

    await websocket.accept()
    await ws_manager.register(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.unregister(user_id, websocket)
