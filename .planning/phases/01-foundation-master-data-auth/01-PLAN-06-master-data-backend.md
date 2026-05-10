---
phase: 01-foundation-master-data-auth
plan: 06
type: execute
wave: 4
depends_on: [03, 05]
files_modified:
  - backend/app/models/bidang.py
  - backend/app/models/konkin_template.py
  - backend/app/models/perspektif.py
  - backend/app/models/indikator.py
  - backend/app/models/ml_stream.py
  - backend/app/models/konkin_import_log.py
  - backend/app/models/user.py
  - backend/app/schemas/master.py
  - backend/app/routers/master_bidang.py
  - backend/app/routers/master_konkin.py
  - backend/app/services/excel_import.py
  - backend/alembic/versions/20260512_140000_0003_master_data.py
  - backend/tests/test_bidang.py
  - backend/tests/test_master_konkin.py
  - backend/tests/test_ml_stream.py
  - backend/tests/test_no_upload_policy.py
autonomous: true
requirements:
  - REQ-bidang-master
  - REQ-konkin-template-crud
  - REQ-dynamic-ml-schema
  - REQ-route-guards
  - REQ-no-evidence-upload
must_haves:
  truths:
    - "Five master-data tables exist with UUID PKs, audit columns, soft delete: `bidang`, `konkin_template`, `perspektif`, `indikator`, `ml_stream` (CONSTR-data-model-core-tables); plus `konkin_import_log` for idempotent imports"
    - "`ml_stream.structure` is JSONB with a GIN index `idx_ml_stream_structure` (REQ-dynamic-ml-schema acceptance)"
    - "**B-04 fix:** `users.bidang_id UUID NULL` column + FK `users.bidang_id → bidang(id) ON DELETE SET NULL` are added IN THIS migration (after `bidang` is created), and the `User` model file is amended to declare the field. Plan 05's 0002 migration does NOT touch this column."
    - "**W-07 fix:** `perspektif` table has `is_pengurang BOOLEAN NOT NULL DEFAULT FALSE` and `pengurang_cap NUMERIC(5,2) NULL`. Lock validator filters: `SUM(bobot) WHERE is_pengurang = FALSE` MUST equal 100.00 ± 0.01. Indikator bobots within each perspektif still sum to 100% per REQ-konkin-template-crud."
    - "RBAC uses spec role names (B-01/B-02): `/master/*` write requires `super_admin` or `admin_unit`; `pic_bidang` reads scoped to own `bidang_id`; `asesor` and `manajer_unit` and `viewer` get read-all (no master CRUD); unauth = 401"
    - "`POST /konkin/templates` accepts `clone_from_id` for deep copy"
    - "`POST /konkin/templates/{id}/lock` makes the template immutable (rejects any further mutation)"
    - "**B-07 fix:** `POST /konkin/templates/{id}/import-from-excel` is admin-only (super_admin or admin_unit) AND requires `Depends(require_csrf)` — same CSRF rule as every other cookie-reachable mutating route. The misleading 'Bearer auth assumed' comment is removed."
    - "Multipart contract test now asserts EXACTLY ONE multipart endpoint = `/api/v1/konkin/templates/{template_id}/import-from-excel`"
    - "`link_eviden` fields validate as `HttpUrl` (Pydantic `format=uri`) — caught by the no-upload contract test"
  artifacts:
    - path: "backend/app/models/perspektif.py"
      provides: "Perspektif model with bobot + is_pengurang + pengurang_cap (W-07 fix)"
      contains: "is_pengurang"
    - path: "backend/app/models/ml_stream.py"
      provides: "ml_stream model with JSONB structure column + GIN index"
      contains: "JSONB"
    - path: "backend/app/routers/master_konkin.py"
      provides: "Konkin template / perspektif / indikator / ml_stream CRUD + lock + Excel import"
      contains: "import-from-excel"
    - path: "backend/app/services/excel_import.py"
      provides: "openpyxl streaming + per-sheet SAVEPOINT + Idempotency-Key handling"
      contains: "read_only=True"
    - path: "backend/app/models/konkin_import_log.py"
      provides: "Idempotency log for Excel imports (CONTEXT.md Data Model)"
      contains: "idempotency_key"
    - path: "backend/alembic/versions/20260512_140000_0003_master_data.py"
      provides: "Creates master tables + perspektif.is_pengurang/pengurang_cap (W-07) + adds users.bidang_id FK (B-04)"
      contains: "fk_users_bidang_id"
    - path: "backend/app/models/user.py"
      provides: "Amended to declare bidang_id field after Plan 05 (B-04)"
      contains: "bidang_id"
    - path: "backend/tests/test_no_upload_policy.py"
      provides: "Updated allow-list = {/api/v1/konkin/templates/{template_id}/import-from-excel}"
      contains: "import-from-excel"
  key_links:
    - from: "backend/app/routers/master_konkin.py"
      to: "backend/app/deps/auth.py"
      via: "Depends(require_role(\"super_admin\", \"admin_unit\"))"
      pattern: "require_role"
    - from: "backend/app/routers/master_konkin.py"
      to: "backend/app/deps/csrf.py"
      via: "Depends(require_csrf) on import-from-excel (B-07)"
      pattern: "require_csrf"
    - from: "backend/app/routers/master_konkin.py"
      to: "backend/app/services/excel_import.py"
      via: "service call"
      pattern: "excel_import"
    - from: "backend/alembic/versions/20260512_140000_0003_master_data.py"
      to: "backend/alembic/versions/20260512_100000_0002_auth_users_roles.py"
      via: "down_revision chain"
      pattern: "down_revision.*0002_auth_users_roles"
