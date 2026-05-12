"""Bidang master CRUD (REQ-bidang-master + REQ-route-guards).

Mounts under ``/api/v1/bidang`` via the auto-discovery aggregator in
``app/routers/__init__.py``.

RBAC contract (B-01/B-02, spec naming verbatim):

- ``GET``  routes require any authenticated user (``current_user``). Anonymous
  callers get 401. ``pic_bidang`` is *scoped* — only their own
  ``bidang_id`` is visible. ``admin_unit`` / ``super_admin`` / ``asesor`` /
  ``manajer_unit`` / ``viewer`` see everything.
- ``POST`` / ``PATCH`` / ``DELETE`` require ``super_admin`` OR
  ``admin_unit`` AND a valid CSRF token (cookie-mode); Bearer-mode is exempt
  from CSRF per ``require_csrf``'s standard rule.

Soft delete: ``DELETE /bidang/{id}`` sets ``deleted_at = now()`` instead of
hard-deleting. Subsequent reads filter ``WHERE deleted_at IS NULL``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import current_user, require_role
from app.deps.csrf import require_csrf
from app.deps.db import get_db
from app.models.bidang import Bidang
from app.models.user import User
from app.schemas.master import BidangCreate, BidangPublic, BidangUpdate

router = APIRouter(prefix="/bidang", tags=["master-bidang"])


# ---------------------------------------------------------------------------
# READ (any authenticated; pic_bidang is scoped)
# ---------------------------------------------------------------------------


@router.get("", response_model=dict, summary="List bidang (pic_bidang scoped)")
async def list_bidang(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    """List bidang, paginated.

    pic_bidang sees only their own ``user.bidang_id`` (Phase 1 — Phase 2
    expands hierarchy via parent_id traversal). Other roles see every
    non-deleted row.
    """
    q = select(Bidang).where(Bidang.deleted_at.is_(None))

    user_role_names = {r.name for r in user.roles}
    if "pic_bidang" in user_role_names and not (
        user_role_names & {"super_admin", "admin_unit"}
    ):
        # Scope pic_bidang to own bidang_id. If they have no bidang_id
        # assigned, they see an empty list (rather than the whole table).
        if user.bidang_id is None:
            return {
                "data": [],
                "meta": {"page": page, "page_size": page_size, "total": 0},
            }
        q = q.where(Bidang.id == user.bidang_id)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        await db.scalars(
            q.order_by(Bidang.kode)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "data": [BidangPublic.model_validate(r) for r in rows],
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
        },
    }


@router.get(
    "/{bidang_id}",
    response_model=BidangPublic,
    summary="Get bidang by id (pic_bidang scoped)",
)
async def get_bidang(
    bidang_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> BidangPublic:
    row = await db.scalar(
        select(Bidang).where(
            Bidang.id == bidang_id, Bidang.deleted_at.is_(None)
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bidang not found")

    user_role_names = {r.name for r in user.roles}
    if "pic_bidang" in user_role_names and not (
        user_role_names & {"super_admin", "admin_unit"}
    ):
        if user.bidang_id is None or row.id != user.bidang_id:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Bidang not found"
            )

    return BidangPublic.model_validate(row)


# ---------------------------------------------------------------------------
# WRITE (super_admin | admin_unit + CSRF)  — B-01/B-02 spec naming
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=BidangPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create bidang (super_admin|admin_unit + CSRF)",
    tags=["audit:bidang"],
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def create_bidang(
    payload: BidangCreate, db: AsyncSession = Depends(get_db)
) -> BidangPublic:
    # Uniqueness on `kode` is enforced at the DB layer; surface a clean 409
    # for duplicates rather than the raw integrity error.
    existing = await db.scalar(
        select(Bidang).where(
            Bidang.kode == payload.kode, Bidang.deleted_at.is_(None)
        )
    )
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "bidang.kode already exists"
        )
    if payload.parent_id is not None:
        parent = await db.scalar(
            select(Bidang).where(
                Bidang.id == payload.parent_id,
                Bidang.deleted_at.is_(None),
            )
        )
        if not parent:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "parent_id does not reference an active bidang",
            )

    row = Bidang(
        kode=payload.kode,
        nama=payload.nama,
        parent_id=payload.parent_id,
    )
    db.add(row)
    await db.flush()
    await db.commit()
    return BidangPublic.model_validate(row)


@router.patch(
    "/{bidang_id}",
    response_model=BidangPublic,
    summary="Update bidang (super_admin|admin_unit + CSRF)",
    tags=["audit:bidang"],
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def update_bidang(
    bidang_id: uuid.UUID,
    payload: BidangUpdate,
    db: AsyncSession = Depends(get_db),
) -> BidangPublic:
    row = await db.scalar(
        select(Bidang).where(
            Bidang.id == bidang_id, Bidang.deleted_at.is_(None)
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bidang not found")

    data = payload.model_dump(exclude_unset=True)
    if "kode" in data:
        clash = await db.scalar(
            select(Bidang).where(
                Bidang.kode == data["kode"],
                Bidang.id != row.id,
                Bidang.deleted_at.is_(None),
            )
        )
        if clash:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "bidang.kode already exists"
            )
    for k, v in data.items():
        setattr(row, k, v)
    await db.flush()
    await db.commit()
    return BidangPublic.model_validate(row)


@router.delete(
    "/{bidang_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete bidang (super_admin|admin_unit + CSRF)",
    tags=["audit:bidang"],
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def delete_bidang(
    bidang_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> None:
    row = await db.scalar(
        select(Bidang).where(
            Bidang.id == bidang_id, Bidang.deleted_at.is_(None)
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bidang not found")
    row.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await db.commit()
    return None
