"""Pydantic v2 DTOs for master-data routes (Plan 06).

Conventions:

- All `link_eviden` fields are typed ``HttpUrl`` so the OpenAPI components
  schema renders ``format: uri`` — the no-upload contract test in
  ``backend/tests/test_no_upload_policy.py`` walks the OpenAPI surface and
  rejects any other declaration of this field (CONSTR-no-file-upload,
  DEC-010).
- ``bobot`` fields use ``Decimal`` with ``decimal_places=2`` /
  ``max_digits=6`` for perspektif/indikator (range 0.00–999.99 is plenty;
  Konkin 2026 caps perspektif bobot at 46.00).
- ``polaritas`` is a ``Literal["positif","negatif","range"]`` so the OpenAPI
  emits an enum and the validator rejects mistypes at the edge — Phase 3
  NKO calc keys on this string verbatim.
- W-07 fix: ``PerspektifPublic`` exposes ``is_pengurang`` (bool) and
  ``pengurang_cap`` (Decimal | None) so the frontend can label perspektif VI
  visually as a pengurang and surface its cap.
- All `_Public` DTOs are `from_attributes=True` so they accept SQLAlchemy
  ORM instances directly via ``Model.model_validate(row)``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ---------------------------------------------------------------------------
# bidang
# ---------------------------------------------------------------------------


class BidangPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kode: str
    nama: str
    parent_id: UUID | None = None


class BidangCreate(BaseModel):
    kode: str = Field(min_length=1, max_length=32)
    nama: str = Field(min_length=1, max_length=255)
    parent_id: UUID | None = None


class BidangUpdate(BaseModel):
    """All fields optional — PATCH semantics."""

    kode: str | None = Field(default=None, min_length=1, max_length=32)
    nama: str | None = Field(default=None, min_length=1, max_length=255)
    parent_id: UUID | None = None


# ---------------------------------------------------------------------------
# konkin template
# ---------------------------------------------------------------------------


class TemplatePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tahun: int
    nama: str
    locked: bool


class TemplateCreate(BaseModel):
    tahun: int = Field(ge=2000, le=2100)
    nama: str = Field(min_length=1, max_length=255)
    # When set, the router deep-copies the source template's perspektif +
    # indikator chain (verbatim is_pengurang/pengurang_cap on perspektif).
    clone_from_id: UUID | None = None


class TemplateUpdate(BaseModel):
    tahun: int | None = Field(default=None, ge=2000, le=2100)
    nama: str | None = Field(default=None, min_length=1, max_length=255)


# ---------------------------------------------------------------------------
# perspektif (W-07: is_pengurang + pengurang_cap on Public)
# ---------------------------------------------------------------------------


class PerspektifPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_id: UUID
    kode: str
    nama: str
    bobot: Decimal
    # W-07: exposed so the frontend can label VI as "pengurang" and surface
    # its cap. Lock validator uses these fields server-side.
    is_pengurang: bool
    pengurang_cap: Decimal | None = None
    sort_order: int


class PerspektifCreate(BaseModel):
    kode: str = Field(min_length=1, max_length=8)
    nama: str = Field(min_length=1, max_length=255)
    bobot: Decimal = Field(ge=0, le=999.99, max_digits=6, decimal_places=2)
    is_pengurang: bool = False
    pengurang_cap: Decimal | None = Field(
        default=None, ge=0, le=999.99, max_digits=5, decimal_places=2
    )
    sort_order: int = 0


class PerspektifUpdate(BaseModel):
    kode: str | None = Field(default=None, min_length=1, max_length=8)
    nama: str | None = Field(default=None, min_length=1, max_length=255)
    bobot: Decimal | None = Field(
        default=None, ge=0, le=999.99, max_digits=6, decimal_places=2
    )
    is_pengurang: bool | None = None
    pengurang_cap: Decimal | None = Field(
        default=None, ge=0, le=999.99, max_digits=5, decimal_places=2
    )
    sort_order: int | None = None


# ---------------------------------------------------------------------------
# indikator (link_eviden is HttpUrl — guards CONSTR-no-file-upload)
# ---------------------------------------------------------------------------

# Literal type re-exported here for downstream consumers.
PolaritasT = Literal["positif", "negatif", "range"]


class IndikatorPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    perspektif_id: UUID
    kode: str
    nama: str
    bobot: Decimal
    polaritas: PolaritasT
    formula: str | None = None
    # HttpUrl so the OpenAPI schema renders format=uri and the contract test
    # in test_no_upload_policy.py is satisfied. Stored as str in DB.
    link_eviden: HttpUrl | None = None


class IndikatorCreate(BaseModel):
    kode: str = Field(min_length=1, max_length=32)
    nama: str = Field(min_length=1, max_length=255)
    bobot: Decimal = Field(ge=0, le=999.99, max_digits=6, decimal_places=2)
    polaritas: PolaritasT
    formula: str | None = Field(default=None, max_length=255)
    link_eviden: HttpUrl | None = None


class IndikatorUpdate(BaseModel):
    kode: str | None = Field(default=None, min_length=1, max_length=32)
    nama: str | None = Field(default=None, min_length=1, max_length=255)
    bobot: Decimal | None = Field(
        default=None, ge=0, le=999.99, max_digits=6, decimal_places=2
    )
    polaritas: PolaritasT | None = None
    formula: str | None = Field(default=None, max_length=255)
    link_eviden: HttpUrl | None = None


# ---------------------------------------------------------------------------
# ml_stream (JSONB structure tree — Phase 1: any dict)
# ---------------------------------------------------------------------------


class MlStreamPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kode: str
    nama: str
    version: str


class MlStreamDetail(MlStreamPublic):
    """Adds the full JSONB rubric tree to the public projection."""

    structure: dict


class MlStreamCreate(BaseModel):
    kode: str = Field(min_length=1, max_length=32)
    nama: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=16)
    structure: dict = Field(default_factory=dict)


class MlStreamUpdate(BaseModel):
    kode: str | None = Field(default=None, min_length=1, max_length=32)
    nama: str | None = Field(default=None, min_length=1, max_length=255)
    version: str | None = Field(default=None, min_length=1, max_length=16)
    structure: dict | None = None