---

## Revision History

- **Iteration 1 (initial):** Five master tables, JSONB GIN, admin-gated CRUD, deep clone, lock with bobot validator, single multipart endpoint, idempotent excel import. Wave 3, parallel with Plan 05.
- **Iteration 2 (this revision):**
  - **W-04 fix (Option A — sequential):** `wave` changed from 3 to **4**. `depends_on` keeps `[05]` so this plan runs strictly after Plan 05. Alembic chain stays linear (0001 → 0002 → 0003) and a single `alembic upgrade head` integration step (Plan 07) applies all three.
  - **B-04 fix:** `users.bidang_id UUID NULL` column + `fk_users_bidang_id` FK to `bidang(id)` ON DELETE SET NULL are added in THIS migration (after `bidang` table exists). The `User` model file (`backend/app/models/user.py`) is amended in Task 1 of this plan to add the corresponding `Mapped[uuid.UUID | None]` field. Plan 05's 0002 migration does NOT touch `bidang_id`.
  - **W-07 fix:** `perspektif` table gets two new columns:
      - `is_pengurang BOOLEAN NOT NULL DEFAULT FALSE`
      - `pengurang_cap NUMERIC(5,2) NULL`
    Lock validator filters: `SUM(bobot) WHERE is_pengurang = FALSE` must equal 100.00 ± 0.01. Indikator bobots within each perspektif still sum to 100% (unchanged). Phase-3 NKO calculator subtracts `pengurang_cap` (max -10 for VI) from gross NKO. Plan 07 seed sets perspektif VI as `is_pengurang=True, bobot=0.00, pengurang_cap=10.00`.
  - **B-07 fix:** `POST /konkin/templates/{id}/import-from-excel` now adds `Depends(require_csrf)` to its dependencies list. The misleading 'Bearer auth assumed' comment is removed; the frontend uses cookie auth with `withCredentials: true` and echoes the CSRF token via the `X-CSRF-Token` header (existing pattern, see Plan 04 api.ts and Plan 07 axios request interceptor).
  - **B-01 + B-02 fix:** All `require_role(...)` calls switched to spec names: `require_role("super_admin", "admin_unit")` for write routes, `require_role("pic_bidang")` where read-scoping applies. Tests use spec names verbatim.
  - **B-06 fix:** `<automated>` blocks now run real `pytest` (not `ast.parse`) inside the running `pulse-backend` container with a `docker info` preflight. Host-side import smoke is the fallback when the stack isn't up.

<objective>
Implement the five master-data domain tables (bidang, konkin_template, perspektif, indikator, ml_stream) with UUID PKs, audit cols, soft delete, and the JSONB+GIN index on `ml_stream.structure` — plus admin-gated CRUD, deep-clone, lock (with W-07 pengurang-aware bobot validator), and the single locked multipart endpoint for Excel template bootstrap (B-07: CSRF-protected). This migration also adds the deferred `users.bidang_id` column + FK (B-04 fix). Update the no-upload contract test to lock in EXACTLY ONE multipart endpoint.

Purpose: REQ-bidang-master + REQ-konkin-template-crud + REQ-dynamic-ml-schema + REQ-route-guards (backend) + REQ-no-evidence-upload (final form). Plan 07 (Wave 5) consumes these endpoints and runs the seed module.

**Wave 4 — sequential** (W-04 Option A) after Plan 05 (Wave 3). The sequential ordering also resolves B-04 (FK on `users.bidang_id` cannot exist before the `bidang` table is created in this migration).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/01-foundation-master-data-auth/01-CONTEXT.md
@.planning/phases/01-foundation-master-data-auth/01-RESEARCH.md
@.planning/phases/01-foundation-master-data-auth/01-03-SUMMARY.md
@.planning/phases/01-foundation-master-data-auth/01-05-SUMMARY.md

<!-- Source-doc references for data-model details (read selectively) -->
@01_DOMAIN_MODEL.md
@03_DATA_MODEL.md

<interfaces>
<!-- From Plan 03 / Plan 05 (already in place) -->
- app.db.base.Base (auto-imports new model modules)
- app.deps.db.get_db, app.deps.auth.current_user, app.deps.auth.require_role
- app.deps.csrf.require_csrf  (cookie-mode CSRF defense)
- backend/tests/conftest.py: client + db_session + (Plan 05) admin_unit_user, pic_user, manajer_user

<!-- Exposed seams Plan 07 (frontend browse + seed) consumes -->

# Bidang
GET    /api/v1/bidang                       -> 200 {data: [BidangPublic], meta}
GET    /api/v1/bidang/{id}                  -> 200 BidangPublic | 404
POST   /api/v1/bidang        (super_admin|admin_unit + CSRF)        -> 201 BidangPublic
PATCH  /api/v1/bidang/{id}   (super_admin|admin_unit + CSRF)        -> 200 BidangPublic
DELETE /api/v1/bidang/{id}   (super_admin|admin_unit + CSRF)        -> 204  (soft delete)

