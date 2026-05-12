from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import WebSocket

from app.core.logging import get_logger

log = get_logger("pulse.ws.manager")


class WsManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._conns: dict[str, set[WebSocket]] = defaultdict(set)

    async def register(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._conns[user_id].add(ws)
            log.info("ws_registered", user_id=user_id, count=len(self._conns[user_id]))

    async def unregister(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._conns[user_id].discard(ws)
            if not self._conns[user_id]:
                del self._conns[user_id]
            log.info("ws_unregistered", user_id=user_id)

    async def send_to_user(self, user_id: str, payload: dict) -> int:
        async with self._lock:
            sockets = list(self._conns.get(user_id, set()))
        sent = 0
        for sock in sockets:
            try:
                await sock.send_json(payload)
                sent += 1
            except Exception as exc:
                log.warning("ws_send_failed", user_id=user_id, error=str(exc))
        return sent

    async def send_to_all(self, payload: dict) -> int:
        async with self._lock:
            sockets = [sock for group in self._conns.values() for sock in group]
        sent = 0
        for sock in sockets:
            try:
                await sock.send_json(payload)
                sent += 1
            except Exception as exc:
                log.warning("ws_broadcast_failed", error=str(exc))
        return sent

    def online_users(self) -> set[str]:
        return set(self._conns.keys())


ws_manager = WsManager()
