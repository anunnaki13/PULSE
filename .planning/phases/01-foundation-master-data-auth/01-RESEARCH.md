# Phase 1: Foundation (Master Data + Auth) — Research

**Researched:** 2026-05-11
**Domain:** Full-stack scaffolding (FastAPI + React 18 + PostgreSQL 16 + Docker Compose) with auth, design-system primitives, and ops baseline
**Confidence:** HIGH (stack is fully locked; research focuses on *how-to* patterns)

## Summary

Phase 1 establishes a runnable PULSE shell: a FastAPI + asyncpg backend, a React 18 + Vite + TypeScript frontend with skeuomorphic Pulse Heartbeat design system, PostgreSQL 16 with pgvector extension, Redis 7 cache, and an Nginx reverse proxy on host port 3399 — all orchestrated by Docker Compose. The locked stack (CONSTR-stack-*, DEC-010) removes most architectural choice; this research therefore concentrates on **best-practice scaffolding patterns** for that exact stack as it stands in May 2026, with verified library versions from PyPI/npm/Docker Hub.

The four highest-leverage decisions still under Claude's discretion are: (1) **monorepo layout** — single repo with `backend/`, `frontend/`, `nginx/`, `docker-compose.yml`, `.env.example` at root; (2) **JWT library** — recommend `python-jose[cryptography]` + a custom `Depends` chain (ergonomic, low-magic, matches the small-team-solo-dev profile far better than `fastapi-users` or `authx`); (3) **i18n strategy** — recommend a hand-rolled lookup map for Phase 1, deferring `react-i18next` (~22 kB) until English translation is actually required; (4) **backup architecture** — recommend a sidecar `pulse-backup` container with built-in cron rather than host-cron-into-container (portable, self-contained, restorable on any Docker host).

**Primary recommendation:** Monorepo with sub-folder per service; lock package versions exactly as listed in `## Standard Stack`; use `python-jose` for JWT with httpOnly cookie + Bearer dual-mode and a single role-checking dependency; ship `pgvector/pgvector:pg16` with a `docker-entrypoint-initdb.d/00-extensions.sh` shell script (NOT .sql) for `CREATE EXTENSION` reliability; gate every motion through `prefers-reduced-motion` via framer-motion's `MotionConfig reducedMotion="user"` plus a CSS-keyframes fallback for `.sk-led[data-state="on"]`; assert the no-upload policy with a pytest case that introspects the live OpenAPI schema.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| User authentication (JWT issue/verify) | API / Backend | — | Secrets (`JWT_SECRET_KEY`) and refresh-token state must live server-side; locked by CONSTR-env-secrets. |
| Session storage (httpOnly cookie) | Browser (cookie jar) + API (Set-Cookie) | — | Cookie is set by FastAPI `Response.set_cookie`; browser stores it; client JS never reads it. |
| Route guard / role gate (UI) | Browser / Client | API (canonical enforcement) | UX layer prevents wasted nav; backend remains source of truth via `Depends(require_role(...))`. |
| Master-data CRUD (konkin_template, indikator, ml_stream) | API / Backend | Database | All persistence + validation lives in the API tier; UUID PKs and JSONB schema enforced by Postgres. |
| Excel import (single multipart endpoint) | API / Backend | — | `UploadFile` parsed server-side with openpyxl; idempotency tracked in DB. |
| Master-data browsing UI | Frontend Server (Vite dev) / CDN-static (prod build) | API | Static SPA assets served by Nginx; data fetched via REST. |
| Skeuomorphic primitives + Pulse Heartbeat animation | Browser / Client | — | Pure CSS keyframes + framer-motion; no server involvement. |
| Health check `/api/v1/health` | API / Backend | Database, Redis | API tier owns aggregation; pings db + redis via short-timeout async calls. |
| Daily backup cron | Sidecar container (Docker) | Host filesystem | Container owns schedule; volume-mounted into host backup dir. |
| Reverse proxy / TLS termination / security headers | Nginx | — | Standard tier ownership; Postgres never exposed externally. |

## Standard Stack

### Backend Core (Python 3.11)
| Library | Version | Purpose | Provenance |
|---------|---------|---------|------------|
| `fastapi` | 0.136.1 | HTTP framework, OpenAPI auto-gen | [VERIFIED: pypi.org/pypi/fastapi/json, fetched 2026-05-11] |
| `uvicorn[standard]` | 0.46.0 | ASGI server (worker class for gunicorn) | [VERIFIED: pypi.org/pypi/uvicorn/json] |
| `gunicorn` | 26.0.0 | Process manager, 4 workers prod | [VERIFIED: pypi.org/pypi/gunicorn/json] |
| `sqlalchemy[asyncio]` | 2.0.49 | Async ORM | [VERIFIED: pypi.org/pypi/sqlalchemy/json] |
| `asyncpg` | 0.31.0 | Postgres async driver | [VERIFIED: pypi.org/pypi/asyncpg/json] |
| `alembic` | 1.18.4 | Migrations | [VERIFIED: pypi.org/pypi/alembic/json] |
| `pydantic` | 2.13.4 | Schema validation (v2 API) | [VERIFIED: pypi.org/pypi/pydantic/json] |
| `pydantic-settings` | 2.14.1 | Env-var config (replaces v1 `BaseSettings`) | [VERIFIED: pypi.org/pypi/pydantic-settings/json] |
| `python-jose[cryptography]` | 3.5.0 | JWT encode/decode | [VERIFIED: pypi.org/pypi/python-jose/json] |
| `passlib[bcrypt]` | 1.7.4 | Password hashing | [VERIFIED: pypi.org/pypi/passlib/json] |
| `bcrypt` | 5.0.0 | Hash backend (pin to avoid passlib warning) | [VERIFIED: pypi.org/pypi/bcrypt/json] |
| `openpyxl` | 3.1.5 | Excel `.xlsx` parsing for admin import | [VERIFIED: pypi.org/pypi/openpyxl/json] |
| `pytest` | 9.0.3 | Test runner | [VERIFIED: pypi.org/pypi/pytest/json] |
| `pytest-asyncio` | 1.3.0 | Async test support | [VERIFIED: pypi.org/pypi/pytest-asyncio/json] |
| `httpx` | 0.28.1 | FastAPI test client | [VERIFIED: pypi.org/pypi/httpx/json] |

### Frontend Core (Node 20+)
| Library | Version | Purpose | Provenance |
|---------|---------|---------|------------|
| `react` | 19.2.6 | UI framework (Phase 1 scoped to React 18 per CONSTR-stack-frontend; pin to `^18.3.1` until upgrade decision) | [VERIFIED: npm view react] — note: npm latest is 19.x but stack is locked to React 18 [CITED: CONSTR-stack-frontend] |
| `vite` | 7.15.0 | Dev server + bundler | [VERIFIED: npm view vite] |
| `typescript` | 5.9.x (project pin) | Types | [ASSUMED] — npm view returns 4.3.0 for `typescript` core package which is misleading; use `~5.9` per Vite 7 template |
| `@tanstack/react-query` | 5.100.9 | Server state | [VERIFIED: npm view @tanstack/react-query] |
| `zustand` | 5.0.13 | Client state | [VERIFIED: npm view zustand] |
| `react-hook-form` | 7.75.0 | Form state | [VERIFIED: npm view react-hook-form] |
| `zod` | 4.4.3 | Schema validation | [VERIFIED: npm view zod] |
| `react-router-dom` | 7.15.0 | Routing — see Pitfall: v7 vs v6 below | [VERIFIED: npm view react-router-dom] |
| `tailwindcss` | 4.3.0 | CSS framework — v4 changes config model | [VERIFIED: npm view tailwindcss] |
| `@tailwindcss/vite` | matched to 4.3.x | Vite plugin (replaces postcss config) | [CITED: ui.shadcn.com/docs/tailwind-v4] |
| `tw-animate-css` | latest | Animation utilities (replaces `tailwindcss-animate` for v4) | [CITED: ui.shadcn.com/docs/tailwind-v4] |
| `motion` (framer-motion) | 12.38.0 | Animation library; package renamed from `framer-motion` to `motion` | [VERIFIED: npm view framer-motion] |
| `sonner` | 2.0.7 | Toast | [VERIFIED: npm view sonner] |
| `axios` | 1.16.0 | HTTP client | [VERIFIED: npm view axios] |
| `vitest` | 4.1.5 | Test runner | [VERIFIED: npm view vitest] |
| `@testing-library/react` | 16.3.2 | DOM testing | [VERIFIED: npm view @testing-library/react] |