# Konkin templates  (all writes: super_admin|admin_unit + CSRF)
GET    /api/v1/konkin/templates                       -> 200 {data: [TemplatePublic], meta}
GET    /api/v1/konkin/templates/{id}                  -> 200 TemplateDetail
POST   /api/v1/konkin/templates                        body {tahun, clone_from_id?: UUID} -> 201
PATCH  /api/v1/konkin/templates/{id}                   -> 200; rejects if locked
POST   /api/v1/konkin/templates/{id}/lock              -> 200; validates bobot sums (W-07)
POST   /api/v1/konkin/templates/{id}/import-from-excel (multipart, admin + CSRF — B-07)  -> 201|200 (idempotent)

# Perspektif (nested under template)
GET/POST/PATCH/DELETE under /api/v1/konkin/templates/{template_id}/perspektif[/{id}]

# Indikator
GET/POST/PATCH/DELETE under /api/v1/konkin/perspektif/{perspektif_id}/indikator[/{id}]

# ML Stream
GET    /api/v1/ml-stream                  -> 200 {data:[MlStreamPublic], meta}
GET    /api/v1/ml-stream/{id}             -> 200 MlStreamDetail (with full JSONB tree)
POST   /api/v1/ml-stream      (super_admin|admin_unit + CSRF)
PATCH  /api/v1/ml-stream/{id} (super_admin|admin_unit + CSRF)
DELETE /api/v1/ml-stream/{id} (super_admin|admin_unit + CSRF)

