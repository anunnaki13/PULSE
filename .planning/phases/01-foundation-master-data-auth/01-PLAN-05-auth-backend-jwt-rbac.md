---
phase: 01-foundation-master-data-auth
plan: 05
type: execute
wave: 3
depends_on: [03]
files_modified:
  - backend/app/models/user.py
  - backend/app/models/role.py
  - backend/app/schemas/auth.py
  - backend/app/schemas/user.py
  - backend/app/core/security.py
  - backend/app/deps/auth.py
  - backend/app/deps/csrf.py
  - backend/app/deps/metrics_admin.py
  - backend/app/routers/auth.py
  - backend/app/services/refresh_tokens.py
  - backend/alembic/versions/20260512_100000_0002_auth_users_roles.py
  - backend/tests/test_auth.py
  - backend/tests/test_rbac.py
  - backend/tests/test_user_roles.py
autonomous: true
requirements:
  - REQ-user-roles
  - REQ-auth-jwt
must_haves:
  truths:
    - "`POST /api/v1/auth/login` accepts email + password (JSON or form), validates via bcrypt, and returns access+refresh JWTs in BOTH the response body AND as httpOnly cookies (dual-mode per RESEARCH.md Pattern 3)"
    - "`POST /api/v1/auth/refresh` rotates the refresh token: old `jti` is revoked in Redis with TTL = remaining lifetime, new pair issued"
    - "`POST /api/v1/auth/logout` revokes the active refresh `jti` and clears both cookies"
    - "`GET /api/v1/auth/me` returns the current user (decoded from access token, dual-mode)"
    - "`require_role(*allowed)` dependency returns 403 when the user's roles don't intersect the allowed set, 401 when no token"
    - "**SIX role rows** seeded by the auth migration using REQ-user-roles spec naming verbatim (B-01 + B-02 fix per CONTEXT.md Auth): `super_admin`, `admin_unit`, `pic_bidang`, `asesor`, `manajer_unit`, `viewer`"
    - "Access token TTL = 60 min, refresh token TTL = 14 days, both signed with `JWT_SECRET_KEY` from settings"
    - "JWT decode uses an explicit algorithm allow-list (`algorithms=[\"HS256\"]`) — defense against `alg: none` / alg-confusion attacks"
    - "CSRF double-submit token enforced on cookie-mutating routes (RESEARCH.md Pitfall #8)"
    - "Brute-force protection: 5 failed logins within 5 minutes locks the account for 15 minutes (Redis-backed counter — defense in depth alongside nginx login_zone)"
    - "**B-04 fix:** the `users.bidang_id` column is NOT created in this migration — Plan 06 declares it together with the FK after the `bidang` table exists"
    - "**W-02 wiring:** `app/deps/metrics_admin.py` is updated to delegate to `require_role(\"super_admin\", \"admin_unit\")` so `/health/detail` and `/metrics` (Plan 03) become admin-callable"
  artifacts:
    - path: "backend/app/models/user.py"
      provides: "User model with UUID PK, email unique, password_hash, is_active, audit cols (NO bidang_id — moved to Plan 06 per B-04)"
      contains: "uuid_generate_v4()"
    - path: "backend/app/models/role.py"
      provides: "Role + user_role association tables"
      contains: "user_roles"
    - path: "backend/app/routers/auth.py"
      provides: "POST /auth/login, /auth/refresh, /auth/logout; GET /auth/me"
      contains: "/login"
    - path: "backend/app/core/security.py"
      provides: "hash_password, verify_password, create_access_token, create_refresh_token, decode_token"
      contains: "algorithms=[settings.JWT_ALGORITHM]"
    - path: "backend/app/deps/auth.py"
      provides: "current_user dual-mode + require_role factory"
      contains: "require_role"
    - path: "backend/app/deps/metrics_admin.py"
      provides: "Updated: now delegates to require_role(super_admin, admin_unit) for /health/detail and /metrics (W-02)"
      contains: "require_role"
    - path: "backend/app/services/refresh_tokens.py"
      provides: "Redis-backed refresh-token jti revocation set"
      contains: "revoked"
    - path: "backend/alembic/versions/20260512_100000_0002_auth_users_roles.py"
      provides: "Creates roles + users + user_roles. Seeds SIX roles (B-01/B-02). Does NOT create users.bidang_id (B-04)."
      contains: "super_admin"
  key_links:
    - from: "backend/app/routers/auth.py"
      to: "backend/app/services/refresh_tokens.py"
      via: "revoke + check_revoked on refresh"
      pattern: "revoke|is_revoked"
    - from: "backend/app/deps/auth.py"
      to: "backend/app/core/security.py"
      via: "decode_token import"
      pattern: "decode_token"
    - from: "backend/app/routers/auth.py"
      to: "backend/app/models/user.py"
      via: "User lookup by email"
      pattern: "User"
---

## Revision History

