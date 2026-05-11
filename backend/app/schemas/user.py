"""Public User DTOs (Pydantic v2).

`UserPublic` is the response shape returned by `POST /auth/login` (nested
under `user`) and `GET /auth/me`. Roles are flattened to a list of names so
the frontend `Role` union (Plan 07) matches the backend identifiers verbatim
(B-01/B-02: super_admin, admin_unit, pic_bidang, asesor, manajer_unit,
viewer).

The `_flatten_roles` validator accepts SQLAlchemy `User` instances as input
(the relationship `User.roles` returns a list of `Role` ORM objects) and
extracts `r.name` from each. It also tolerates the `bidang_id` attribute
being absent on the ORM instance — pre-Plan-06 the User model has no such
column, so `getattr(v, "bidang_id", None)` is the safe form.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    bidang_id: UUID | None = None
    roles: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def _flatten_roles(cls, v):
        """Accept a SQLAlchemy `User` instance and flatten `roles` to names.

        - When `v` is a SQLAlchemy User: extract `r.name` for each `r` in
          `v.roles`; read `bidang_id` via getattr (None pre-Plan-06).
        - When `v` is already a dict: pass through untouched.
        - When `v` is a Pydantic model instance: pass through; Pydantic v2
          will use model_dump when needed.
        """
        if isinstance(v, dict):
            return v
        if hasattr(v, "roles"):
            return {
                "id": v.id,
                "email": v.email,
                "full_name": v.full_name,
                "is_active": v.is_active,
                "bidang_id": getattr(v, "bidang_id", None),
                "roles": [r.name for r in (getattr(v, "roles") or [])],
            }
        return v