<!-- Schema sketches -->
class BidangPublic(BaseModel): id: UUID; kode: str; nama: str; parent_id: UUID|None
class TemplatePublic(BaseModel): id: UUID; tahun: int; nama: str; locked: bool; created_at: datetime
class PerspektifPublic(BaseModel): id: UUID; kode: str; nama: str; bobot: Decimal; is_pengurang: bool; pengurang_cap: Decimal | None
class IndikatorPublic(BaseModel): id: UUID; kode: str; nama: str; bobot: Decimal; polaritas: Literal["positif","negatif","range"]; link_eviden: HttpUrl | None
class MlStreamPublic(BaseModel): id: UUID; kode: str; nama: str; version: str
class MlStreamDetail(MlStreamPublic): structure: dict   # the JSONB tree
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Models (with W-07 perspektif columns) + Alembic 0003 (creates master tables AND adds users.bidang_id FK per B-04) + amend User model</name>
  <files>
    backend/app/models/bidang.py,
    backend/app/models/konkin_template.py,
    backend/app/models/perspektif.py,
    backend/app/models/indikator.py,
    backend/app/models/ml_stream.py,
    backend/app/models/konkin_import_log.py,
    backend/app/models/user.py,
    backend/alembic/versions/20260512_140000_0003_master_data.py
  </files>
  <action>
    Every model: UUID PK (`server_default=text("uuid_generate_v4()")`), audit cols `created_at, updated_at, created_by, updated_by` (created_by/updated_by are UUID nullable FKs to users.id with no cascade), and (for critical entities) `deleted_at` soft-delete column. All identifiers per `03_DATA_MODEL.md`.

    1. `bidang.py`:
       ```python
       class Bidang(Base):
           __tablename__ = "bidang"
           id: ... PK uuid
           kode: Mapped[str] = mapped_column(String(32), unique=True)
           nama: Mapped[str] = mapped_column(String(255))
           parent_id: Mapped[UUID|None] = mapped_column(ForeignKey("bidang.id", ondelete="SET NULL"))
           # audit + deleted_at
       ```

    2. `konkin_template.py`:
       ```python
       class KonkinTemplate(Base):
           __tablename__ = "konkin_template"
           id: ... PK
           tahun: Mapped[int]
           nama: Mapped[str]
           locked: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
           # audit + deleted_at
           # uniqueness (tahun, nama)
       ```

    3. `perspektif.py` — **W-07 fix: `is_pengurang` + `pengurang_cap` columns**:
       ```python
       from decimal import Decimal
       from sqlalchemy import Numeric, Boolean
       class Perspektif(Base):
           __tablename__ = "perspektif"
           id: ... PK
           template_id: FK konkin_template ON DELETE CASCADE
           kode: Mapped[str] = mapped_column(String(4))         # I, II, III, IV, V, VI
           nama: Mapped[str]
           bobot: Mapped[Decimal] = mapped_column(Numeric(6,2))
           # W-07: pengurang convention. Stored as bobot=0.00 + is_pengurang=True for perspektif VI.
           # Lock validator filters by is_pengurang=False; Phase-3 NKO calc subtracts pengurang_cap from gross.
           is_pengurang: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
           pengurang_cap: Mapped[Decimal | None] = mapped_column(Numeric(5,2), nullable=True)
           sort_order: Mapped[int] = mapped_column(server_default=text("0"))
           # audit
           # unique (template_id, kode)
       ```

    4. `indikator.py`:
       ```python
       class Indikator(Base):
           __tablename__ = "indikator"
           id: ... PK
           perspektif_id: FK perspektif ON DELETE CASCADE
           kode: Mapped[str]
           nama: Mapped[str]
           bobot: Mapped[Decimal] = mapped_column(Numeric(6,2))
           polaritas: Mapped[str] = mapped_column(String(16))
           formula: Mapped[str | None] = mapped_column(String(255))
           link_eviden: Mapped[str | None] = mapped_column(String(2048))
           # audit + deleted_at
           # unique (perspektif_id, kode)
       ```

    5. `ml_stream.py`:
       ```python
       class MlStream(Base):
           __tablename__ = "ml_stream"
           id: ... PK
           kode: Mapped[str] = mapped_column(String(32), unique=True)
           nama: Mapped[str]
           version: Mapped[str] = mapped_column(String(16))
           structure: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
           # audit + deleted_at
       ```

    6. `konkin_import_log.py`:
       ```python
       class KonkinImportLog(Base):
           __tablename__ = "konkin_import_log"
           id: ... PK
           template_id: FK konkin_template
           idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
           imported_at: Mapped[datetime]
           summary: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
           imported_by: FK users.id
       ```

    7. **Amend `backend/app/models/user.py` (B-04):** add the `bidang_id` Mapped column after Plan 05's user model is in place. Add this single field declaration:
       ```python
       # B-04: bidang_id is added here AFTER bidang table is created in Plan 06's migration.
       # Plan 05's 0002 migration intentionally did NOT create this column.
       from sqlalchemy import ForeignKey
       # Inside class User:
       bidang_id: Mapped[uuid.UUID | None] = mapped_column(
           UUID(as_uuid=True),
           ForeignKey("bidang.id", ondelete="SET NULL"),
           nullable=True,
       )
       ```
       Use a code-edit (insert after the `is_active` column declaration). The model file's import block must already include `ForeignKey` and `UUID` (it does from Plan 05).

    8. `backend/alembic/versions/20260512_140000_0003_master_data.py` — header:
       ```python
       """master data: bidang, konkin_template, perspektif (with is_pengurang + pengurang_cap — W-07),
       indikator, ml_stream, konkin_import_log; AND users.bidang_id column + FK (B-04 fix).

       Revision ID: 0003_master_data
       Revises: 0002_auth_users_roles
       Create Date: 2026-05-12 14:00:00
       """
       ```

       `upgrade()` operations (in order):
       a) Create `bidang` (parent_id self-FK ON DELETE SET NULL).
       b) Create `konkin_template` (unique (tahun, nama)).
       c) Create `perspektif` with **`is_pengurang BOOLEAN NOT NULL DEFAULT FALSE`** and **`pengurang_cap NUMERIC(5,2) NULL`** (W-07).
       d) Create `indikator` (FK perspektif CASCADE).
       e) Create `ml_stream` (JSONB structure column with server_default empty object).
       f) Create `konkin_import_log` (FK template + FK users; unique idempotency_key).
       g) `op.execute("CREATE INDEX idx_ml_stream_structure ON ml_stream USING GIN (structure)")`.
       h) **B-04**: `op.add_column("users", sa.Column("bidang_id", UUID(as_uuid=True), nullable=True))` then `op.create_foreign_key("fk_users_bidang_id", "users", "bidang", ["bidang_id"], ["id"], ondelete="SET NULL")`.

       `downgrade()`:
       a) `op.drop_constraint("fk_users_bidang_id", "users", type_="foreignkey")`.
       b) `op.drop_column("users", "bidang_id")`.
       c) Drop the GIN index.
       d) Drop the six tables (children first).
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $models = 'bidang','konkin_template','perspektif','indikator','ml_stream','konkin_import_log';
        foreach ($m in $models) {
          if (-not (Test-Path ('backend/app/models/' + $m + '.py'))) { Write-Output ('missing model: ' + $m); exit 1 }
        };
        # W-07: perspektif must have is_pengurang and pengurang_cap
        $persp = Get-Content 'backend/app/models/perspektif.py' -Raw;
        if ($persp -notmatch 'is_pengurang') { Write-Output 'W-07: missing is_pengurang on perspektif'; exit 2 };
        if ($persp -notmatch 'pengurang_cap') { exit 3 };
        $ml = Get-Content 'backend/app/models/ml_stream.py' -Raw;
        if ($ml -notmatch 'JSONB') { exit 4 };
        $ind = Get-Content 'backend/app/models/indikator.py' -Raw;
        if ($ind -notmatch 'polaritas') { exit 5 };
        if ($ind -notmatch 'link_eviden') { exit 6 };
        # B-04: amended User model must declare bidang_id
        $u = Get-Content 'backend/app/models/user.py' -Raw;
        if ($u -notmatch 'bidang_id') { Write-Output 'B-04: User model not amended with bidang_id'; exit 7 };
        # Migration content
        $mig = Get-Content 'backend/alembic/versions/20260512_140000_0003_master_data.py' -Raw;
        if ($mig -notmatch 'idx_ml_stream_structure') { exit 8 };
        if ($mig -notmatch 'USING GIN') { exit 9 };
        if ($mig -notmatch 'fk_users_bidang_id') { Write-Output 'B-04: 0003 must add fk_users_bidang_id'; exit 10 };
        if ($mig -notmatch 'add_column.+users.+bidang_id') { Write-Output 'B-04: 0003 must add_column users.bidang_id'; exit 11 };
        if ($mig -notmatch 'is_pengurang')  { Write-Output 'W-07: 0003 must declare is_pengurang on perspektif'; exit 12 };
        if ($mig -notmatch 'pengurang_cap') { exit 13 };
        if ($mig -notmatch 'down_revision\\s*=\\s*\"0002_auth_users_roles\"') { exit 14 };
        # B-06: real Python import (not ast.parse)
        Push-Location backend
        python -c 'from sqlalchemy import inspect; from app.models.user import User; from app.models.bidang import Bidang; from app.models.konkin_template import KonkinTemplate; from app.models.perspektif import Perspektif; from app.models.indikator import Indikator; from app.models.ml_stream import MlStream; from app.models.konkin_import_log import KonkinImportLog; cols = {c.name for c in inspect(User).columns}; assert \"bidang_id\" in cols, \"B-04: User model must now have bidang_id\"; pcols = {c.name for c in inspect(Perspektif).columns}; assert \"is_pengurang\" in pcols and \"pengurang_cap\" in pcols, \"W-07: perspektif must have is_pengurang + pengurang_cap\"; print(\"models OK; bidang_id present; is_pengurang+pengurang_cap present\")' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 15 };
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Six model files exist; perspektif has is_pengurang + pengurang_cap (W-07); User model amended with bidang_id (B-04); Alembic 0003 creates the master tables AND adds users.bidang_id + fk_users_bidang_id; revision chain 0001→0002→0003 intact.
  </done>