### Infrastructure
| Image | Tag | Purpose | Provenance |
|-------|-----|---------|------------|
| `pgvector/pgvector` | `pg16` (or `0.8.2-pg16`) | Postgres 16 + pgvector 0.8.2 | [VERIFIED: hub.docker.com/v2/repositories/pgvector/pgvector/tags fetched 2026-05-11] |
| `redis` | `7-alpine` (current `8.6.3-alpine` if upgrading; stack locked at 7) | Cache | [VERIFIED: hub.docker.com/v2/repositories/library/redis/tags] [CITED: CONSTR-stack-cache] |
| `nginx` | `1.30-alpine` (or `mainline-alpine`) | Reverse proxy | [VERIFIED: hub.docker.com/v2/repositories/library/nginx/tags] |
| `python` | `3.11-slim` | Backend base image | [CITED: CONSTR-stack-backend] |
| `node` | `20-alpine` | Frontend build stage | [ASSUMED — stack does not pin Node version; 20 LTS is safe default] |

### Alternatives Considered (and rejected for this phase)
| Instead of | Could Use | Why rejected here |
|------------|-----------|-------------------|
| `python-jose` | `authx` | `authx` is opinionated about cookie/header semantics and ties you to its dependency model; locked stack is small enough to use raw jose + 1 dependency. Also less Stack Overflow coverage. |
| `python-jose` | `fastapi-users` | Brings whole user-management framework; PULSE has 3 fixed roles seeded at install — overkill, and obscures the role/bidang_id RBAC dimension. |
| Hand-rolled lookup map | `react-i18next` | Bundle cost ~22.2 kB gzipped [CITED: bundlephobia.com/package/react-i18next]; Phase 1 only ships BI copy, no language switcher. Defer to a later phase if EN ever needed. |
| Sidecar backup container | Host cron | Host cron requires the operator to remember installation steps on every redeploy; sidecar is part of `docker-compose up`. |

### Verification command (reproduce versions)
```bash
# Backend (one-liner per package)
curl -s https://pypi.org/pypi/fastapi/json | python -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"

# Frontend
npm view @tanstack/react-query version

# Postgres image tag
curl -s https://hub.docker.com/v2/repositories/pgvector/pgvector/tags?page_size=20 \
  | python -c "import sys,json; [print(t['name']) for t in json.load(sys.stdin)['results']]"
```

## Architecture Patterns

### System Architecture Diagram

```
[Browser]
   │  HTTPS / HTTP :3399
   ▼
[pulse-nginx]  (Nginx 1.30-alpine)
   │  ─── /             ─────► [pulse-frontend]   (built static SPA, served from Nginx upstream OR baked into nginx image)
   │  ─── /api/v1/*     ─────► [pulse-backend]    (FastAPI :8000 via gunicorn 4× UvicornWorker)
   │  ─── /ws/*         ─────► [pulse-backend]    (WebSocket upgrade, proxy_read_timeout 3600s — Phase 2 wire-up; route stub OK in Phase 1)
   │       (security headers, rate-limit zones, CSRF for cookie endpoints)
   ▼
   ┌─ pulse-backend ─────────────┐
   │  FastAPI app                │
   │   ├─ routers/               │
   │   ├─ deps (auth, db, redis) │
   │   ├─ models, schemas        │
   │   └─ alembic/               │
   └──┬─────────────┬────────────┘
      │             │
      ▼             ▼
[pulse-db]     [pulse-redis]
 (pgvector/    (Redis 7-alpine,
  pgvector:     maxmemory 256mb,
  pg16,         allkeys-lru)
  uuid-ossp,
  pgcrypto,
  vector ext.)
      │
      │ (volume mount)
      ▼
[pulse-backup]  (sidecar with cron + pg_dump → /var/backups/pulse, daily 02:00, weekly rsync to NAS 03:00 Sun)
```

Internal Docker network: `pulse-net` (bridge). Postgres port 5432 is **not** published to the host (CONSTR-host-port).

### Recommended Project Structure (monorepo)

```
PULSE/
├── docker-compose.yml             # all 6 services (db, redis, backend, frontend, nginx, backup)
├── docker-compose.override.yml    # dev-only overrides (volume mounts, hot-reload)
├── .env.example                   # JWT_SECRET_KEY, POSTGRES_PASSWORD, etc. (no real values)
├── .env                           # gitignored
├── Makefile                       # make up | down | seed | migrate | test | backup | restore
├── README.md
├── nginx/
│   ├── Dockerfile                 # FROM nginx:1.30-alpine; COPY conf, security headers
│   ├── nginx.conf
│   └── conf.d/
│       └── pulse.conf             # upstream blocks, /api proxy, /ws upgrade, security headers
├── backend/
│   ├── Dockerfile                 # FROM python:3.11-slim; gunicorn entrypoint
│   ├── pyproject.toml             # poetry or hatch
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py                 # async URL via settings
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app, lifespan, /api/v1/health
│   │   ├── core/
│   │   │   ├── config.py          # pydantic-settings BaseSettings
│   │   │   ├── security.py        # JWT encode/decode, password hash
│   │   │   └── logging.py         # structured-JSON logger to stdout
│   │   ├── db/
│   │   │   ├── session.py         # async engine + sessionmaker
│   │   │   └── base.py            # Declarative Base + import all models
│   │   ├── models/                # SQLAlchemy 2.0 models (one file per aggregate)
│   │   ├── schemas/               # Pydantic v2 DTOs
│   │   ├── deps/                  # FastAPI dependencies (get_db, current_user, require_role)
│   │   ├── routers/
│   │   │   ├── auth.py            # /auth/login, /auth/refresh, /auth/logout
│   │   │   ├── master_konkin.py   # /konkin/templates, /perspektif, /indikator, /ml-stream
│   │   │   ├── master_bidang.py
│   │   │   └── health.py
│   │   └── seed/
│   │       ├── __main__.py        # python -m app.seed -> idempotent
│   │       ├── konkin_2026.py
│   │       └── pilot_rubrics/     # outage.py smap.py eaf.py efor.py
│   └── tests/
│       ├── conftest.py            # async client + transactional db fixture
│       ├── test_auth.py
│       ├── test_master_konkin.py
│       ├── test_health.py
│       └── test_no_upload_policy.py   # introspects /openapi.json
├── frontend/
│   ├── Dockerfile                 # multi-stage: node:20-alpine build → nginx static
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.app.json          # baseUrl + paths
│   ├── vite.config.ts
│   ├── tailwind.config.ts         # v4: thin shim; tokens live in @theme inline in src/index.css
│   ├── components.json            # shadcn/ui config (paths, style=new-york, css-vars=true)
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css              # @import "tailwindcss"; @theme inline { ... CSS variables ... }
│       ├── lib/
│       │   ├── api.ts             # axios instance + interceptors (refresh-token rotation)
│       │   ├── auth-store.ts      # Zustand store
│       │   ├── query-client.ts    # TanStack Query
│       │   └── i18n.ts            # simple lookup map (BI default)
│       ├── components/
│       │   ├── ui/                # shadcn forked (Button, Input, Dialog, Toast)
│       │   └── skeuomorphic/      # SkLed, SkDial, SkLcdDigit (custom primitives)
│       ├── routes/
│       │   ├── ProtectedRoute.tsx # role-gating wrapper
│       │   ├── Login.tsx
│       │   ├── Dashboard.tsx      # PIC landing
│       │   └── master/
│       │       ├── KonkinTemplate.tsx
│       │       ├── BidangList.tsx
│       │       └── MlStreamTree.tsx
│       └── styles/
│           └── pulse-heartbeat.css   # @keyframes pulse-heartbeat
└── docs/                          # phase docs, runbooks (optional)
```