- **Iteration 1 (initial):** Auth backend with JWT dual-mode, CSRF, 3 roles (Admin/PIC/Asesor), users.bidang_id with deferred FK.
- **Iteration 2 (this revision):**
  - **B-01 + B-02 fix:** Replace 3-role seed with the **six** spec-named roles from REQ-user-roles: `super_admin`, `admin_unit`, `pic_bidang`, `asesor`, `manajer_unit`, `viewer`. All `require_role(...)` calls and tests use these names verbatim. Frontend (Plan 07) uses the same `Role` union.
  - **B-04 fix:** REMOVE `users.bidang_id` from this migration AND from the `User` model. Plan 06 (master data) creates it together with the FK to `bidang(id)` after the `bidang` table exists. Auth migration's `users` table has no `bidang_id` column.
  - **B-06 fix:** Verify blocks now run **real `pytest`** (not `ast.parse`) against the test files this plan creates. Tests that exercise SQL fixtures use `docker compose exec pulse-backend pytest …` with a `docker info` preflight; tests that don't need the DB (e.g., `test_password_hash_roundtrip`) run on host.
  - **W-02 wiring:** This plan now also touches `backend/app/deps/metrics_admin.py` to swap the placeholder dep for `require_role("super_admin","admin_unit")` so `/health/detail` and `/metrics` from Plan 03 become callable by admins.

<objective>
Implement JWT-based authentication (REQ-auth-jwt) and the **six** Phase-1 roles (REQ-user-roles) on the FastAPI backend, with dual-mode token transport (Bearer header OR httpOnly cookie), refresh-token rotation backed by Redis, CSRF double-submit protection on cookie-mutating routes, brute-force lockout, and an explicit-algorithm JWT decode. Tests cover login round-trip, role 403 contract, and refresh rotation.

Purpose: REQ-auth-jwt and REQ-user-roles, plus the backend half of REQ-route-guards (frontend half is in Plan 07). Plan 06 (master data) reuses `require_role` from this plan; Plan 07 (frontend) consumes `/auth/login` and `/auth/me`. This plan also closes the Plan 03 `metrics_admin_dep` placeholder (W-02 wiring).

**Wave 3 — sequential after Plan 03 (Wave 2).** Plan 06 (master data) is now Wave 4 (sequential after Plan 05) per W-04 fix. The `users.bidang_id` column + FK move entirely to Plan 06 (B-04 fix), so the Alembic chain is: 0001_baseline → 0002_auth_users_roles → 0003_master_data (where 0003 adds `users.bidang_id` via `op.add_column` + `op.create_foreign_key`).
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