</task>

<task type="auto">
  <name>Task 2: Pydantic schemas + Bidang router + Master Konkin CRUD/lock router (W-07 lock validator + spec role names)</name>
  <files>
    backend/app/schemas/master.py,
    backend/app/routers/master_bidang.py,
    backend/app/routers/master_konkin.py
  </files>
  <action>
    1. `backend/app/schemas/master.py` — full Pydantic v2 DTOs per `<interfaces>`. Every `link_eviden` field uses `Pydantic.HttpUrl` (renders `format: uri`). Use `Decimal` for `bobot` with `decimal_places=2, max_digits=6`. Validators:
       - `IndikatorCreate.polaritas`: `Literal["positif","negatif","range"]`.
       - `PerspektifPublic`: includes `is_pengurang: bool` and `pengurang_cap: Decimal | None` (W-07 fix).
       - `MlStreamCreate.structure` is `dict` typed as the nested area tree — Phase 1 accepts any dict; Phase 2/6 tightens.

    2. `backend/app/routers/master_bidang.py` — gates use spec role names (B-01/B-02):
       ```python
       from fastapi import APIRouter, Depends, HTTPException, status, Query
       from sqlalchemy import select, func
       from sqlalchemy.ext.asyncio import AsyncSession
       from app.deps.db import get_db
       from app.deps.auth import current_user, require_role
       from app.deps.csrf import require_csrf
       from app.models.bidang import Bidang
       from app.models.user import User
       from app.schemas.master import BidangPublic, BidangCreate, BidangUpdate

       router = APIRouter(prefix="/bidang", tags=["master-bidang"])

       @router.get("", response_model=dict)
       async def list_bidang(
           db: AsyncSession = Depends(get_db),
           user: User = Depends(current_user),
           page: int = Query(1, ge=1),
           page_size: int = Query(50, ge=1, le=200),
       ):
           q = select(Bidang).where(Bidang.deleted_at.is_(None))
           # pic_bidang: scope to own bidang_id (Phase 1: own bidang only; Phase 2 expands hierarchy)
           if any(r.name == "pic_bidang" for r in user.roles) and user.bidang_id:
               q = q.where(Bidang.id == user.bidang_id)
           total = await db.scalar(select(func.count()).select_from(q.subquery()))
           rows = (await db.scalars(q.offset((page-1)*page_size).limit(page_size).order_by(Bidang.kode))).all()
           return {"data": [BidangPublic.model_validate(r) for r in rows],
                   "meta": {"page": page, "page_size": page_size, "total": total}}

       # POST/PATCH/DELETE: dependencies=[Depends(require_role("super_admin","admin_unit")), Depends(require_csrf)]
       ```

    3. `backend/app/routers/master_konkin.py` — three nested routers under one file. Key business logic:
       - `POST /konkin/templates` with `clone_from_id`: open a transaction, INSERT template, then `INSERT ... SELECT` perspektif + indikator chains from the source template (deep copy, new UUIDs). The cloned `is_pengurang` + `pengurang_cap` carry over verbatim.
       - `POST /konkin/templates/{id}/lock` — **W-07 fix lock validator**:
         - SUM perspektif bobots **WHERE is_pengurang = FALSE**; reject 422 if not == 100.00 (within 0.01 tolerance). Return JSON detail showing the actual sum and the offending perspektif rows.
         - For each non-pengurang perspektif: SUM aggregate indikator bobots; reject 422 if not == 100.00.
         - Pengurang perspektif rows are excluded from the indikator-sum check too (their indikator are computed differently per Phase-3 NKO calc).
         - On pass: `UPDATE konkin_template SET locked=true`.
       - All mutations check `template.locked == False` first; raise 409 if locked.
       - **B-07 fix**: `POST /konkin/templates/{id}/import-from-excel` dependencies are `[Depends(require_role("super_admin","admin_unit")), Depends(require_csrf)]`. Remove any "Bearer auth assumed" comment from earlier draft.
       - Every other mutating route: `dependencies=[Depends(require_role("super_admin","admin_unit")), Depends(require_csrf)]`. Read routes: `Depends(current_user)` (401 if no token).
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $b = Get-Content 'backend/app/routers/master_bidang.py' -Raw;
        if ($b -notmatch 'require_role\\(\"super_admin\",\\s*\"admin_unit\"\\)') { Write-Output 'B-01/B-02: bidang router must use spec role names'; exit 1 };
        if ($b -notmatch 'pic_bidang') { exit 2 };
        if ($b -notmatch 'page_size') { exit 3 };
        if ($b -notmatch 'deleted_at') { exit 4 };
        $k = Get-Content 'backend/app/routers/master_konkin.py' -Raw;
        if ($k -notmatch '/lock') { exit 5 };
        if ($k -notmatch 'clone_from_id') { exit 6 };
        # W-07: lock validator must filter by is_pengurang
        if ($k -notmatch 'is_pengurang' ) { Write-Output 'W-07: lock validator must reference is_pengurang'; exit 7 };
        # B-07: import-from-excel must use require_csrf
        # Look for the dependency list near import-from-excel; both names should appear in the file.
        if ($k -notmatch 'import-from-excel') { exit 8 };
        if ($k -notmatch 'require_csrf') { Write-Output 'B-07: import-from-excel must require CSRF'; exit 9 };
        # No misleading 'Bearer auth assumed' comment
        if ($k -match 'Bearer auth assumed') { Write-Output 'B-07: misleading comment must be removed'; exit 10 };
        $s = Get-Content 'backend/app/schemas/master.py' -Raw;
        if ($s -notmatch 'HttpUrl') { exit 11 };
        if ($s -notmatch 'polaritas') { exit 12 };
        if ($s -notmatch 'Literal\\[') { exit 13 };
        if ($s -notmatch 'is_pengurang') { Write-Output 'W-07: PerspektifPublic must expose is_pengurang'; exit 14 };
        # Real import smoke (B-06)
        Push-Location backend
        python -c 'from app.schemas.master import PerspektifPublic, IndikatorPublic, BidangPublic, TemplatePublic, MlStreamPublic; from app.routers.master_bidang import router as br; from app.routers.master_konkin import router as kr; print(\"routers OK\", br.prefix, kr.prefix)' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 15 };
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Schemas use HttpUrl + Literal + is_pengurang/pengurang_cap; bidang router applies pic_bidang scope and uses spec role names on writes; konkin router covers clone, lock with W-07-aware bobot validation, all CRUD; import-from-excel uses `require_csrf` (B-07); no "Bearer auth assumed" comment.
  </done>