[CITED: github.com/vikramgulia/fastapi-react/blob/master/docker-compose.yml — confirms folder convention of `backend/`, `frontend/`, `nginx/` siblings under root]

### Pattern 1: Async SQLAlchemy 2.0 session dependency

**What:** A FastAPI `Depends`-yielding async generator that produces an `AsyncSession` per request and rolls back on exception.

**When to use:** Every endpoint that touches the DB.

```python
# backend/app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL,    # postgresql+asyncpg://pulse:...@pulse-db:5432/pulse
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# CRITICAL: expire_on_commit=False is required for async sessions
# [CITED: docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html]
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# backend/app/deps/db.py
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

[CITED: medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308 — confirms `expire_on_commit=False` requirement]

### Pattern 2: pydantic-settings v2 config

```python
# backend/app/core/config.py
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    APP_SECRET_KEY: SecretStr
    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TTL_MIN: int = 60
    JWT_REFRESH_TTL_DAYS: int = 14

    POSTGRES_HOST: str = "pulse-db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "pulse"
    POSTGRES_USER: str = "pulse"
    POSTGRES_PASSWORD: SecretStr

    REDIS_URL: str = "redis://pulse-redis:6379/0"

    APP_BASE_URL: str = "https://pulse.tenayan.local"

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()
```

### Pattern 3: JWT auth — dual-mode (Bearer OR httpOnly cookie) with role dependency

```python
# backend/app/core/security.py
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str: return pwd_context.hash(plain)
def verify_password(plain: str, hashed: str) -> bool: return pwd_context.verify(plain, hashed)

def create_access_token(sub: str, roles: list[str], bidang_id: str | None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub, "roles": roles, "bidang_id": bidang_id,
        "iat": now, "exp": now + timedelta(minutes=settings.JWT_ACCESS_TTL_MIN),
        "typ": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY.get_secret_value(),
                      algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(sub: str, jti: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": sub, "jti": jti, "iat": now,
               "exp": now + timedelta(days=settings.JWT_REFRESH_TTL_DAYS),
               "typ": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY.get_secret_value(),
                      algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY.get_secret_value(),
                      algorithms=[settings.JWT_ALGORITHM])
```

```python
# backend/app/deps/auth.py
from fastapi import Cookie, Depends, Header, HTTPException, status
from app.core.security import decode_token
from jose import JWTError

async def current_user(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
) -> dict:
    """Accepts Bearer header OR httpOnly cookie. Returns decoded payload."""
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
        return payload
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

def require_role(*allowed: str):
    async def _checker(user: dict = Depends(current_user)) -> dict:
        if not set(user.get("roles", [])) & set(allowed):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user
    return _checker

# Usage in routers:
# @router.get("/templates", dependencies=[Depends(require_role("Admin"))])
# async def list_templates(...): ...
```

**Refresh-token rotation:** on `POST /api/v1/auth/refresh`, decode the refresh token, look up its `jti` in a Redis set `revoked_jti:{user_id}`, reject if revoked; otherwise issue new pair AND add the old `jti` to the revoked set with TTL = remaining refresh-token life. This kills replay.
[CITED: medium.com/@ancilartech/bulletproof-jwt-authentication-in-fastapi-a-complete-guide-2c5602a38b4f]

**Cookie set on login:**
```python
response.set_cookie(
    key="access_token", value=access_jwt, httponly=True, secure=True,
    samesite="lax", max_age=settings.JWT_ACCESS_TTL_MIN * 60, path="/api/v1",
)
response.set_cookie(
    key="refresh_token", value=refresh_jwt, httponly=True, secure=True,
    samesite="strict", max_age=settings.JWT_REFRESH_TTL_DAYS * 86400,
    path="/api/v1/auth/refresh",   # narrow path = CSRF surface minimisation
)
```
[CITED: blog.greeden.me/en/2025/10/14/a-beginners-guide-to-serious-security-design-with-fastapi — `samesite=strict` for refresh-token path]

### Pattern 4: React Router protected route with role gate (v6 layout pattern)

**Note:** CONSTR-stack-frontend locks "React Router v6". npm `react-router-dom` is now at v7.x; v6.30.x is the last v6 line and remains supported. Pin to `^6.30.0` to honor the constraint.

```tsx
// frontend/src/routes/ProtectedRoute.tsx
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/lib/auth-store";

type Role = "Admin" | "PIC" | "Asesor";

interface Props { allow?: Role[]; redirectTo?: string; }

export function ProtectedRoute({ allow, redirectTo = "/login" }: Props) {
  const { user, isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }
  if (allow && !allow.some(r => user?.roles.includes(r))) {
    // PIC redirected to /dashboard per success criterion #2
    return <Navigate to="/dashboard" replace />;
  }
  return <Outlet />;
}

// Usage in router config:
// <Route element={<ProtectedRoute allow={["Admin"]} />}>
//   <Route path="/master/*" element={<MasterLayout />} />
// </Route>
```
[CITED: dev.to/m_yousaf/implementing-role-based-access-control-in-react-18-with-react-router-v6-a-step-by-step-guide-1p8b]

### Pattern 5: Pulse Heartbeat animation with reduced-motion gate

```css
/* frontend/src/styles/pulse-heartbeat.css */
@keyframes pulse-heartbeat {
  0%, 60%, 100% { transform: scale(1);   opacity: 1;   box-shadow: 0 0 8px var(--sk-pln-yellow-glow); }
  30%           { transform: scale(1.15); opacity: 0.85; box-shadow: 0 0 16px var(--sk-pln-yellow-glow); }
}

.sk-led[data-state="on"] {
  animation: pulse-heartbeat 0.857s ease-in-out infinite;  /* 70 BPM ≈ 857ms */
}
.sk-led[data-state="alert"] { animation-duration: 0.5s; }   /* ~120 BPM */

@media (prefers-reduced-motion: reduce) {
  .sk-led[data-state="on"],
  .sk-led[data-state="alert"] { animation: none; opacity: 1; }
}
```

```tsx
// frontend/src/App.tsx — wrap whole app in MotionConfig
import { MotionConfig } from "motion/react";
export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      {/* setting "user" auto-disables transform/layout animation when OS reduced-motion is on */}
      <Router>{/* ... */}</Router>
    </MotionConfig>
  );
}
```
[CITED: motion.dev/docs/react-accessibility — `MotionConfig reducedMotion="user"`]
[CITED: framer.com/motion/use-reduced-motion/ — `useReducedMotion()` hook for finer-grained per-component control]

### Pattern 6: Nginx reverse-proxy config skeleton

```nginx
# nginx/conf.d/pulse.conf
upstream pulse_backend  { server pulse-backend:8000; }
upstream pulse_frontend { server pulse-frontend:80; }   # or remove and serve /usr/share/nginx/html

limit_req_zone $binary_remote_addr zone=api_zone:10m rate=60r/s;
limit_req_zone $binary_remote_addr zone=ai_zone:10m  rate=20r/m;

