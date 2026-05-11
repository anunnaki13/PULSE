"""Konkin-template + perspektif + indikator + ml_stream CRUD (Plan 06).

Mounts under ``/api/v1/`` via the auto-discovery aggregator in
``app/routers/__init__.py``. Sub-prefixes:

- ``/konkin/templates``                                           — template CRUD + lock + import
- ``/konkin/templates/{template_id}/perspektif``                  — perspektif CRUD
- ``/konkin/perspektif/{perspektif_id}/indikator``                — indikator CRUD
- ``/ml-stream``                                                  — ML stream CRUD

RBAC (spec naming — B-01/B-02):
- All write routes: ``Depends(require_role("super_admin","admin_unit"))`` +
  ``Depends(require_csrf)``.
- Read routes: ``Depends(current_user)`` (any authenticated; anonymous = 401).

Lock semantics (REQ-konkin-template-crud):
- ``POST /konkin/templates/{id}/lock`` triggers the W-07-aware bobot
  validator (see ``_validate_template_for_lock``). On pass, the row's
  ``locked`` becomes True. Once locked, every mutating route returns 409
  Conflict.

Excel import (REQ-no-evidence-upload final form):
- ``POST /konkin/templates/{id}/import-from-excel`` is the SINGLE multipart
  endpoint in the entire API surface (test_no_upload_policy asserts this).
  B-07 fix: it requires ``require_role("super_admin","admin_unit")`` AND
  ``require_csrf`` — same CSRF rule as every other cookie-reachable
  mutating route. The earlier-draft comment incorrectly suggesting that
  cookie CSRF could be skipped because callers would use Bearer mode has
  been removed; cookie callers MUST present the X-CSRF-Token header.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import current_user, require_role
from app.deps.csrf import require_csrf
from app.deps.db import get_db
from app.models.indikator import Indikator
from app.models.konkin_template import KonkinTemplate
from app.models.ml_stream import MlStream
from app.models.perspektif import Perspektif
from app.models.user import User
from app.schemas.master import (
    IndikatorCreate,
    IndikatorPublic,
    IndikatorUpdate,
    MlStreamCreate,
    MlStreamDetail,
    MlStreamPublic,
    MlStreamUpdate,
    PerspektifCreate,
    PerspektifPublic,
    PerspektifUpdate,
    TemplateCreate,
    TemplatePublic,
    TemplateUpdate,
)
from app.services import excel_import

router = APIRouter(tags=["master-konkin"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_template_or_404(
    db: AsyncSession, template_id: uuid.UUID
) -> KonkinTemplate:
    row = await db.scalar(
        select(KonkinTemplate).where(
            KonkinTemplate.id == template_id,
            KonkinTemplate.deleted_at.is_(None),
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")
    return row


def _ensure_unlocked(template: KonkinTemplate) -> None:
    """Reject any mutating call on a locked template with 409."""
    if template.locked:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Template is locked; clone it to make further changes",
        )


# ---------------------------------------------------------------------------
# Template CRUD
# ---------------------------------------------------------------------------


@router.get(
    "/konkin/templates",
    response_model=dict,
    summary="List konkin templates",
)
async def list_templates(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    q = select(KonkinTemplate).where(KonkinTemplate.deleted_at.is_(None))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        await db.scalars(
            q.order_by(KonkinTemplate.tahun.desc(), KonkinTemplate.nama)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "data": [TemplatePublic.model_validate(r) for r in rows],
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
        },
    }


@router.get(
    "/konkin/templates/{template_id}",
    response_model=TemplatePublic,
    summary="Get konkin template",
)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
) -> TemplatePublic:
    row = await _get_template_or_404(db, template_id)
    return TemplatePublic.model_validate(row)


async def _clone_template(
    db: AsyncSession,
    source: KonkinTemplate,
    new_tahun: int,
    new_nama: str,
) -> KonkinTemplate:
    """Deep-copy perspektif + indikator chains from `source` to a fresh template.

    The clone is created *unlocked* even if the source was locked, so the
    target year's admin can edit freely. W-07 carry-over: ``is_pengurang``
    and ``pengurang_cap`` propagate verbatim on perspektif rows.
    """
    target = KonkinTemplate(tahun=new_tahun, nama=new_nama, locked=False)
    db.add(target)
    await db.flush()  # assigns target.id

    src_persp = (
        await db.scalars(
            select(Perspektif).where(Perspektif.template_id == source.id)
        )
    ).all()
    for sp in src_persp:
        np_ = Perspektif(
            template_id=target.id,
            kode=sp.kode,
            nama=sp.nama,
            bobot=sp.bobot,
            # W-07 carry-over — verbatim.
            is_pengurang=sp.is_pengurang,
            pengurang_cap=sp.pengurang_cap,
            sort_order=sp.sort_order,
        )
        db.add(np_)
        await db.flush()  # assigns np_.id

        src_ind = (
            await db.scalars(
                select(Indikator).where(
                    Indikator.perspektif_id == sp.id,
                    Indikator.deleted_at.is_(None),
                )
            )
        ).all()
        for si in src_ind:
            db.add(
                Indikator(
                    perspektif_id=np_.id,
                    kode=si.kode,
                    nama=si.nama,
                    bobot=si.bobot,
                    polaritas=si.polaritas,
                    formula=si.formula,
                    link_eviden=si.link_eviden,
                )
            )
    await db.flush()
    return target


@router.post(
    "/konkin/templates",
    response_model=TemplatePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create or clone konkin template (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def create_template(
    payload: TemplateCreate, db: AsyncSession = Depends(get_db)
) -> TemplatePublic:
    clash = await db.scalar(
        select(KonkinTemplate).where(
            KonkinTemplate.tahun == payload.tahun,
            KonkinTemplate.nama == payload.nama,
            KonkinTemplate.deleted_at.is_(None),
        )
    )
    if clash:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Template with (tahun, nama) already exists",
        )

    if payload.clone_from_id is not None:
        source = await db.scalar(
            select(KonkinTemplate).where(
                KonkinTemplate.id == payload.clone_from_id,
                KonkinTemplate.deleted_at.is_(None),
            )
        )
        if not source:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "clone_from_id does not reference an active template",
            )
        target = await _clone_template(
            db, source, payload.tahun, payload.nama
        )
    else:
        target = KonkinTemplate(
            tahun=payload.tahun, nama=payload.nama, locked=False
        )
        db.add(target)
        await db.flush()

    await db.commit()
    return TemplatePublic.model_validate(target)


@router.patch(
    "/konkin/templates/{template_id}",
    response_model=TemplatePublic,
    summary="Update konkin template (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def update_template(
    template_id: uuid.UUID,
    payload: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
) -> TemplatePublic:
    row = await _get_template_or_404(db, template_id)
    _ensure_unlocked(row)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    await db.flush()
    await db.commit()
    return TemplatePublic.model_validate(row)


# ---------------------------------------------------------------------------
# Lock validator (W-07: exclude is_pengurang rows from perspektif-sum check
# AND from the inner indikator-sum check)
# ---------------------------------------------------------------------------


_LOCK_TOLERANCE = Decimal("0.01")
_HUNDRED = Decimal("100.00")


async def _validate_template_for_lock(
    db: AsyncSession, template_id: uuid.UUID
) -> None:
    """Run the bobot-sum validator. Raises 422 with a structured detail if
    any rule fails.

    Rules (W-07-aware):
    1. SUM(perspektif.bobot) WHERE is_pengurang = FALSE must equal 100.00
       within ``_LOCK_TOLERANCE`` (0.01 pp).
    2. For each *non-pengurang* perspektif: SUM(indikator.bobot) must equal
       100.00 within ``_LOCK_TOLERANCE``. Pengurang perspektif rows are
       excluded — their indikator are computed differently per the Phase-3
       NKO calc.
    """
    rows = (
        await db.scalars(
            select(Perspektif).where(Perspektif.template_id == template_id)
        )
    ).all()
    non_pengurang = [r for r in rows if not r.is_pengurang]

    # ---- Rule 1: non-pengurang perspektif sum == 100 ± tol ---------------
    sum_persp = sum((p.bobot for p in non_pengurang), Decimal("0"))
    if abs(sum_persp - _HUNDRED) > _LOCK_TOLERANCE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "bobot_perspektif_invalid",
                "expected": str(_HUNDRED),
                "actual": str(sum_persp),
                "tolerance": str(_LOCK_TOLERANCE),
                "offending": [
                    {
                        "id": str(p.id),
                        "kode": p.kode,
                        "bobot": str(p.bobot),
                        "is_pengurang": p.is_pengurang,
                    }
                    for p in rows
                ],
                "rule": "SUM(bobot) WHERE is_pengurang = FALSE must equal "
                "100.00 (W-07)",
            },
        )

    # ---- Rule 2: indikator sum per non-pengurang perspektif --------------
    for p in non_pengurang:
        inds = (
            await db.scalars(
                select(Indikator).where(
                    Indikator.perspektif_id == p.id,
                    Indikator.deleted_at.is_(None),
                )
            )
        ).all()
        sum_ind = sum((i.bobot for i in inds), Decimal("0"))
        if abs(sum_ind - _HUNDRED) > _LOCK_TOLERANCE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "bobot_indikator_invalid",
                    "perspektif_id": str(p.id),
                    "perspektif_kode": p.kode,
                    "expected": str(_HUNDRED),
                    "actual": str(sum_ind),
                    "tolerance": str(_LOCK_TOLERANCE),
                    "rule": "SUM(indikator.bobot) per non-pengurang "
                    "perspektif must equal 100.00",
                },
            )


@router.post(
    "/konkin/templates/{template_id}/lock",
    response_model=TemplatePublic,
    summary="Lock template (W-07 bobot validator; super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def lock_template(
    template_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> TemplatePublic:
    row = await _get_template_or_404(db, template_id)
    if row.locked:
        # Idempotent: locking an already-locked template is a no-op success.
        return TemplatePublic.model_validate(row)

    await _validate_template_for_lock(db, template_id)
    row.locked = True
    await db.flush()
    await db.commit()
    return TemplatePublic.model_validate(row)


# ---------------------------------------------------------------------------
# Excel import (single multipart endpoint — REQ-no-evidence-upload + B-07)
# ---------------------------------------------------------------------------


@router.post(
    "/konkin/templates/{template_id}/import-from-excel",
    status_code=status.HTTP_201_CREATED,
    summary="Import perspektif + indikator from .xlsx (admin + CSRF — B-07)",
    dependencies=[
        # B-07 fix: cookie-mode CSRF defense, same as every other mutating
        # route. Bearer-mode callers are skipped by require_csrf's standard
        # rule (no CSRF surface). The earlier draft's comment claiming the
        # endpoint could rely on bearer-only auth has been removed — cookie
        # callers MUST echo the X-CSRF-Token header.
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def import_from_excel(
    template_id: uuid.UUID,
    file: Annotated[UploadFile, File(...)],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("super_admin", "admin_unit")),
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key"
    ),
):
    """Stream-parse a .xlsx into perspektif + indikator rows for the
    referenced template.

    Idempotency: when the client sends ``Idempotency-Key``, a second request
    with the same key returns ``200 already_applied`` (not ``201``) and the
    workbook is NOT re-parsed — see ``app.services.excel_import`` for the
    log-row machinery.

    Returns the import summary (per-sheet row counts).
    """
    if file.content_type not in excel_import.ALLOWED_CT:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Only .xlsx accepted",
        )
    template = await _get_template_or_404(db, template_id)
    _ensure_unlocked(template)

    raw = await file.read()
    result = await excel_import.import_workbook(
        db=db,
        template=template,
        raw=raw,
        idempotency_key=idempotency_key,
        imported_by=user.id,
    )
    status_code = (
        status.HTTP_200_OK
        if result.get("status") == "already_applied"
        else status.HTTP_201_CREATED
    )
    return JSONResponse(
        status_code=status_code, content={"data": result}
    )


# ---------------------------------------------------------------------------
# Perspektif CRUD (nested under template)
# ---------------------------------------------------------------------------


@router.get(
    "/konkin/templates/{template_id}/perspektif",
    response_model=dict,
    summary="List perspektif for a template",
)
async def list_perspektif(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
) -> dict:
    await _get_template_or_404(db, template_id)
    rows = (
        await db.scalars(
            select(Perspektif)
            .where(Perspektif.template_id == template_id)
            .order_by(Perspektif.sort_order, Perspektif.kode)
        )
    ).all()
    return {"data": [PerspektifPublic.model_validate(r) for r in rows]}


@router.post(
    "/konkin/templates/{template_id}/perspektif",
    response_model=PerspektifPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Add perspektif (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def create_perspektif(
    template_id: uuid.UUID,
    payload: PerspektifCreate,
    db: AsyncSession = Depends(get_db),
) -> PerspektifPublic:
    template = await _get_template_or_404(db, template_id)
    _ensure_unlocked(template)
    clash = await db.scalar(
        select(Perspektif).where(
            Perspektif.template_id == template_id,
            Perspektif.kode == payload.kode,
        )
    )
    if clash:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "perspektif.kode already used in this template",
        )
    row = Perspektif(
        template_id=template_id,
        kode=payload.kode,
        nama=payload.nama,
        bobot=payload.bobot,
        is_pengurang=payload.is_pengurang,
        pengurang_cap=payload.pengurang_cap,
        sort_order=payload.sort_order,
    )
    db.add(row)
    await db.flush()
    await db.commit()
    return PerspektifPublic.model_validate(row)


@router.patch(
    "/konkin/perspektif/{perspektif_id}",
    response_model=PerspektifPublic,
    summary="Update perspektif (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def update_perspektif(
    perspektif_id: uuid.UUID,
    payload: PerspektifUpdate,
    db: AsyncSession = Depends(get_db),
) -> PerspektifPublic:
    row = await db.scalar(
        select(Perspektif).where(Perspektif.id == perspektif_id)
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Perspektif not found")
    template = await _get_template_or_404(db, row.template_id)
    _ensure_unlocked(template)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    await db.flush()
    await db.commit()
    return PerspektifPublic.model_validate(row)


@router.delete(
    "/konkin/perspektif/{perspektif_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete perspektif (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def delete_perspektif(
    perspektif_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> None:
    row = await db.scalar(
        select(Perspektif).where(Perspektif.id == perspektif_id)
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Perspektif not found")
    template = await _get_template_or_404(db, row.template_id)
    _ensure_unlocked(template)
    await db.delete(row)
    await db.flush()
    await db.commit()
    return None


# ---------------------------------------------------------------------------
# Indikator CRUD (nested under perspektif)
# ---------------------------------------------------------------------------


@router.get(
    "/konkin/perspektif/{perspektif_id}/indikator",
    response_model=dict,
    summary="List indikator for a perspektif",
)
async def list_indikator(
    perspektif_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
) -> dict:
    persp = await db.scalar(
        select(Perspektif).where(Perspektif.id == perspektif_id)
    )
    if not persp:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Perspektif not found")
    rows = (
        await db.scalars(
            select(Indikator)
            .where(
                Indikator.perspektif_id == perspektif_id,
                Indikator.deleted_at.is_(None),
            )
            .order_by(Indikator.kode)
        )
    ).all()
    return {"data": [IndikatorPublic.model_validate(r) for r in rows]}


@router.post(
    "/konkin/perspektif/{perspektif_id}/indikator",
    response_model=IndikatorPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Add indikator (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def create_indikator(
    perspektif_id: uuid.UUID,
    payload: IndikatorCreate,
    db: AsyncSession = Depends(get_db),
) -> IndikatorPublic:
    persp = await db.scalar(
        select(Perspektif).where(Perspektif.id == perspektif_id)
    )
    if not persp:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Perspektif not found")
    template = await _get_template_or_404(db, persp.template_id)
    _ensure_unlocked(template)
    row = Indikator(
        perspektif_id=perspektif_id,
        kode=payload.kode,
        nama=payload.nama,
        bobot=payload.bobot,
        polaritas=payload.polaritas,
        formula=payload.formula,
        # HttpUrl -> str when persisting; Pydantic v2 emits str(url).
        link_eviden=str(payload.link_eviden) if payload.link_eviden else None,
    )
    db.add(row)
    await db.flush()
    await db.commit()
    return IndikatorPublic.model_validate(row)


@router.patch(
    "/konkin/indikator/{indikator_id}",
    response_model=IndikatorPublic,
    summary="Update indikator (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def update_indikator(
    indikator_id: uuid.UUID,
    payload: IndikatorUpdate,
    db: AsyncSession = Depends(get_db),
) -> IndikatorPublic:
    row = await db.scalar(
        select(Indikator).where(
            Indikator.id == indikator_id, Indikator.deleted_at.is_(None)
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indikator not found")
    persp = await db.scalar(
        select(Perspektif).where(Perspektif.id == row.perspektif_id)
    )
    template = await _get_template_or_404(db, persp.template_id)
    _ensure_unlocked(template)
    data = payload.model_dump(exclude_unset=True)
    if "link_eviden" in data and data["link_eviden"] is not None:
        data["link_eviden"] = str(data["link_eviden"])
    for k, v in data.items():
        setattr(row, k, v)
    await db.flush()
    await db.commit()
    return IndikatorPublic.model_validate(row)


@router.delete(
    "/konkin/indikator/{indikator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete indikator (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def delete_indikator(
    indikator_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> None:
    row = await db.scalar(
        select(Indikator).where(
            Indikator.id == indikator_id, Indikator.deleted_at.is_(None)
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indikator not found")
    persp = await db.scalar(
        select(Perspektif).where(Perspektif.id == row.perspektif_id)
    )
    template = await _get_template_or_404(db, persp.template_id)
    _ensure_unlocked(template)
    row.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await db.commit()
    return None


# ---------------------------------------------------------------------------
# ML Stream CRUD (REQ-dynamic-ml-schema)
# ---------------------------------------------------------------------------


@router.get(
    "/ml-stream",
    response_model=dict,
    summary="List ML streams",
)
async def list_ml_stream(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    q = select(MlStream).where(MlStream.deleted_at.is_(None))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (
        await db.scalars(
            q.order_by(MlStream.kode)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "data": [MlStreamPublic.model_validate(r) for r in rows],
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
        },
    }


@router.get(
    "/ml-stream/{stream_id}",
    response_model=MlStreamDetail,
    summary="Get ML stream with full structure tree",
)
async def get_ml_stream(
    stream_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
) -> MlStreamDetail:
    row = await db.scalar(
        select(MlStream).where(
            MlStream.id == stream_id, MlStream.deleted_at.is_(None)
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stream not found")
    return MlStreamDetail.model_validate(row)


@router.post(
    "/ml-stream",
    response_model=MlStreamDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create ML stream (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def create_ml_stream(
    payload: MlStreamCreate, db: AsyncSession = Depends(get_db)
) -> MlStreamDetail:
    clash = await db.scalar(
        select(MlStream).where(
            MlStream.kode == payload.kode, MlStream.deleted_at.is_(None)
        )
    )
    if clash:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "ml_stream.kode already exists"
        )
    row = MlStream(
        kode=payload.kode,
        nama=payload.nama,
        version=payload.version,
        structure=payload.structure or {},
    )
    db.add(row)
    await db.flush()
    await db.commit()
    return MlStreamDetail.model_validate(row)


@router.patch(
    "/ml-stream/{stream_id}",
    response_model=MlStreamDetail,
    summary="Update ML stream (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def update_ml_stream(
    stream_id: uuid.UUID,
    payload: MlStreamUpdate,
    db: AsyncSession = Depends(get_db),
) -> MlStreamDetail:
    row = await db.scalar(
        select(MlStream).where(
            MlStream.id == stream_id, MlStream.deleted_at.is_(None)
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stream not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    await db.flush()
    await db.commit()
    return MlStreamDetail.model_validate(row)


@router.delete(
    "/ml-stream/{stream_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete ML stream (super_admin|admin_unit + CSRF)",
    dependencies=[
        Depends(require_role("super_admin", "admin_unit")),
        Depends(require_csrf),
    ],
)
async def delete_ml_stream(
    stream_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> None:
    row = await db.scalar(
        select(MlStream).where(
            MlStream.id == stream_id, MlStream.deleted_at.is_(None)
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stream not found")
    row.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await db.commit()
    return None