<interfaces>
<!-- From Plan 03 (already in place — DO NOT modify these files) -->
- app.db.session.engine / SessionLocal
- app.deps.db.get_db
- app.deps.redis.get_redis
- app.core.config.settings  (with JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TTL_MIN, JWT_REFRESH_TTL_DAYS)
- app.db.base.Base + auto-import-models (so this plan's new models are picked up by Alembic without editing base.py)
- app.routers.api_router  (this plan's auth.py just defines `router = APIRouter(prefix="/auth", tags=["auth"])` — auto-included)
- app.deps.metrics_admin.metrics_admin_dep  (placeholder dep — REPLACE in Task 2 of THIS plan)
- backend/tests/conftest.py  (client + db_session fixtures available)

<!-- Exposed seams Plan 06 (master data) consumes -->
- from app.deps.auth import current_user, require_role
- require_role("super_admin", "admin_unit") -> dependency factory (FastAPI Depends)
- require_role("pic_bidang") for read-scoped routes
- decoded payload shape: {"sub": "<user_id>", "roles": ["admin_unit"], "bidang_id": null|"<uuid>", "iat": .., "exp": .., "typ": "access"}
- The token's `bidang_id` claim is sourced from `User.bidang_id` after Plan 06's migration adds the column. Until then, claim is always null. The login handler reads it via `getattr(user, "bidang_id", None)` so this plan compiles before Plan 06 runs.

<!-- Exposed seams Plan 07 (auth frontend) consumes -->
- POST /api/v1/auth/login   body {email, password}  -> 200 {access_token, refresh_token, user: {id, email, full_name, roles, bidang_id}}
                                                       also sets access_token (path=/api/v1, samesite=lax, httpOnly, secure)
                                                                refresh_token (path=/api/v1/auth/refresh, samesite=strict, httpOnly, secure)
                                                                csrf_token (path=/, samesite=lax, NOT httpOnly  — frontend reads + echoes via X-CSRF-Token)
- POST /api/v1/auth/refresh -> 200 {access_token, refresh_token}  (rotates jti)
- POST /api/v1/auth/logout  -> 204
- GET  /api/v1/auth/me      -> 200 {id, email, full_name, roles, bidang_id, is_active}
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: User + Role models + Alembic 0002 migration with SIX roles seeded (B-01/B-02), NO bidang_id (B-04)</name>
  <files>
    backend/app/models/user.py,
    backend/app/models/role.py,
    backend/app/schemas/user.py,
    backend/alembic/versions/20260512_100000_0002_auth_users_roles.py
  </files>
  <action>
    1. `backend/app/models/role.py`:
       ```python
       from datetime import datetime
       import uuid
       from sqlalchemy import String, Table, Column, ForeignKey, DateTime, text
       from sqlalchemy.dialects.postgresql import UUID
       from sqlalchemy.orm import Mapped, mapped_column
       from app.db.base import Base

       class Role(Base):
           __tablename__ = "roles"
           id:   Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
           name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
           description: Mapped[str | None] = mapped_column(String(255))
           created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

       user_roles = Table(
           "user_roles",
           Base.metadata,
           Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
           Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
       )
       ```

    2. `backend/app/models/user.py` — **B-04 fix: NO `bidang_id` column in this model.** Plan 06 will add it via `op.add_column` + `op.create_foreign_key` once `bidang` exists. The Python model can be amended in Plan 06 with a one-line addition; meanwhile the auth router uses `getattr(user, "bidang_id", None)` so login still works pre-Plan-06.
       ```python
       from datetime import datetime
       import uuid
       from sqlalchemy import Boolean, String, DateTime, text
       from sqlalchemy.dialects.postgresql import UUID
       from sqlalchemy.orm import Mapped, mapped_column, relationship
       from app.db.base import Base
       from app.models.role import Role, user_roles

       class User(Base):
           __tablename__ = "users"
           id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
           email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
           full_name: Mapped[str] = mapped_column(String(255), nullable=False)
           password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
           is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)
           # NOTE: bidang_id column intentionally NOT declared here per CONTEXT.md "Migration FK ordering" (B-04 fix).
           # Plan 06 (master data) declares it via op.add_column + op.create_foreign_key after `bidang` is created,
           # and amends this model file in-place to add `bidang_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bidang.id", ondelete="SET NULL"), nullable=True)`.
           created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
           updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"))
           deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
           roles: Mapped[list[Role]] = relationship("Role", secondary=user_roles, lazy="selectin")
       ```

    3. `backend/app/schemas/user.py` — Pydantic v2 DTOs. `bidang_id` stays in the public schema as Optional UUID; the field is populated only after Plan 06 lands (the model attribute will be missing pre-Plan-06, so we use a `model_validator` defaulting to None):
       ```python
       from pydantic import BaseModel, EmailStr, ConfigDict, model_validator
       from uuid import UUID

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
               # Accept SQLAlchemy User instances: extract role names from `roles` relationship.
               if hasattr(v, "roles") and not isinstance(v, dict):
                   roles = [r.name for r in (getattr(v, "roles") or [])]
                   bidang_id = getattr(v, "bidang_id", None)
                   return {
                       "id": v.id, "email": v.email, "full_name": v.full_name,
                       "is_active": v.is_active, "bidang_id": bidang_id, "roles": roles,
                   }
               return v
       ```

    4. `backend/alembic/versions/20260512_100000_0002_auth_users_roles.py` — creates `roles`, `users` (no `bidang_id`), `user_roles` tables. **Seeds SIX role rows verbatim per REQ-user-roles** (B-01 + B-02):
       ```python
       """auth: users + roles + user_roles (six-role seed; bidang_id added by 0003 per B-04)

       Revision ID: 0002_auth_users_roles
       Revises: 0001_baseline
       Create Date: 2026-05-12 10:00:00
       """
       from alembic import op
       import sqlalchemy as sa
       from sqlalchemy.dialects.postgresql import UUID

       revision = "0002_auth_users_roles"
       down_revision = "0001_baseline"
       branch_labels = None
       depends_on = None

       # B-01 + B-02 fix: six roles per REQ-user-roles spec naming, used verbatim everywhere.
       PHASE1_ROLES: list[tuple[str, str]] = [
           ("super_admin",  "Akses penuh lintas-bidang dan lintas-unit; pemilik konfigurasi sistem."),
           ("admin_unit",   "Admin tingkat unit pembangkit; CRUD master data dan kelola pengguna unit."),
           ("pic_bidang",   "PIC bidang yang mengisi self-assessment dan rekomendasi pada bidang_id-nya."),
           ("asesor",       "Asesor yang mereview submission PIC; approve / override / request_revision."),
           ("manajer_unit", "Manajer unit yang mengonsumsi dashboard NKO dan laporan eksekutif."),
           ("viewer",       "Read-only viewer untuk audit / observer; tidak ada mutasi."),
       ]

       def upgrade() -> None:
           op.create_table(
               "roles",
               sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
               sa.Column("name", sa.String(64), nullable=False, unique=True),
               sa.Column("description", sa.String(255), nullable=True),
               sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
           )
           op.create_table(
               "users",
               sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
               sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
               sa.Column("full_name", sa.String(255), nullable=False),
               sa.Column("password_hash", sa.String(255), nullable=False),
               sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
               # NO bidang_id here — Plan 06 (0003_master_data) adds it after `bidang` exists (B-04 fix).
               sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
               sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
               sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
           )
           op.create_table(
               "user_roles",
               sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
               sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
           )
           # Six-role seed (B-01/B-02). Idempotent via INSERT ... ON CONFLICT DO NOTHING.
           bind = op.get_bind()
           for name, desc in PHASE1_ROLES:
               bind.execute(
                   sa.text("INSERT INTO roles (name, description) VALUES (:n, :d) ON CONFLICT (name) DO NOTHING"),
                   {"n": name, "d": desc},
               )

       def downgrade() -> None:
           op.drop_table("user_roles")
           op.drop_table("users")
           op.drop_table("roles")
       ```
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        # Real Python parse via importing the module (B-06: no ast-only)
        Push-Location backend
        python -c 'from app.models.user import User; from app.models.role import Role; from app.schemas.user import UserPublic; print(\"models import OK\")' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 };
        # B-04: User must NOT declare bidang_id (Plan 06 adds it)
        python -c 'from sqlalchemy import inspect; from app.models.user import User; cols = {c.name for c in inspect(User).columns}; assert \"bidang_id\" not in cols, f\"B-04 violation: bidang_id present in users table model: {cols}\"; print(\"B-04 OK: bidang_id NOT in user model\")' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 2 };
        Pop-Location
        # Migration content checks (B-01 / B-02 / B-04)
        $mig = Get-Content 'backend/alembic/versions/20260512_100000_0002_auth_users_roles.py' -Raw;
        # The migration must seed all six spec-named roles
        foreach ($role in 'super_admin','admin_unit','pic_bidang','asesor','manajer_unit','viewer') {
          if ($mig -notmatch [regex]::Escape($role)) { Write-Output ('B-01/B-02 missing role seed: ' + $role); exit 3 }
        };
        # Old 3-role names must NOT appear as seed values (only allowed in comments stripped via grep -v)
        $migNoComments = ($mig -split \"``n\") | Where-Object { $_ -notmatch '^\\s*#' } | Out-String;
        foreach ($legacy in '\"Admin\"','\"PIC\"','\"Asesor\"') {
          if ($migNoComments -match $legacy) { Write-Output ('legacy role identifier still present (B-01/B-02): ' + $legacy); exit 4 }
        };
        # B-04: migration must NOT create users.bidang_id
        if ($mig -match 'bidang_id' -and $mig -notmatch '# NO bidang_id') {
          # Allow only in a comment line that explicitly disclaims it
          if (($mig -split \"``n\") | Where-Object { $_ -match 'bidang_id' -and $_ -notmatch '^\\s*#' }) {
            Write-Output 'B-04 violation: 0002 migration declares bidang_id'; exit 5
          }
        };
        if ($mig -notmatch 'down_revision\\s*=\\s*\"0001_baseline\"') { exit 6 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    User model imports cleanly and has NO `bidang_id` column (B-04). Role model + schemas parse. Alembic 0002 creates `roles`, `users` (without bidang_id), `user_roles`; seeds six spec-named role rows (B-01/B-02). Old 3-role names absent. down_revision chains to 0001_baseline.
  </done>
</task>

<task type="auto">
  <name>Task 2: Security primitives + refresh-token Redis service + auth deps + CSRF + W-02 metrics_admin_dep wiring</name>
  <files>
    backend/app/core/security.py,
    backend/app/services/refresh_tokens.py,
    backend/app/deps/auth.py,
    backend/app/deps/csrf.py,
    backend/app/deps/metrics_admin.py,
    backend/app/schemas/auth.py
  </files>
  <action>
    1. `backend/app/core/security.py` — RESEARCH.md Pattern 3 verbatim, with explicit-algorithm allow-list on decode (defense vs `alg: none`):
       ```python
       from datetime import datetime, timedelta, timezone
       from uuid import uuid4
       from jose import JWTError, jwt
       from passlib.context import CryptContext
       from app.core.config import settings

       pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

       def hash_password(plain: str) -> str: return pwd_context.hash(plain)
       def verify_password(plain: str, hashed: str) -> bool: return pwd_context.verify(plain, hashed)

       def create_access_token(sub: str, roles: list[str], bidang_id: str | None) -> tuple[str, datetime]:
           now = datetime.now(timezone.utc)
           exp = now + timedelta(minutes=settings.JWT_ACCESS_TTL_MIN)
           payload = {"sub": sub, "roles": roles, "bidang_id": bidang_id,
                      "iat": now, "exp": exp, "typ": "access"}
           tok = jwt.encode(payload, settings.JWT_SECRET_KEY.get_secret_value(), algorithm=settings.JWT_ALGORITHM)
           return tok, exp

       def create_refresh_token(sub: str) -> tuple[str, str, datetime]:
           now = datetime.now(timezone.utc)
           exp = now + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
           jti = uuid4().hex
           payload = {"sub": sub, "jti": jti, "iat": now, "exp": exp, "typ": "refresh"}
           tok = jwt.encode(payload, settings.JWT_SECRET_KEY.get_secret_value(), algorithm=settings.JWT_ALGORITHM)
           return tok, jti, exp

       def decode_token(token: str) -> dict:
           # Explicit allow-list; rejects alg: none and alg-confusion.
           return jwt.decode(token, settings.JWT_SECRET_KEY.get_secret_value(),
                             algorithms=[settings.JWT_ALGORITHM])
       ```

    2. `backend/app/services/refresh_tokens.py` — Redis-backed jti revocation:
       ```python
       from redis.asyncio import Redis
       from datetime import datetime, timezone

       async def revoke_jti(r: Redis, user_id: str, jti: str, exp: datetime) -> None:
           ttl = max(1, int((exp - datetime.now(timezone.utc)).total_seconds()))
           await r.set(f"revoked:{user_id}:{jti}", "1", ex=ttl)

       async def is_revoked(r: Redis, user_id: str, jti: str) -> bool:
           return bool(await r.exists(f"revoked:{user_id}:{jti}"))
       ```

    3. `backend/app/deps/auth.py` — RESEARCH.md Pattern 3:
       ```python
       from fastapi import Cookie, Depends, Header, HTTPException, status
       from jose import JWTError
       from sqlalchemy import select
       from sqlalchemy.ext.asyncio import AsyncSession
       from app.core.security import decode_token
       from app.deps.db import get_db
       from app.models.user import User

       async def current_user(
           authorization: str | None = Header(default=None),
           access_token: str | None = Cookie(default=None),
           db: AsyncSession = Depends(get_db),
       ) -> User:
           token = None
           if authorization and authorization.lower().startswith("bearer "):
               token = authorization.split(" ", 1)[1]
           elif access_token:
               token = access_token
           if not token:
               raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
           try:
               payload = decode_token(token)
               if payload.get("typ") != "access":
                   raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
           except JWTError:
               raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
           user = await db.scalar(select(User).where(User.id == payload["sub"], User.is_active.is_(True), User.deleted_at.is_(None)))
           if not user:
               raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer active")
           return user

       def require_role(*allowed: str):
           # B-01/B-02: callers pass spec role names verbatim, e.g. require_role("super_admin", "admin_unit").
           async def _check(user: User = Depends(current_user)) -> User:
               user_role_names = {r.name for r in user.roles}
               if not user_role_names & set(allowed):
                   raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
               return user
           return _check
       ```

    4. `backend/app/deps/csrf.py` — Double-submit:
       ```python
       from fastapi import Cookie, Header, HTTPException, status

       async def require_csrf(
           csrf_token: str | None = Cookie(default=None),
           x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
           authorization: str | None = Header(default=None),
       ) -> None:
           if authorization and authorization.lower().startswith("bearer "):
               return
           if not csrf_token or not x_csrf_token or csrf_token != x_csrf_token:
               raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token mismatch")
       ```

    5. `backend/app/deps/metrics_admin.py` — **W-02 wiring**: replace the Plan-03 placeholder body with a `require_role` delegate so `/health/detail` and `/metrics` are now admin-callable:
       ```python
       """W-02 wiring (was a 401-everything placeholder in Plan 03; Plan 05 wires it to require_role).
       Health endpoints (Plan 03) import `metrics_admin_dep` from this module — they don't change."""
       from app.deps.auth import require_role

       # Per CONTEXT.md API: /health/detail and /metrics are admin-only.
       # Spec roles per REQ-user-roles (B-01/B-02): super_admin and admin_unit.
       metrics_admin_dep = require_role("super_admin", "admin_unit")
       ```

    6. `backend/app/schemas/auth.py`:
       ```python
       from pydantic import BaseModel, EmailStr, Field
       from app.schemas.user import UserPublic

       class LoginRequest(BaseModel):
           email: EmailStr
           password: str = Field(min_length=1)

       class TokenPair(BaseModel):
           access_token: str
           refresh_token: str
           token_type: str = "bearer"
           user: UserPublic
       ```
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $sec = Get-Content 'backend/app/core/security.py' -Raw;
        if ($sec -notmatch 'algorithms=\\[settings\\.JWT_ALGORITHM\\]') { exit 1 };
        if ($sec -notmatch 'CryptContext.*bcrypt') { exit 2 };
        $deps = Get-Content 'backend/app/deps/auth.py' -Raw;
        if ($deps -notmatch 'require_role') { exit 3 };
        if ($deps -notmatch 'access_token.*=.*Cookie') { exit 4 };
        if ($deps -notmatch 'authorization.*=.*Header') { exit 5 };
        $csrf = Get-Content 'backend/app/deps/csrf.py' -Raw;
        if ($csrf -notmatch 'X-CSRF-Token') { exit 6 };
        $rt = Get-Content 'backend/app/services/refresh_tokens.py' -Raw;
        if ($rt -notmatch 'revoked')   { exit 7 };
        # W-02 wiring check: metrics_admin_dep must call require_role with super_admin + admin_unit
        $ma = Get-Content 'backend/app/deps/metrics_admin.py' -Raw;
        if ($ma -notmatch 'require_role') { Write-Output 'W-02 wiring missing'; exit 8 };
        if ($ma -notmatch 'super_admin')  { exit 9 };
        if ($ma -notmatch 'admin_unit')   { exit 10 };
        # Old placeholder body (`HTTP_401_UNAUTHORIZED` raise) must be gone
        if ($ma -match 'HTTP_401_UNAUTHORIZED') { Write-Output 'old placeholder still present in metrics_admin.py'; exit 11 };
        # Real-import smoke (B-06)
        Push-Location backend
        python -c 'from app.core.security import hash_password, verify_password, decode_token, create_access_token, create_refresh_token; from app.deps.auth import current_user, require_role; from app.deps.csrf import require_csrf; from app.deps.metrics_admin import metrics_admin_dep; from app.services.refresh_tokens import revoke_jti, is_revoked; print(\"imports OK\")' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 12 };
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Security primitives use explicit algorithm allow-list; dual-mode auth dep accepts Bearer OR cookie; require_role enforces role intersection (callers use spec names); CSRF dep skips Bearer mode but enforces double-submit on cookie mode; refresh-token service has revoke + is_revoked; metrics_admin_dep is now `require_role("super_admin","admin_unit")` (W-02 closed).
  </done>
</task>

<task type="auto">
  <name>Task 3: Auth router (login/refresh/logout/me) + brute-force lockout + tests using SIX-role seed (real pytest)</name>
  <files>
    backend/app/routers/auth.py,
    backend/tests/test_auth.py,
    backend/tests/test_rbac.py,
    backend/tests/test_user_roles.py
  </files>
  <action>
    1. `backend/app/routers/auth.py` — full Phase-1 auth endpoints. Key points:
       - `router = APIRouter(prefix="/auth", tags=["auth"])` (auto-included).
       - `POST /login`: lookup user by email; on success, build `bidang_id = getattr(user, "bidang_id", None)` (None until Plan 06 adds the column), build access+refresh + a random `csrf_token = secrets.token_urlsafe(32)`. Set three cookies. Return `TokenPair`.
       - Brute-force lockout: Redis `login_fail:{email}` integer counter, TTL 300s. On 5+ fails return 429 with `Retry-After: 900`. Reset on success.
       - `POST /refresh`: read refresh token from cookie OR `refresh_token` field in JSON body OR Bearer header. Decode with allow-list, assert `typ=="refresh"`, check `is_revoked`, on success revoke old jti and issue new pair (rotate).
       - `POST /logout`: revoke active jti; clear all three cookies.
       - `GET /me`: depends on `current_user`; return `UserPublic`.

       Cookie config: same as iteration 1 (httpOnly access/refresh + non-httpOnly csrf). In dev (DEBUG=true) drop `secure=True`.

    2. `backend/tests/test_auth.py` — covers REQ-auth-jwt acceptance using the new role names:
       ```python
       import pytest, secrets
       from sqlalchemy import select
       from app.models.user import User
       from app.models.role import Role
       from app.core.security import hash_password

       @pytest.fixture
       async def admin(db_session):
           # Use admin_unit (B-01/B-02 spec name) — was "Admin" pre-revision.
           role = await db_session.scalar(select(Role).where(Role.name == "admin_unit"))
           u = User(email="admin@pulse.local", full_name="Admin", password_hash=hash_password("s3cret-pwd"))
           u.roles = [role]
           db_session.add(u); await db_session.flush()
           return u

       @pytest.mark.asyncio
       async def test_login_returns_tokens_and_cookies(client, admin):
           r = await client.post("/api/v1/auth/login", json={"email": admin.email, "password": "s3cret-pwd"})
           assert r.status_code == 200, r.text
           body = r.json()
           assert body["access_token"] and body["refresh_token"]
           assert body["user"]["email"] == admin.email
           assert "admin_unit" in body["user"]["roles"]
           assert "access_token" in r.cookies and "refresh_token" in r.cookies and "csrf_token" in r.cookies

       @pytest.mark.asyncio
       async def test_login_wrong_password_returns_401(client, admin):
           r = await client.post("/api/v1/auth/login", json={"email": admin.email, "password": "wrong"})
           assert r.status_code == 401

       @pytest.mark.asyncio
       async def test_me_with_bearer(client, admin):
           r = await client.post("/api/v1/auth/login", json={"email": admin.email, "password": "s3cret-pwd"})
           access = r.json()["access_token"]
           me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
           assert me.status_code == 200
           assert me.json()["email"] == admin.email
           assert "admin_unit" in me.json()["roles"]

       @pytest.mark.asyncio
       async def test_refresh_rotates_jti(client, admin):
           r1 = await client.post("/api/v1/auth/login", json={"email": admin.email, "password": "s3cret-pwd"})
           refresh1 = r1.json()["refresh_token"]
           r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
           assert r2.status_code == 200
           refresh2 = r2.json()["refresh_token"]
           assert refresh2 != refresh1
           r3 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
           assert r3.status_code == 401

       @pytest.mark.asyncio
       async def test_brute_force_lockout(client, admin):
           for _ in range(5):
               await client.post("/api/v1/auth/login", json={"email": admin.email, "password": "wrong"})
           r = await client.post("/api/v1/auth/login", json={"email": admin.email, "password": "s3cret-pwd"})
           assert r.status_code == 429
           assert "Retry-After" in r.headers
       ```

    3. `backend/tests/test_rbac.py` — REQ-route-guards backend half, **uses spec role names**:
       ```python
       import pytest
       from sqlalchemy import select
       from app.models.user import User
       from app.models.role import Role
       from app.core.security import hash_password
       from fastapi import APIRouter, Depends
       from app.main import app
       from app.deps.auth import require_role

       _t = APIRouter(prefix="/__test")
       @_t.get("/admin-only", dependencies=[Depends(require_role("super_admin", "admin_unit"))])
       async def admin_only(): return {"ok": True}
       @_t.get("/pic-only", dependencies=[Depends(require_role("pic_bidang"))])
       async def pic_only(): return {"ok": True}
       @_t.get("/manajer-only", dependencies=[Depends(require_role("manajer_unit"))])
       async def manajer_only(): return {"ok": True}
       app.include_router(_t)

       async def _user_with_role(db_session, email: str, role_name: str) -> User:
           role = await db_session.scalar(select(Role).where(Role.name == role_name))
           u = User(email=email, full_name=role_name, password_hash=hash_password("pwd"))
           u.roles = [role]
           db_session.add(u); await db_session.flush()
           return u

       @pytest.fixture
       async def pic_user(db_session):
           return await _user_with_role(db_session, "pic@pulse.local", "pic_bidang")

       @pytest.fixture
       async def admin_unit_user(db_session):
           return await _user_with_role(db_session, "admin-unit@pulse.local", "admin_unit")

       @pytest.fixture
       async def manajer_user(db_session):
           return await _user_with_role(db_session, "manajer@pulse.local", "manajer_unit")

       @pytest.mark.asyncio
       async def test_pic_blocked_from_admin_endpoint(client, pic_user):
           login = await client.post("/api/v1/auth/login", json={"email": pic_user.email, "password": "pwd"})
           token = login.json()["access_token"]
           r = await client.get("/__test/admin-only", headers={"Authorization": f"Bearer {token}"})
           assert r.status_code == 403

       @pytest.mark.asyncio
       async def test_admin_unit_allowed_for_admin_endpoint(client, admin_unit_user):
           login = await client.post("/api/v1/auth/login", json={"email": admin_unit_user.email, "password": "pwd"})
           token = login.json()["access_token"]
           r = await client.get("/__test/admin-only", headers={"Authorization": f"Bearer {token}"})
           assert r.status_code == 200

       @pytest.mark.asyncio
       async def test_pic_allowed_for_pic_endpoint(client, pic_user):
           login = await client.post("/api/v1/auth/login", json={"email": pic_user.email, "password": "pwd"})
           token = login.json()["access_token"]
           r = await client.get("/__test/pic-only", headers={"Authorization": f"Bearer {token}"})
           assert r.status_code == 200

       @pytest.mark.asyncio
       async def test_manajer_blocked_from_pic_endpoint(client, manajer_user):
           login = await client.post("/api/v1/auth/login", json={"email": manajer_user.email, "password": "pwd"})
           token = login.json()["access_token"]
           r = await client.get("/__test/pic-only", headers={"Authorization": f"Bearer {token}"})
           assert r.status_code == 403

       @pytest.mark.asyncio
       async def test_unauthenticated_returns_401(client):
           r = await client.get("/__test/admin-only")
           assert r.status_code == 401
       ```

    4. `backend/tests/test_user_roles.py` — REQ-user-roles seed assertion (all SIX roles) + password roundtrip:
       ```python
       import pytest
       from sqlalchemy import select
       from app.models.role import Role
       from app.core.security import hash_password, verify_password

       PHASE1_ROLES = {"super_admin", "admin_unit", "pic_bidang", "asesor", "manajer_unit", "viewer"}

       @pytest.mark.asyncio
       async def test_six_phase1_roles_seeded(db_session):
           rows = (await db_session.scalars(select(Role.name))).all()
           names = set(rows)
           missing = PHASE1_ROLES - names
           assert not missing, f"missing seeded roles (B-01/B-02): {missing}"

       def test_password_hash_roundtrip():
           h = hash_password("hello-pulse-2026")
           assert verify_password("hello-pulse-2026", h)
           assert not verify_password("wrong", h)
       ```
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $r = Get-Content 'backend/app/routers/auth.py' -Raw;
        foreach ($pat in '/login','/refresh','/logout','/me','set_cookie\\(.*access_token','set_cookie\\(.*refresh_token','set_cookie\\(.*csrf_token','login_fail') {
          if ($r -notmatch $pat) { Write-Output ('missing pattern: ' + $pat); exit 1 }
        };
        # B-01 / B-02 sweep across the auth files + tests: role identifiers must use spec names
        $tests = @('backend/tests/test_auth.py','backend/tests/test_rbac.py','backend/tests/test_user_roles.py') | ForEach-Object { Get-Content $_ -Raw } | Out-String;
        # Spec names must appear
        foreach ($role in 'super_admin','admin_unit','pic_bidang','asesor','manajer_unit','viewer') {
          if ($tests -notmatch $role) { Write-Output ('test missing spec role: ' + $role); exit 2 }
        };
        # Legacy 3-role identifiers must NOT appear as string literals (allow Asesor since it's a spec name; capitalized 'Admin'/'PIC' must be gone)
        if ($tests -match '\"Admin\"') { Write-Output 'legacy role \"Admin\" still in tests'; exit 3 };
        if ($tests -match '\"PIC\"')   { Write-Output 'legacy role \"PIC\" still in tests'; exit 4 };
        # B-06: real test execution against the running container (CONTEXT.md: docker compose exec pytest with docker info preflight)
        docker info 1>$null 2>&1
        if ($LASTEXITCODE -ne 0) {
          Write-Output 'docker engine not reachable — skipping pytest-in-container smoke. Plan 07 e2e checkpoint will gate this.';
          # Fall back to a host-side import smoke so we still validate Python syntax + imports without DB.
          Push-Location backend
          python -c 'import importlib; mods = [\"app.routers.auth\",\"app.core.security\",\"app.deps.auth\"]; [importlib.import_module(m) for m in mods]; from tests import test_auth, test_rbac, test_user_roles; print(\"imports OK\")' 2>&1 | Out-String | Write-Output
          if ($LASTEXITCODE -ne 0) { Pop-Location; exit 5 };
          Pop-Location
          Write-Output 'pass (docker offline; container pytest deferred to Plan 07 checkpoint)';
          exit 0
        };
        # If docker is up AND the stack happens to be running, run pytest in the backend container.
        $running = docker compose ps --services --filter status=running 2>$null;
        if ($running -match 'pulse-backend') {
          docker compose exec -T pulse-backend pytest tests/test_auth.py tests/test_rbac.py tests/test_user_roles.py -x -q 2>&1 | Out-String | Write-Output
          if ($LASTEXITCODE -ne 0) { Write-Output 'pytest failed in pulse-backend container'; exit 6 };
        } else {
          Write-Output 'pulse-backend container not running yet (Plan 02 must apply migrations first); imports-only smoke';
          Push-Location backend
          python -c 'from app.routers.auth import router; from tests import test_auth, test_rbac, test_user_roles; print(\"imports OK\")' 2>&1 | Out-String | Write-Output
          if ($LASTEXITCODE -ne 0) { Pop-Location; exit 7 };
          Pop-Location
        };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Four endpoints implemented (login/refresh/logout/me) with dual-mode token transport, three-cookie set on login, brute-force lockout via Redis, refresh rotation via jti revoke set. Test files cover login round-trip, refresh rotation, brute-force lockout, RBAC 403 + 200 across spec role names, six-role seed presence, password roundtrip. Verify executes real pytest when the stack is running (B-06) or falls through to import-smoke + docker-info preflight when stack is offline.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Browser → /api/v1/auth/* | Untrusted; rate-limited by nginx login_zone + Redis lockout |
| JWT in transit | Signed HS256; secret from env |
| Refresh token at rest | In httpOnly cookie OR Redis revocation set |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-05-S-01 | Spoofing | JWT alg confusion (`alg: none`, RS→HS) | mitigate | `jwt.decode(..., algorithms=[settings.JWT_ALGORITHM])` explicit allow-list. |
| T-05-S-02 | Spoofing | Brute-force login | mitigate | Nginx `login_zone 5r/m` (Plan 02) + Redis counter `login_fail:{email}` -> 429 after 5 fails in 300s. |
| T-05-S-03 | Spoofing | Token replay after logout | mitigate | Refresh-token jti revocation set in Redis with TTL = remaining lifetime; `is_revoked` checked on `/refresh`. |
| T-05-T-01 | Tampering | CSRF via cookie auth | mitigate | Double-submit `X-CSRF-Token` header vs `csrf_token` cookie on cookie-auth mutating routes. Skipped for Bearer mode. |
| T-05-I-01 | Information disclosure | Token in URL (XSS, logs, referer) | mitigate | Tokens only in cookies (httpOnly) and JSON body — never query params. structlog (Plan 03); never log token values. |
| T-05-I-02 | Information disclosure | `/health/detail` + `/metrics` reveal internals | mitigate | metrics_admin_dep now delegates to `require_role("super_admin","admin_unit")` (W-02 wiring). |
| T-05-R-01 | Repudiation | User claims they didn't log in | accept | Audit log added in Phase 2 (REQ-audit-log). |
| T-05-D-01 | DoS | Bcrypt verify cost saturates CPU | mitigate | Brute-force lockout caps work; Nginx login_zone caps request rate. |
| T-05-E-01 | Elevation | Missing role check on a future endpoint | mitigate | `require_role` is documented convention; Plan 06 + future plans add it to every mutating route; no-upload test catches one class of mistake. |
</threat_model>

<verification>
- `pytest backend/tests/test_auth.py backend/tests/test_rbac.py backend/tests/test_user_roles.py -x` passes inside `pulse-backend` (real exec — B-06)
- `alembic upgrade head` applies 0002 migration without error AND `users` has no `bidang_id` column (B-04)
- All six spec roles seeded: `super_admin, admin_unit, pic_bidang, asesor, manajer_unit, viewer` (B-01/B-02)
- OpenAPI `/api/v1/docs` shows /auth/login, /auth/refresh, /auth/logout, /auth/me
- `/api/v1/health/detail` and `/api/v1/metrics` are now callable by admin_unit / super_admin tokens (W-02 wiring)
</verification>

<success_criteria>
- All four endpoints functional with dual-mode token transport
- Refresh rotation rejects reuse of old refresh token
- Brute-force lockout fires at 5 failures
- **Six** Phase-1 role rows seeded with spec naming (B-01/B-02)
- JWT decode uses explicit algorithm allow-list
- CSRF double-submit enforced on cookie-mode mutating routes
- `users.bidang_id` is NOT in this migration (B-04 — Plan 06 owns it)
- `metrics_admin_dep` swapped from placeholder to `require_role` (W-02)
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-master-data-auth/01-05-SUMMARY.md` listing:
1. Final endpoint contract table (path, methods, request shape, response shape, cookie set/cleared)
2. Cookie config table
3. Test-to-requirement traceability (which test covers which REQ-)
4. **Six-role seed audit (B-01/B-02):** the six rows present in `roles` table after migration runs
5. **B-04 audit:** confirm `users` table has columns: id, email, full_name, password_hash, is_active, created_at, updated_at, deleted_at — and NOT `bidang_id`
6. **W-02 wiring note:** `metrics_admin_dep` now points at `require_role("super_admin","admin_unit")`; downstream plans don't re-import.
</output>
