"""Dashboard WebSocket broadcast helpers."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.services.ws_manager import ws_manager


async def broadcast_nko_updated(
    periode_id: uuid.UUID,
    nko_total: Decimal,
    changed_indikator: uuid.UUID | None = None,
) -> int:
    return await ws_manager.send_to_all(
        {
            "type": "nko_updated",
            "periode_id": str(periode_id),
            "nko_total": float(nko_total),
            "changed_indikator": str(changed_indikator) if changed_indikator else None,
        }
    )