server {
    listen 80;
    server_name pulse.tenayan.local;

    add_header X-Frame-Options              "DENY"                                always;
    add_header X-Content-Type-Options       "nosniff"                             always;
    add_header X-XSS-Protection             "1; mode=block"                       always;
    add_header Strict-Transport-Security    "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy              "strict-origin-when-cross-origin"     always;

    client_max_body_size 25M;   # admin Excel import; reject anything bigger

    location /api/v1/ai/ {
        limit_req zone=ai_zone burst=5 nodelay;
        proxy_pass http://pulse_backend;
        include /etc/nginx/conf.d/_proxy.inc;
    }
    location /api/ {
        limit_req zone=api_zone burst=20 nodelay;
        proxy_pass http://pulse_backend;
        include /etc/nginx/conf.d/_proxy.inc;
    }
    location /ws/ {
        proxy_pass http://pulse_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }
    location / {
        proxy_pass http://pulse_frontend;
        include /etc/nginx/conf.d/_proxy.inc;
    }
}
```
[CITED: CONSTR-security-headers, CONSTR-rate-limits, CONSTR-websocket-endpoints]

### Anti-Patterns to Avoid
- **Sync DB calls inside async endpoints** — kills the event loop. All DB work goes through `AsyncSession`.
- **Storing JWT in `localStorage`** — vulnerable to XSS [CITED: blog.greeden.me/en/2025/10/14]; always httpOnly cookie or in-memory.
- **Setting cookie `samesite="none"` without `secure`** — browsers reject silently in dev, accept in prod, hard to debug.
- **CSS-only spinner for loading states** — DEC-003 mandates pulse-wave or heartbeat motion; no generic spinner.
- **Rolling your own password hash** — always passlib + bcrypt.
- **Putting `CREATE EXTENSION` in a `.sql` file in `docker-entrypoint-initdb.d/`** — known reliability problem [CITED: github.com/pgvector/pgvector/issues/355]; use `.sh`.
- **Calling Alembic migrations from `docker-entrypoint-initdb.d/`** — those run only at first init; migrations belong in the backend container's entrypoint or a one-shot `migrate` service.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom bcrypt loop / sha256 with salt | `passlib[bcrypt]` | Constant-time compare, parameter migration, well-audited. |
| JWT encode/decode | Custom HMAC | `python-jose[cryptography]` | Header validation, alg confusion attack guards, exp/nbf/iat handling. |
| Excel parsing | csv-by-hand from `.xlsx` | `openpyxl` (3.1.5) | Real `.xlsx` is a zipped XML bundle; openpyxl supports `read_only=True` for streaming. |
| UUID generation | Python `uuid4()` then INSERT | `uuid_generate_v4()` Postgres default (uuid-ossp) | Matches CONSTR-id-uuid; one source of truth; works for batch inserts. |
| DB migration runner | Hand-written SQL files + bash | Alembic + `--autogenerate` | Reversible, branch-aware, works with async engine via `connection.run_sync(...)`. |
| Reduced-motion detection | `window.matchMedia` listener inside components | framer-motion `MotionConfig reducedMotion="user"` + CSS `@media (prefers-reduced-motion)` | Library handles every motion component automatically. |
| Form validation | `useState` + manual rules | React Hook Form 7 + Zod 4 | Type-safe end-to-end; locked stack. |
| API client | `fetch` with retry/refresh wrappers per call | Axios 1.16 + interceptor (refresh on 401) | One central place for refresh-token rotation. |
| Toast/snackbar | Hand-rolled portal | Sonner 2.0 | Locked stack; ~3 kB; accessible. |
| Cron-in-Python | APScheduler inside the API | Sidecar container with `cron` | Kills app coupling; survives `pulse-backend` restart loops. |
| Backup retention | `find -mtime +30 -delete` written ad hoc | The same one-liner — but in the sidecar's cron entry, audited via `ls /var/backups/pulse` from a Make target | This is the one place hand-rolling is acceptable; just keep it in a single shell script in `nginx/backup/` or `infra/backup/`. |
| i18n (Phase 1) | `react-intl` / `react-i18next` | Plain TS lookup map | BI-only at launch; saves 22 kB; switch to `react-i18next` if EN ever requested. |

**Key insight:** The locked stack already provides battle-tested solutions for every cross-cutting concern in Phase 1. Custom code should be limited to: business-logic endpoints, the seed module, the skeuomorphic primitive components (SkLed/SkDial/SkLcdDigit), and the heartbeat keyframes. Everything else is configuration of existing libraries.

## Common Pitfalls

### Pitfall 1: `CREATE EXTENSION` from `.sql` initdb script silently fails for pgvector
**What goes wrong:** A `00-init.sql` placed in `/docker-entrypoint-initdb.d/` containing `CREATE EXTENSION IF NOT EXISTS vector;` runs but the extension is not loaded — the next Alembic migration fails with `type "vector" does not exist`.
**Why it happens:** Documented bug [CITED: github.com/pgvector/pgvector/issues/355]; superuser context differs between `psql -f` and the entrypoint script in some Postgres image flavors.
**How to avoid:** Use a shell script:
```bash
# pulse-db init: 00-extensions.sh
#!/bin/sh
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  CREATE EXTENSION IF NOT EXISTS "pgcrypto";
  CREATE EXTENSION IF NOT EXISTS "vector";
EOSQL
```
Mount via `volumes: - ./pulse-db/init:/docker-entrypoint-initdb.d:ro`.
**Warning signs:** First migration fails `psycopg/asyncpg: relation does not exist` or `type vector does not exist`.

### Pitfall 2: Alembic migrations running before the database is ready (race in Compose)
**What goes wrong:** `pulse-backend` boots and tries to migrate before pgvector init script finishes; Alembic crashes; backend container restart-loops.
**Why it happens:** `depends_on: condition: service_started` does NOT wait for healthcheck.
**How to avoid:** Two layers. (1) `db` healthcheck with `pg_isready -U pulse -d pulse`. (2) backend `depends_on: db: { condition: service_healthy }`. (3) backend entrypoint runs `alembic upgrade head` THEN `gunicorn`.
[CITED: oneuptime.com/blog/post/2026-01-23-docker-health-checks-effectively/view]

### Pitfall 3: `passlib` + `bcrypt 4.x/5.x` warning spam at startup
**What goes wrong:** passlib 1.7.4 logs `(trapped) error reading bcrypt version` every startup with bcrypt ≥ 4.x.
**Why it happens:** passlib reads `bcrypt.__about__` which was removed.
**How to avoid:** Pin exactly: `passlib[bcrypt]==1.7.4` AND `bcrypt==5.0.0` and add a startup filter or accept the warning. Alternative: use `argon2-cffi` (also recommended for new projects) — but stack ergonomics favor sticking with bcrypt for a Phase 1 system.

### Pitfall 4: SQLAlchemy 2.0 async sessions and `expire_on_commit`
**What goes wrong:** After `await session.commit()`, accessing any attribute on a returned ORM object triggers an implicit lazy-load, which crashes inside async context.
**Why it happens:** Default `expire_on_commit=True` invalidates instances after commit; lazy-load tries to use the now-invalid sync session.
**How to avoid:** ALWAYS create the sessionmaker with `expire_on_commit=False`. [CITED: docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession]

### Pitfall 5: React Router v7 vs v6 confusion
**What goes wrong:** `npm install react-router-dom` pulls v7.x by default in 2026; v7's `Route` API has subtle changes (e.g., default error boundary, `loader`/`action` are mainstream).
**Why it happens:** v7 was released as a "drop-in" but several APIs changed names.
**How to avoid:** Pin `"react-router-dom": "^6.30.0"` explicitly per CONSTR-stack-frontend. If/when migrating, do it as a phase task, not implicitly.

### Pitfall 6: shadcn/ui + Tailwind v4 — old `tailwindcss-animate` doesn't work
**What goes wrong:** Following an old shadcn tutorial wires `tailwindcss-animate` plugin; v4 silently ignores it; Dialog open/close animations don't render.
**Why it happens:** Tailwind v4 deprecated the plugin model; shadcn now ships with `tw-animate-css`.
**How to avoid:** Install `tw-animate-css` and add `@import "tw-animate-css";` to `src/index.css` after the Tailwind import. [CITED: ui.shadcn.com/docs/tailwind-v4]

### Pitfall 7: `framer-motion` package rename to `motion`
**What goes wrong:** Tutorials say `import { motion } from "framer-motion"`; npm package `framer-motion` still exists but is in maintenance mode.
**Why it happens:** Framer renamed to `motion` (the company). Both names install today, but `motion` is canonical going forward.
**How to avoid:** `npm install motion`; import via `import { motion } from "motion/react"`.

### Pitfall 8: CSRF on cookie-based auth endpoints
**What goes wrong:** Switching from Bearer to cookie auth introduces CSRF without anyone noticing; a malicious site can `<form action="https://pulse.tenayan.local/api/v1/...">` cause state changes.
**Why it happens:** Browsers automatically send cookies on cross-site form/image/script submissions.
**How to avoid:** (a) `samesite=lax` on access cookie, `samesite=strict` on refresh cookie; (b) require a `X-CSRF-Token` header (double-submit pattern) on all mutating endpoints when authenticated via cookie; (c) Nginx `add_header` does not help here — must be enforced in FastAPI dependency. [CITED: blog.greeden.me/en/2025/10/14]

### Pitfall 9: OpenAPI multipart-endpoint enforcement is easy to break by accident
**What goes wrong:** A future task adds a `File()` parameter on a logging endpoint "for diagnostics"; the no-upload contract is silently violated.
**Why it happens:** No automated check.
**How to avoid:** Add an integration test (see Validation Architecture below) that introspects the live OpenAPI schema and asserts the count of multipart endpoints.

### Pitfall 10: Excel import endpoint memory blow-up
**What goes wrong:** A user uploads a 200 MB `.xlsx`; openpyxl loads everything into memory; the worker OOMs and gunicorn kills it; the import is half-applied.
**Why it happens:** Default `openpyxl.load_workbook` is in-memory.
**How to avoid:** (a) Cap upload at Nginx (`client_max_body_size 25M`); (b) `load_workbook(filename, read_only=True, data_only=True)` to enable streaming; (c) wrap whole import in a single transaction with `SAVEPOINT` per row group so failures roll back cleanly; (d) idempotency key (`Idempotency-Key` header) recorded in a `konkin_import_log` table.

## Code Examples

### `/api/v1/health` endpoint with structured JSON

```python
# backend/app/routers/health.py
import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.deps.db import get_db
from app.deps.redis import get_redis
from app import __version__

router = APIRouter(tags=["health"])

@router.get("/health")
async def health(db: AsyncSession = Depends(get_db), r: Redis = Depends(get_redis)):
    async def check_db():
        try:
            await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=2.0)
            return "ok"
        except Exception: return "down"
    async def check_redis():
        try:
            await asyncio.wait_for(r.ping(), timeout=2.0)
            return "ok"
        except Exception: return "down"
    db_status, redis_status = await asyncio.gather(check_db(), check_redis())
    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    return {"status": overall, "db": db_status, "redis": redis_status, "version": __version__}