</task>

<task type="auto">
  <name>Task 3: Excel import service (CSRF-protected route — B-07) + updated no-upload contract test + master-data tests (real pytest)</name>
  <files>
    backend/app/services/excel_import.py,
    backend/tests/test_no_upload_policy.py,
    backend/tests/test_bidang.py,
    backend/tests/test_master_konkin.py,
    backend/tests/test_ml_stream.py
  </files>
  <action>
    1. `backend/app/services/excel_import.py` — RESEARCH.md Code Examples + Pitfall #10 (streaming, SAVEPOINT per sheet, idempotency-key gate):
       ```python
       from io import BytesIO
       from uuid import UUID
       from openpyxl import load_workbook
       from sqlalchemy import select
       from sqlalchemy.ext.asyncio import AsyncSession
       from app.models.konkin_import_log import KonkinImportLog
       from app.models.konkin_template import KonkinTemplate

       ALLOWED_CT = {
           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
           "application/vnd.ms-excel",
       }

       async def import_workbook(
           db: AsyncSession,
           template: KonkinTemplate,
           raw: bytes,
           idempotency_key: str | None,
           imported_by: UUID,
       ) -> dict:
           if idempotency_key:
               existing = await db.scalar(select(KonkinImportLog).where(
                   KonkinImportLog.idempotency_key == idempotency_key))
               if existing:
                   return {"status": "already_applied", "log_id": str(existing.id), "summary": existing.summary}

           wb = load_workbook(BytesIO(raw), read_only=True, data_only=True)
           summary: dict[str, int] = {}
           for sheet in wb.sheetnames:
               async with db.begin_nested():
                   n = await _import_sheet(db, template, wb[sheet])
                   summary[sheet] = n
           if idempotency_key:
               db.add(KonkinImportLog(
                   template_id=template.id, idempotency_key=idempotency_key,
                   summary=summary, imported_by=imported_by,
               ))
           await db.commit()
           return {"status": "imported", "summary": summary}

       async def _import_sheet(db, template, sheet) -> int:
           # Phase 1 scope: accept perspektif + indikator rows from a single workbook.
           return 0
       ```

       Wire into `master_konkin.py`'s endpoint — **B-07 fix: CSRF dep present, comment removed**:
       ```python
       @router.post(
           "/templates/{template_id}/import-from-excel",
           status_code=201,
           dependencies=[
               Depends(require_role("super_admin", "admin_unit")),
               Depends(require_csrf),   # B-07: cookie-mode CSRF defense, same as every other mutating route
           ],
       )
       async def import_from_excel(
           template_id: UUID,
           file: UploadFile = File(...),
           idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
           db: AsyncSession = Depends(get_db),
           user: User = Depends(require_role("super_admin", "admin_unit")),
       ):
           if file.content_type not in ALLOWED_CT:
               raise HTTPException(415, "Only .xlsx accepted")
           template = await db.scalar(select(KonkinTemplate).where(KonkinTemplate.id == template_id))
           if not template:
               raise HTTPException(404, "Template not found")
           if template.locked:
               raise HTTPException(409, "Template is locked")
           raw = await file.read()
           result = await excel_import.import_workbook(db, template, raw, idempotency_key, user.id)
           status_code = 200 if result["status"] == "already_applied" else 201
           return JSONResponse(status_code=status_code, content={"data": result})
       ```

    2. `backend/tests/test_no_upload_policy.py` — REPLACE the empty allow-list with the locked single-endpoint allow-list:
       ```python
       ALLOWED_MULTIPART_PATHS: set[str] = {
           "/api/v1/konkin/templates/{template_id}/import-from-excel",
       }
       ```

    3. `backend/tests/test_bidang.py` — covers RBAC with spec role names. admin_unit and super_admin can CRUD; pic_bidang sees only own bidang; manajer_unit / asesor / viewer = 403 on writes; unauth = 401.

    4. `backend/tests/test_master_konkin.py` — covers REQ-konkin-template-crud:
       - admin_unit creates template, clones, locks.
       - **W-07 lock validator**: lock with non-pengurang perspektif sum != 100 returns 422 with detail showing the bad rows; lock SUCCEEDS when non-pengurang sum to 100 even if a pengurang perspektif (e.g. VI) has bobot=0. Add test:
         ```python
         @pytest.mark.asyncio
         async def test_lock_validator_excludes_pengurang(db_session, admin_unit_user):
             # Create template with five non-pengurang perspektif summing to 100 + one pengurang at bobot=0.
             # Expect /lock to return 200.
             ...
         ```
       - mutation against locked template returns 409.
       - pic_bidang cannot mutate (403); manajer_unit cannot mutate (403); viewer cannot mutate (403).
       - admin_unit Excel import: send a tiny in-memory xlsx; assert 201; second send with same `Idempotency-Key` returns 200 + `already_applied`. **B-07 contract**: a request without the `X-CSRF-Token` header (cookie auth path) returns 403.

    5. `backend/tests/test_ml_stream.py` — REQ-dynamic-ml-schema:
       ```python
       @pytest.mark.asyncio
       async def test_jsonb_query(db_session):
           from app.models.ml_stream import MlStream
           stream = MlStream(kode="OUTAGE", nama="Outage Management", version="2026.1",
                             structure={"areas": [{"code": "OM-1", "name": "Planning",
                                                   "sub_areas": [{"code": "OM-1-1", "uraian": "...",
                                                                  "criteria": {"level_0": "...", "level_4": "..."}}]}]})
           db_session.add(stream); await db_session.flush()
           from sqlalchemy import text
           rows = (await db_session.execute(text(
               "SELECT id FROM ml_stream WHERE structure @> '{\"areas\":[{\"code\":\"OM-1\"}]}'::jsonb"
           ))).scalars().all()
           assert stream.id in rows
       ```
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $e = Get-Content 'backend/app/services/excel_import.py' -Raw;
        if ($e -notmatch 'read_only=True')  { exit 1 };
        if ($e -notmatch 'begin_nested')    { exit 2 };
        if ($e -notmatch 'idempotency_key') { exit 3 };
        $tnu = Get-Content 'backend/tests/test_no_upload_policy.py' -Raw;
        if ($tnu -notmatch 'import-from-excel') { exit 4 };
        # B-07: master_konkin must have require_csrf in import-from-excel deps
        $k = Get-Content 'backend/app/routers/master_konkin.py' -Raw;
        if ($k -notmatch 'import-from-excel[\\s\\S]+require_csrf') { Write-Output 'B-07: require_csrf missing on import-from-excel'; exit 5 };
        # No misleading comment
        if ($k -match 'Bearer auth assumed') { exit 6 };
        $tk = Get-Content 'backend/tests/test_master_konkin.py' -Raw;
        if ($tk -notmatch 'clone_from_id') { exit 7 };
        if ($tk -notmatch 'locked') { exit 8 };
        if ($tk -notmatch 'already_applied') { exit 9 };
        # W-07 test presence
        if ($tk -notmatch 'pengurang') { Write-Output 'W-07: missing pengurang test'; exit 10 };
        # B-07 test presence
        if ($tk -notmatch 'X-CSRF-Token' -and $tk -notmatch 'csrf') { Write-Output 'B-07: missing csrf test on import-from-excel'; exit 11 };
        $tm = Get-Content 'backend/tests/test_ml_stream.py' -Raw;
        if ($tm -notmatch 'jsonb') { exit 12 };
        # B-06: real pytest if container is up; otherwise host-side import smoke + docker-info preflight
        docker info 1>$null 2>&1
        if ($LASTEXITCODE -ne 0) {
          Write-Output 'docker offline; falling back to import smoke';
          Push-Location backend
          python -c 'from app.services.excel_import import import_workbook; from tests import test_bidang, test_master_konkin, test_ml_stream, test_no_upload_policy; print(\"imports OK\")' 2>&1 | Out-String | Write-Output
          if ($LASTEXITCODE -ne 0) { Pop-Location; exit 13 };
          Pop-Location
          Write-Output 'pass (deferred)';
          exit 0
        };
        $running = docker compose ps --services --filter status=running 2>$null;
        if ($running -match 'pulse-backend') {
          docker compose exec -T pulse-backend pytest tests/test_bidang.py tests/test_master_konkin.py tests/test_ml_stream.py tests/test_no_upload_policy.py -x -q 2>&1 | Out-String | Write-Output
          if ($LASTEXITCODE -ne 0) { Write-Output 'pytest failed'; exit 14 };
        } else {
          Write-Output 'pulse-backend not running yet; deferred to Plan 07 e2e checkpoint';
          Push-Location backend
          python -c 'from app.services.excel_import import import_workbook; from tests import test_bidang, test_master_konkin, test_ml_stream, test_no_upload_policy; print(\"imports OK\")' 2>&1 | Out-String | Write-Output
          if ($LASTEXITCODE -ne 0) { Pop-Location; exit 15 };
          Pop-Location
        };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Excel import service uses streaming + savepoint + idempotency; no-upload allow-list is exactly `{/api/v1/konkin/templates/{template_id}/import-from-excel}`; link_eviden URI check passes; master-data test files cover CRUD with spec role names, RBAC across all six roles, lock with W-07 pengurang exclusion, clone, JSONB query, B-07 CSRF requirement on import-from-excel.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Untrusted multipart Excel upload | Admin-only endpoint behind require_role + require_csrf (B-07) |
| Untrusted JSON body for CRUD | Pydantic schemas + role gates |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-06-T-01 | Tampering | Mass assignment via JSON body | mitigate | Pydantic schemas declare exactly allowed fields; never bind raw request body to ORM model. |
| T-06-T-02 | Tampering | Path traversal via Excel filename | mitigate | excel_import reads from `BytesIO`, never writes uploaded bytes to disk. |
| T-06-T-03 | Tampering | Mutation against locked template | mitigate | Every mutating route checks `template.locked == False`; returns 409 on attempt. |
| T-06-T-04 | Tampering | CSRF on cookie-auth import-from-excel (B-07) | mitigate | `Depends(require_csrf)` on the import endpoint matches every other mutating route. |
| T-06-D-01 | DoS | Large Excel OOMs worker | mitigate | Nginx `client_max_body_size 25M` (Plan 02); openpyxl `read_only=True, data_only=True`; SAVEPOINT per sheet. |
| T-06-I-01 | Information disclosure | pic_bidang sees other bidang data | mitigate | `bidang` router applies `where(Bidang.id == user.bidang_id)`. Phase 2 expands hierarchy. |
| T-06-E-01 | Elevation | Non-admin role mutates master data | mitigate | All mutating routes carry `Depends(require_role("super_admin","admin_unit"))`; 403 otherwise. |
| T-06-E-02 | Elevation | New multipart endpoint sneaks in | mitigate | `test_no_upload_policy` asserts allow-list = exactly one path. |
</threat_model>