```

### Docker Compose healthcheck blocks

```yaml
services:
  pulse-db:
    image: pgvector/pgvector:pg16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  pulse-redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  pulse-backend:
    build: ./backend
    depends_on:
      pulse-db:    { condition: service_healthy }
      pulse-redis: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s
```
[CITED: oneuptime.com/blog/post/2026-01-23-docker-health-checks-effectively]

### Backup sidecar (cron + pg_dump)

```yaml
# docker-compose.yml fragment
  pulse-backup:
    image: postgres:16-alpine        # has pg_dump; pgvector image works too
    container_name: pulse-backup
    depends_on:
      pulse-db: { condition: service_healthy }
    environment:
      PGHOST: pulse-db
      PGUSER: ${POSTGRES_USER}
      PGPASSWORD: ${POSTGRES_PASSWORD}
      PGDATABASE: ${POSTGRES_DB}
      BACKUP_DIR: /backups
      RETAIN_DAYS: "30"
    volumes:
      - ./infra/backup/scripts:/scripts:ro
      - pulse_backups:/backups
    entrypoint: ["/bin/sh", "/scripts/run-cron.sh"]
    networks: [pulse-net]
volumes:
  pulse_backups:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/backups/pulse      # CONSTR-env-secrets BACKUP_DIR
```

```bash
# infra/backup/scripts/backup.sh
#!/bin/sh
set -eu
TS=$(date -u +%Y%m%dT%H%M%SZ)
OUT="${BACKUP_DIR}/pulse-${TS}.sql.gz"
pg_dump --no-owner --clean --if-exists | gzip > "${OUT}"
find "${BACKUP_DIR}" -name 'pulse-*.sql.gz' -mtime "+${RETAIN_DAYS}" -delete
echo "[backup] ${OUT}"
```

```bash
# infra/backup/scripts/restore.sh   (CONSTR-backup acceptance: pipe into psql)
#!/bin/sh
set -eu
[ -z "${1:-}" ] && { echo "Usage: $0 <backup-file>"; exit 2; }
gunzip -c "$1" | psql -v ON_ERROR_STOP=1
```

```bash
# infra/backup/scripts/run-cron.sh — entry point for sidecar
#!/bin/sh
echo "0 2 * * * /scripts/backup.sh >> /backups/backup.log 2>&1" > /etc/crontabs/root
echo "0 3 * * 0 rsync -a /backups/ ${NAS_DEST:-/mnt/nas/pulse-backups}/ >> /backups/rsync.log 2>&1" >> /etc/crontabs/root
crond -f -L /dev/stdout
```
[CITED: serversinc.io/blog/automated-postgresql-backups-in-docker-complete-guide-with-pg_dump, github.com/mentos1386/docker-postgres-cron-backup — pattern reference]

### OpenAPI multipart-endpoint policy test

```python
# backend/tests/test_no_upload_policy.py
from fastapi.testclient import TestClient
from app.main import app

ALLOWED_MULTIPART = {"/api/v1/konkin/templates/{template_id}/import-from-excel"}

def test_only_one_multipart_endpoint():
    schema = app.openapi()
    multipart_paths = set()
    for path, methods in schema["paths"].items():
        for verb, op in methods.items():
            req_body = op.get("requestBody", {})
            content = req_body.get("content", {}) if req_body else {}
            if "multipart/form-data" in content:
                multipart_paths.add(path)
    assert multipart_paths == ALLOWED_MULTIPART, (
        f"Unexpected multipart endpoints: {multipart_paths - ALLOWED_MULTIPART}; "
        f"missing expected: {ALLOWED_MULTIPART - multipart_paths}"
    )

def test_link_eviden_is_url_only():
    schema = app.openapi()
    # Walk components.schemas; any property named link_eviden must be format=uri or pattern URL
    components = schema.get("components", {}).get("schemas", {})
    offenders = []
    for name, s in components.items():
        for prop_name, prop in (s.get("properties") or {}).items():
            if prop_name == "link_eviden":
                if prop.get("format") != "uri":
                    offenders.append(f"{name}.{prop_name}")
    assert not offenders, f"link_eviden must be format=uri (HttpUrl) on: {offenders}"
```

### Excel import (streaming, idempotent)

```python
# backend/app/routers/master_konkin.py (excerpt)
from fastapi import APIRouter, Depends, File, Header, UploadFile, HTTPException, status
from openpyxl import load_workbook
from io import BytesIO

router = APIRouter(prefix="/konkin", tags=["master-konkin"])