<verification>
- `alembic upgrade head` chains 0001 → 0002 → 0003 cleanly; `users` now has `bidang_id` + `fk_users_bidang_id` constraint (B-04)
- `pytest backend/tests/test_bidang.py backend/tests/test_master_konkin.py backend/tests/test_ml_stream.py backend/tests/test_no_upload_policy.py -x` passes inside `pulse-backend` (real exec — B-06)
- OpenAPI shows exactly one multipart endpoint (Plan 06's import-from-excel)
- Lock validator excludes pengurang rows (W-07)
- import-from-excel rejects no-CSRF cookie-auth requests (B-07)
- ml_stream JSONB `@>` query uses GIN index
</verification>

<success_criteria>
- Five master-data tables + import log table with UUID PKs, audit cols, GIN index on JSONB
- Spec-role RBAC enforced on every route (super_admin/admin_unit write, pic_bidang scoped read, others 403/401)
- Template lock validates non-pengurang bobot sums (W-07)
- Excel import is streaming + idempotent + admin-only + CSRF-protected (B-07)
- No-upload allow-list = exactly one endpoint
- `users.bidang_id` + FK live in 0003 (B-04); User model amended in this plan
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-master-data-auth/01-06-SUMMARY.md` listing:
1. Endpoint contract table (path, method, role gate, CSRF requirement, request/response shape)
2. **W-07 lock-validator details:** the SQL filter `WHERE is_pengurang = FALSE`, tolerance 0.01, indikator-sum scope (excluded for pengurang perspektif)
3. Excel import flow: idempotency-key behavior, content-type filter, savepoint strategy, **B-07 CSRF requirement**
4. Updated no-upload test allow-list (exactly one)
5. **B-04 audit:** post-migration `users` table column list including `bidang_id` and the FK constraint name
</output>