@router.post(
    "/templates/{template_id}/import-from-excel",
    status_code=201,
    dependencies=[Depends(require_role("Admin"))],
)
async def import_from_excel(
    template_id: UUID,
    file: UploadFile = File(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    }:
        raise HTTPException(415, "Only .xlsx accepted")

    # Idempotency: short-circuit if same key already applied
    if idempotency_key:
        existing = await db.scalar(select(KonkinImportLog).where(
            KonkinImportLog.idempotency_key == idempotency_key))
        if existing:
            return {"data": {"status": "already_applied", "log_id": str(existing.id)}}

    raw = await file.read()
    wb = load_workbook(BytesIO(raw), read_only=True, data_only=True)
    # ... iterate; insert under SAVEPOINT per sheet ...
    await db.commit()
    return {"data": {"status": "imported", "rows": n}}
```
[CITED: asiones.hashnode.dev/fastapi-receive-a-xlsx-file-and-read-it]

### Simple i18n lookup (Phase 1)

```ts
// frontend/src/lib/i18n.ts
const id = {
  app: { name: "PULSE", tagline: "Denyut Kinerja Pembangkit, Real-Time." },
  login: { username: "Pengguna", password: "Kata Sandi", submit: "Masuk",
           wrong: "Pengguna atau kata sandi salah." },
  nav: { master: "Master Data", dashboard: "Dasbor", logout: "Keluar" },
  master: { konkin: "Template Konkin 2026", bidang: "Master Bidang",
            stream: "Maturity Level Stream" },
  // ...
} as const;

export type LocalePath = string;   // dot-path
export const t = (path: LocalePath): string =>
  path.split(".").reduce<any>((o, k) => (o ?? {})[k], id) ?? path;

// Usage: <h1>{t("login.submit")}</h1>
```

When EN translation is needed (post-Phase 1), this file becomes:
```ts
const dicts = { id, en } as const;
let current: keyof typeof dicts = "id";
export const setLocale = (l: keyof typeof dicts) => { current = l; };
export const t = (path: string) =>
  path.split(".").reduce<any>((o, k) => (o ?? {})[k], dicts[current]) ?? path;
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `BaseSettings` from `pydantic` | `pydantic_settings.BaseSettings` | Pydantic v2 (2023) | Already locked stack — must use `pydantic-settings`. |
| Tailwind v3 `tailwind.config.js` + `@tailwind base; components; utilities;` | Tailwind v4 `@import "tailwindcss"; @theme inline { ... }` in CSS, `@tailwindcss/vite` plugin | Tailwind 4.0 (Jan 2025) | Project gets v4 by default; design tokens live in CSS not JS. |
| `tailwindcss-animate` plugin | `tw-animate-css` package | shadcn/ui v4 update (2025) | New shadcn install path. |
| `framer-motion` package name | `motion` package | 2024 rename | Both work, prefer `motion`. |
| React Router v6 `<Routes>` + `useRoutes` | v6 still current; v7 released as gradual upgrade with new data APIs | v7 release (2024-2025) | Stack pins v6; pin `^6.30.0`. |
| Sync SQLAlchemy 1.4 + psycopg2 | Async SQLAlchemy 2.0 + asyncpg | SQLA 2.0 GA (2023) | Locked. |
| `pyjwt` | `python-jose[cryptography]` | Both maintained; jose preferred for FastAPI ecosystem | Choice; we pick jose for richer alg support. |

**Deprecated/outdated:**
- `pydantic.BaseSettings` (v1 import path) — moved to `pydantic-settings`.
- `tailwindcss-animate` for v4 — use `tw-animate-css`.
- `tailwind.config.js` `theme.extend` for design tokens in v4 — tokens go to `@theme inline` in CSS.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Node 20-alpine is the right base for the frontend build stage. | Standard Stack — Infrastructure | Low — easily swapped to 22-alpine; doesn't affect runtime since output is static files. |
| A2 | TypeScript 5.9 is the right pin (npm view returned `4.3.0` for the `typescript` core package which is misleading; actual `typescript` package is at 5.x). | Standard Stack — Frontend | Low — TS minor versions are backward compatible within major. |
| A3 | `pulse-frontend` ships as a separate container that Nginx proxies to, vs. being baked into the Nginx image. Both work; the separate-container choice mirrors the 6-service compose listed in CONSTR-network-naming. | Architecture — System Diagram | Medium — if the project chooses single-image-with-baked-static, the `pulse-frontend` container disappears. Either way, network naming holds. |
| A4 | `samesite=strict` on the refresh cookie is acceptable for the SPA flow (the only issuer of refresh requests is the same-origin SPA via Axios). | Pattern 3 — Cookie set | Low — strict is correct for same-origin SPAs; would need `lax` if cross-origin OAuth flows existed (none in scope). |
| A5 | Idempotency for Excel import is enforced via an `Idempotency-Key` header + `konkin_import_log` table. The data model in CONSTR-data-model-core-tables does not list this table; it is a recommended addition. | Code Examples — Excel import | Medium — planner should add `konkin_import_log` to migrations as part of Phase 1 task list, OR drop idempotency and document re-runnable seed-style behavior. **Needs user confirmation.** |
| A6 | `bcrypt 5.0.0` works cleanly with `passlib 1.7.4` (passlib has not had a release since 2020). The startup warning is cosmetic but will appear. | Pitfall 3 | Medium — if the warning is unacceptable, recommend switching hash backend to `argon2-cffi` (also a single-line passlib registration). **Needs user confirmation.** |
| A7 | NAS rsync destination is mountable into the `pulse-backup` container (e.g., `/mnt/nas/pulse-backups` exists on the host and is bind-mounted). CONSTR-backup mandates weekly rsync but doesn't specify how the NAS is reachable. | Code Examples — Backup sidecar | High — if the NAS is reachable only from the host network and not from within Docker, the sidecar approach for rsync breaks; falls back to host cron for rsync only. **Needs user confirmation.** |
| A8 | The Phase 1 deliverable does NOT include configuring SSL — DEC-011 explicitly defers SSL to deploy time. Nginx config example uses `listen 80` only. | Pattern 6 — Nginx | Low — matches CONTEXT.md Deferred Ideas. |
| A9 | i18n lookup map is enough for Phase 1; defer `react-i18next` to a later phase. CONSTR-i18n-default says "react-intl or simple lookup" — this satisfies "simple lookup". | Don't Hand-Roll, Code Examples | Low — purely a UX-language scope decision; reversible. |
| A10 | The `make` target convention (`make up`, `make seed`, `make migrate`, `make backup`, `make restore`, `make test`) is the right developer ergonomics. CONTEXT.md mentions `make seed` but does not list a full Makefile contract. | Architecture — Project Structure | Low — Makefile is purely DX; planner is free to choose `just`/`task`/scripts/. |

## Open Questions (RESOLVED 2026-05-11)

All five recommendations were ADOPTED and locked into `01-CONTEXT.md`. No items remain open. (Per plan-checker B-08 — gate now satisfied.)

1. **Nginx static-asset serving — RESOLVED → adopted recommendation.** Separate `pulse-frontend` container serves the Vite build; `pulse-nginx` reverse-proxies to it. Locked in CONTEXT.md "Claude's Discretion" section.

2. **Idempotency table for Excel import — RESOLVED → adopted recommendation.** `konkin_import_log` table is created in the Phase-1 master-data migration. Locked in CONTEXT.md "Data Model" section.

3. **First admin user — RESOLVED → adopted recommendation.** `python -m app.seed` reads `INITIAL_ADMIN_EMAIL` + `INITIAL_ADMIN_PASSWORD` from `.env`, creates one `admin_unit` user idempotently. Locked in CONTEXT.md "Auth" section.

4. **`make seed` invocation — RESOLVED → adopted recommendation.** `docker compose exec pulse-backend python -m app.seed` for dev. Locked in CONTEXT.md "Claude's Discretion" section.

5. **OpenAPI schema introspection test — RESOLVED → adopted recommendation.** In-process `app.openapi()` test asserts EXACTLY one multipart endpoint AND that it is `POST /konkin/templates/{id}/import-from-excel`. Locked in CONTEXT.md "API" section.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker / Docker Compose | All compose services | ✗ (not on `PATH` in current shell) | — | Required for execution; planner must install Docker Desktop on Windows host before compose-up tasks. |
| Python | Backend dev shell | ✓ | 3.13.13 (host) | Backend container uses 3.11-slim; host Python is irrelevant for runtime, only for local quick scripts. |
| Node | Frontend dev shell | ✓ | 25.8.1 (host) | Frontend container uses node:20-alpine; host Node version > 20, fine for local scripts. |
| `make` | Makefile DX | ✗ (not on PowerShell `PATH`) | — | Use Git Bash (which is present), or replace Makefile with `package.json` scripts + `pyproject` scripts. |
| `psql` | Local manual DB ops + restore script (host-side) | ✓ | 17.2 | psql 17 client connects to PG 16 server fine. |
| `git` | Repo ops | ✓ | 2.39.1 | — |
| Curl | Healthcheck `CMD` inside backend container | implicit (image-level) | — | Use Python `http.client` if curl absent in slim image. |

**Missing dependencies with no fallback:**
- **Docker / Docker Compose** — entire phase delivery depends on this. Phase 1 cannot reach success criteria 1, 4, 5, 6 without it. **Planner must include "verify Docker installed" as the very first task or assume operator has it.**

**Missing dependencies with fallback:**
- **GNU Make** — substitute with shell scripts under `scripts/` or use Git Bash where it ships. Or pivot to `package.json` scripts driven by `npm run` since Node is present.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Backend framework | pytest 9.0.3 + pytest-asyncio 1.3.0 + httpx 0.28.1 (TestClient) |
| Frontend framework | Vitest 4.1.5 + @testing-library/react 16.3.2 |
| Backend config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) — Wave 0 |
| Frontend config file | `frontend/vite.config.ts` `test: {}` block + `frontend/src/test/setup.ts` — Wave 0 |
| Quick run command (backend) | `docker compose exec pulse-backend pytest -x --no-header -q` |
| Quick run command (frontend) | `cd frontend && npm run test -- --run --reporter=basic` |
| Full suite command | `make test` (runs both backend pytest and frontend vitest) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| REQ-auth-jwt | Login issues access+refresh, refresh rotates jti | unit + integration | `pytest backend/tests/test_auth.py -x` | ❌ Wave 0 |
| REQ-user-roles | Admin / PIC / Asesor exist, password hashing roundtrip | unit | `pytest backend/tests/test_user_roles.py -x` | ❌ Wave 0 |
| REQ-route-guards | `/master/*` returns 403 for PIC; redirects to /dashboard for UI | integration (backend 403) + frontend (Outlet redirect) | `pytest backend/tests/test_rbac.py -x && cd frontend && vitest run src/routes/ProtectedRoute.test.tsx` | ❌ Wave 0 |
| REQ-konkin-template-crud | CRUD on templates as Admin | integration | `pytest backend/tests/test_master_konkin.py -x` | ❌ Wave 0 |
| REQ-dynamic-ml-schema | `ml_stream.structure JSONB` accepts arbitrary schema, GIN-queryable | integration | `pytest backend/tests/test_ml_stream.py::test_jsonb_query -x` | ❌ Wave 0 |
| REQ-bidang-master | Bidang CRUD + seeded list | integration | `pytest backend/tests/test_bidang.py -x` | ❌ Wave 0 |
| REQ-frontend-stack | Vite build succeeds; bundle <500 KB initial | smoke | `cd frontend && npm run build` | ❌ Wave 0 |
| REQ-backend-stack | gunicorn boots, /docs reachable | smoke | `docker compose up -d pulse-backend && curl localhost:8000/api/v1/health` | ❌ Wave 0 |
| REQ-docker-compose-deploy | All 6 services healthy | manual + smoke | `docker compose up -d --wait` | ❌ Wave 0 |
| REQ-nginx-config | Port 3399 routes /api → backend, / → frontend, security headers present | integration | `pytest backend/tests/test_nginx_proxy.py -x` (curl-style hits via httpx) | ❌ Wave 0 |
| REQ-pulse-branding | grep -ri "siskonkin" repo returns zero hits | smoke (CI grep) | `! grep -ri --exclude-dir=.git --exclude-dir=node_modules siskonkin .` | ❌ Wave 0 |
| REQ-pulse-heartbeat-animation | `.sk-led[data-state="on"]` has `pulse-heartbeat` keyframe | unit (frontend) | `vitest run src/components/skeuomorphic/SkLed.test.tsx` | ❌ Wave 0 |
| REQ-skeuomorphic-design-system | Design tokens present in `:root`, AA contrast on key combos | unit + manual | `vitest run src/styles/tokens.test.ts` | ❌ Wave 0 |
| REQ-health-checks | `/api/v1/health` returns 200 with `{status, db, redis, version}` | integration | `pytest backend/tests/test_health.py -x` | ❌ Wave 0 |
| REQ-no-evidence-upload | OpenAPI has exactly one multipart endpoint; `link_eviden` fields are URI | integration | `pytest backend/tests/test_no_upload_policy.py -x` | ❌ Wave 0 |
| REQ-backup-restore | backup.sh produces a `.sql.gz`; restore.sh roundtrip succeeds | manual + integration | `make backup && make restore FILE=…` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/<touched>.py -x` and/or `vitest run <touched>.test.tsx` — under 30s.
- **Per wave merge:** `make test` — full pytest + full vitest.
- **Phase gate:** Full suite green; `docker compose up -d --wait` succeeds; manual restore runbook executed once.

### Wave 0 Gaps
- [ ] `backend/pyproject.toml` — pytest config + dependencies.
- [ ] `backend/tests/conftest.py` — async TestClient + transactional db fixture (Postgres rollback per test).
- [ ] `backend/tests/test_no_upload_policy.py` — OpenAPI introspection (template above).
- [ ] `backend/tests/test_health.py` — health endpoint shape.
- [ ] `backend/tests/test_auth.py` — login + refresh + role 403.
- [ ] `frontend/vitest.config.ts` (or `vite.config.ts` test block) + `frontend/src/test/setup.ts`.
- [ ] `frontend/src/routes/ProtectedRoute.test.tsx`.
- [ ] CI grep guard for `siskonkin` zero-hit assertion (just a one-liner shell test).
- [ ] Framework install: `cd backend && pip install -e ".[dev]"` and `cd frontend && npm install` — both Wave 0.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | yes | passlib bcrypt for password storage; JWT via `python-jose`; refresh-token rotation w/ jti revocation in Redis. |
| V3 Session Management | yes | httpOnly + secure + samesite cookies; access TTL 60min, refresh TTL 14 days; logout revokes refresh jti. |
| V4 Access Control | yes | Role list in JWT (`roles`); per-route `Depends(require_role(...))`; bidang scoping via `bidang_id` claim filtered server-side. |
| V5 Input Validation | yes | Pydantic v2 schemas on every endpoint; `HttpUrl` for `link_eviden` (enforced by Pydantic + asserted by no-upload test). |
| V6 Cryptography | yes | bcrypt for passwords; HS256 JWT with `JWT_SECRET_KEY` from env (≥32 chars); never hand-rolled. |
| V7 Error Handling & Logging | yes | Structured JSON logs to stdout; never log secrets/JWT/passwords; FastAPI exception handlers return `{error: {code, message}}`. |
| V8 Data Protection | partial | No file uploads (DEC-010); DB encryption at rest deferred to deploy/Phase 6. |
| V9 Communication | yes (Phase 1 deferred) | Nginx security headers; HSTS; TLS deferred to deploy time per DEC-011. |
| V10 Malicious Code | yes | Dependency pinning; `pip-audit` / `npm audit` recommended in CI (Phase 6). |
| V13 API & Web Service | yes | Rate-limit zones in Nginx (`api 60r/s`, `ai 20r/m`); CSRF for cookie-based mutating endpoints; OpenAPI under auth in prod. |

### Known Threat Patterns for {FastAPI + React + Postgres + Nginx}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection | Tampering | SQLAlchemy parameterized queries (default); never string-concatenate SQL. |
| XSS via reflected error | Tampering / Information disclosure | React auto-escapes; never `dangerouslySetInnerHTML` from server data; CSP via Nginx (deferred to Phase 6). |
| CSRF on cookie auth | Tampering | `samesite=strict` on refresh; `samesite=lax` on access; double-submit `X-CSRF-Token` on mutating endpoints when cookie auth in use. |
| JWT alg confusion (`alg: none` / `alg: HS` with public key) | Spoofing | `jwt.decode(..., algorithms=["HS256"])` — explicit allow-list. |
| Token theft via XSS | Spoofing | httpOnly cookie storage (no JS access); short access TTL; refresh rotation. |
| Brute-force login | Repudiation / Spoofing | Rate-limit `/auth/login` at Nginx (e.g. 5/min/IP) + backend lockout after N failures. |
| Mass assignment | Tampering | Pydantic schemas declare exactly the input fields; never bind unfiltered request body to ORM model. |
| ReDoS via overly permissive regex | DoS | Pydantic `HttpUrl` is safe; avoid hand-rolled regex on user input. |
| Path traversal (Excel import) | Tampering | Don't write uploaded file to disk; parse from BytesIO. |
| Privileged endpoint exposed without role check | Elevation of Privilege | Every router file's mutating endpoints carry `dependencies=[Depends(require_role(...))]`; checked by code review + smoke test. |
| Postgres exposed | Information disclosure | `pulse-db` has no `ports:` in compose; only on `pulse-net`. |
| Backup file disclosure | Information disclosure | `BACKUP_DIR` mode 0700; backup files mode 0600; rsync target with restricted perms. |
| Secrets in repo | Information disclosure | `.env` gitignored; `.env.example` only; CI grep for `JWT_SECRET_KEY=` patterns. |

## Project Constraints (from CLAUDE.md)

No `CLAUDE.md` was found at `C:/Users/ANUNNAKI/Projects/PULSE/CLAUDE.md`. No project-specific Claude Code directives apply beyond what is captured in `.planning/intel/` and `01-CONTEXT.md`.

## Sources

### Primary (HIGH confidence — verified in this session)
- PyPI JSON API (fetched 2026-05-11) — fastapi 0.136.1, sqlalchemy 2.0.49, asyncpg 0.31.0, alembic 1.18.4, pydantic 2.13.4, pydantic-settings 2.14.1, python-jose 3.5.0, passlib 1.7.4, bcrypt 5.0.0, openpyxl 3.1.5, gunicorn 26.0.0, uvicorn 0.46.0, pytest 9.0.3, pytest-asyncio 1.3.0, httpx 0.28.1, authx 1.6.0, fastapi-users 15.0.5.
- npm registry (`npm view`) — @tanstack/react-query 5.100.9, zustand 5.0.13, react-hook-form 7.75.0, zod 4.4.3, react-router-dom 7.15.0, tailwindcss 4.3.0, framer-motion 12.38.0, sonner 2.0.7, axios 1.16.0, vitest 4.1.5, @testing-library/react 16.3.2.
- Docker Hub `hub.docker.com/v2/repositories/pgvector/pgvector/tags` (fetched 2026-05-11) — `pg16` and `0.8.2-pg16` tags confirmed available.
- `.planning/intel/constraints.md` and `.planning/intel/decisions.md` — locked stack and naming.

### Secondary (MEDIUM confidence — official docs / multi-sourced)
- [SQLAlchemy 2.0 async docs — `expire_on_commit=False` requirement](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI OAuth2 + JWT tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [shadcn/ui Tailwind v4 docs](https://ui.shadcn.com/docs/tailwind-v4)
- [Motion (framer-motion) accessibility — MotionConfig reducedMotion="user"](https://motion.dev/docs/react-accessibility)
- [Motion useReducedMotion hook reference](https://www.framer.com/motion/use-reduced-motion/)
- [pgvector issue #355 — CREATE EXTENSION reliability in initdb .sql](https://github.com/pgvector/pgvector/issues/355)
- [ServersInc — Automated PostgreSQL Backups in Docker](https://serversinc.io/blog/automated-postgresql-backups-in-docker-complete-guide-with-pg-dump/)
- [Greeden blog — FastAPI security design (cookies, SameSite, CSRF)](https://blog.greeden.me/en/2025/10/14/a-beginners-guide-to-serious-security-design-with-fastapi-authentication-authorization-jwt-oauth2-cookie-sessions-rbac-scopes-csrf-protection-and-real-world-pitfalls/)
- [TestDriven.io — FastAPI JWT authentication](https://testdriven.io/blog/fastapi-jwt-auth/)
- [Robin Wieruch — React Router private routes](https://www.robinwieruch.de/react-router-private-routes/)
- [DEV.to — RBAC in React 18 with React Router v6](https://dev.to/m_yousaf/implementing-role-based-access-control-in-react-18-with-react-router-v6-a-step-by-step-guide-1p8b)
- [OneUptime — Docker health checks effectively (2026)](https://oneuptime.com/blog/post/2026-01-23-docker-health-checks-effectively/view)
- [bundlephobia — react-i18next bundle size](https://bundlephobia.com/package/react-i18next)
- [i18nexus — react-i18next vs react-intl comparison](https://i18nexus.com/posts/comparing-react-i18next-and-react-intl)
- [vikramgulia/fastapi-react — reference monorepo layout](https://github.com/vikramgulia/fastapi-react/blob/master/docker-compose.yml)
- [Asiones — FastAPI receive xlsx file (openpyxl pattern)](https://asiones.hashnode.dev/fastapi-receive-a-xlsx-file-and-read-it)

### Tertiary (LOW confidence — single-source / blog-grade)
- [Markaicode — Deploy FastAPI to Production with Docker Compose 2026](https://markaicode.com/how-to-deploy-fastapi/)
- [Medium — Bulletproof JWT Authentication in FastAPI](https://medium.com/@ancilartech/bulletproof-jwt-authentication-in-fastapi-a-complete-guide-2c5602a38b4f)
- [DEV.to — Async Database Sessions in FastAPI with SQLAlchemy](https://dev.to/akarshan/asynchronous-database-sessions-in-fastapi-with-sqlalchemy-1o7e)
- [Medium — FastAPI + SQLAlchemy 2.0 Modern Async Database Patterns](https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308)
- [github.com/mentos1386/docker-postgres-cron-backup — pattern reference](https://github.com/mentos1386/docker-postgres-cron-backup)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every package version verified against PyPI/npm/Docker Hub on 2026-05-11.
- Architecture: HIGH — patterns are canonical for the stack and cross-referenced with official docs.
- Pitfalls: MEDIUM-HIGH — pgvector init.sql bug verified via GitHub issue tracker; passlib/bcrypt warning is a known nuisance reproducible locally; CSRF/cookie advice reflects current FastAPI consensus.
- Security domain: MEDIUM — ASVS mapping is complete for Phase 1 surface area; specific bcrypt cost factor and rate-limit thresholds left for the planner to size.
- I18n recommendation: MEDIUM — bundle size argument is hard-numerical; the "user only sees BI in Phase 1" assumption is project-specific (CONSTR-i18n-default supports both directions).

**Research date:** 2026-05-11
**Valid until:** 2026-06-10 (~30 days; FastAPI/SQLAlchemy/React stack is stable; re-verify version pins at Phase 2 kickoff).
