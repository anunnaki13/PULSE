---
phase: 01-foundation-master-data-auth
plan: 02
type: execute
wave: 2
depends_on: [01]
files_modified:
  - docker-compose.yml
  - docker-compose.override.yml
  - infra/db/init/00-extensions.sh
  - infra/backup/scripts/backup.sh
  - infra/backup/scripts/restore.sh
  - infra/backup/scripts/run-cron.sh
  - infra/backup/Dockerfile
  - nginx/Dockerfile
  - nginx/nginx.conf
  - nginx/conf.d/pulse.conf
  - nginx/conf.d/_proxy.inc
  - backend/Dockerfile
  - backend/entrypoint.sh
  - frontend/Dockerfile
  - frontend/nginx.conf
autonomous: true
requirements:
  - REQ-docker-compose-deploy
  - REQ-nginx-config
  - REQ-backup-restore
  - REQ-no-evidence-upload
must_haves:
  truths:
    - "An operator can run `make up` (or `./scripts/dev.ps1 up`) and the six containers reach `healthy` state without manual intervention"
    - "Nginx publishes ONLY host port 3399 (HTTP) — Postgres 5432 is NOT exposed publicly"
    - "Postgres extensions `uuid-ossp`, `pgcrypto`, and `vector` are installed at first DB init via a shell script (not .sql, per pgvector issue #355)"
    - "Nginx serves all six locked security headers and enforces `client_max_body_size 25M` (caps Excel-import payload — REQ-no-evidence-upload defense)"
    - "Nginx defines rate-limit zones `api 60r/s` and `ai 20r/m` (REQ-nginx-config; the AI zone is wired now to avoid retro-fits in Phase 5)"
    - "Backup sidecar runs `pg_dump | gzip` at 02:00 daily and rsync to NAS at 03:00 Sunday via internal cron"
    - "A 30-day retention sweep runs after every backup"
  artifacts:
    - path: "docker-compose.yml"
      provides: "6-service compose: pulse-db, pulse-redis, pulse-backend, pulse-frontend, pulse-nginx, pulse-backup on network `pulse-net`"
      contains: "pulse-net"
    - path: "infra/db/init/00-extensions.sh"
      provides: "Idempotent CREATE EXTENSION for uuid-ossp, pgcrypto, vector — shell script per pgvector#355"
      contains: "CREATE EXTENSION IF NOT EXISTS \"vector\""
    - path: "nginx/conf.d/pulse.conf"
      provides: "Reverse-proxy routing /api /ws / + security headers + rate-limit zones"
      contains: "limit_req_zone"
    - path: "infra/backup/scripts/backup.sh"
      provides: "pg_dump → gzip → BACKUP_DIR with 30-day prune"
      contains: "pg_dump"
    - path: "infra/backup/scripts/restore.sh"
      provides: "gunzip | psql restore path"
      contains: "psql"
    - path: "backend/Dockerfile"
      provides: "Python 3.11-slim multi-stage backend image"
      contains: "python:3.11-slim"
    - path: "frontend/Dockerfile"
      provides: "Node 20-alpine build → nginx-alpine static serve"
      contains: "node:20-alpine"
  key_links:
    - from: "docker-compose.yml"
      to: "infra/db/init/00-extensions.sh"
      via: "Volume mount to /docker-entrypoint-initdb.d"
      pattern: "docker-entrypoint-initdb\\.d"
    - from: "docker-compose.yml"
      to: "infra/backup/scripts/run-cron.sh"
      via: "pulse-backup entrypoint"
      pattern: "run-cron\\.sh"
    - from: "nginx/conf.d/pulse.conf"
      to: "pulse-backend:8000"
      via: "upstream proxy_pass"
      pattern: "proxy_pass http://pulse_backend"
---

## Revision History

- **Iteration 1 (initial):** Created 6-service compose + Nginx + backup sidecar.
- **Iteration 2 (this revision):**
  - **W-08 fix:** Replace `busybox-suid` with `dcron` in the backup sidecar Dockerfile for Alpine cron stability (CONTEXT.md Claude Discretion).
  - **B-06 fix (verify hardening):** Task 2 verify now runs `docker compose build pulse-backup` to actually exercise the Dockerfile, in addition to syntax checks.
  - No functional cron-schedule change (still daily 02:00 + Sunday 03:00 rsync).

<objective>
Stand up the Docker Compose infrastructure: all six containers (DEC-002 names), volume mounts, healthchecks, network, security-header-and-rate-limited Nginx reverse proxy, pgvector-ready Postgres with shell-script extension init, Redis 7 with 256mb LRU, and a backup sidecar with internal cron.

Purpose: This plan delivers the deployment substrate (REQ-docker-compose-deploy, REQ-nginx-config, REQ-backup-restore). Plans 03/04 (backend/frontend) build images that this compose file will run; Plan 07 will execute the actual `compose up --wait` smoke. Runs in parallel with Plan 03 (backend skeleton) and Plan 04 (frontend skeleton) — zero file overlap (only `backend/Dockerfile` is created here; the rest of `backend/` is owned by Plan 03; and `frontend/Dockerfile` here, rest of `frontend/` owned by Plan 04).
Output: docker-compose.yml + override + nginx configs + Dockerfiles + backup sidecar scripts.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/01-foundation-master-data-auth/01-CONTEXT.md
@.planning/phases/01-foundation-master-data-auth/01-RESEARCH.md
@.planning/phases/01-foundation-master-data-auth/01-01-SUMMARY.md

<interfaces>
<!-- DEC-002 locked identifiers (every service in compose must use exactly these names) -->
- Network: `pulse-net`
- Services: `pulse-db`, `pulse-redis`, `pulse-backend`, `pulse-frontend`, `pulse-nginx`, `pulse-backup`
- DB image: `pgvector/pgvector:pg16` (RESEARCH.md verified Docker Hub tag)
- DB env vars driven from .env (Plan 01): POSTGRES_DB=pulse, POSTGRES_USER=pulse, POSTGRES_PASSWORD=...
- Backup volume: bind-mount `${BACKUP_DIR:-/var/backups/pulse}` → `/backups` in pulse-backup
- Backend listens internally on :8000 (gunicorn 4 × UvicornWorker — wired in Plan 03)
- Frontend listens internally on :80 (its own Nginx-alpine serving /usr/share/nginx/html)
- Host-published port: 3399 → pulse-nginx:80 (CONSTR-host-port)
- Healthcheck contracts (Plans 03+04 must satisfy these endpoints):
    - pulse-db: `pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB`
    - pulse-redis: `redis-cli ping`
    - pulse-backend: `curl -f http://localhost:8000/api/v1/health`
    - pulse-frontend: `wget -qO- http://localhost/ | grep -q PULSE` (or simpler: `wget --spider http://localhost/`)
    - pulse-nginx: `wget --spider http://localhost/api/v1/health`
- Rate-limit zones: api 60r/s burst=20, ai 20r/m burst=5 (REQ-rate-limiting-general scope-relevant subset wired now)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Compose file + Dockerfiles for db, redis, backend, frontend</name>
  <files>
    docker-compose.yml,
    docker-compose.override.yml,
    infra/db/init/00-extensions.sh,
    backend/Dockerfile,
    backend/entrypoint.sh,
    frontend/Dockerfile,
    frontend/nginx.conf
  </files>
  <action>
    1. `docker-compose.yml` — six services on network `pulse-net` (DEC-002). Start with five services in this task (pulse-db, pulse-redis, pulse-backend, pulse-frontend, pulse-nginx); pulse-backup is added in Task 2 of this plan.

       Key clauses (full file in completion artifact):
       - `version` line omitted (Compose v2 ignores it).
       - `pulse-db`: image `pgvector/pgvector:pg16`; environment from `${POSTGRES_*}`; volumes `pulse_db_data:/var/lib/postgresql/data` AND `./infra/db/init:/docker-entrypoint-initdb.d:ro`; **NO `ports:`** (CONSTR-host-port forbids public Postgres); healthcheck `pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB` (interval 10s, timeout 5s, retries 5, start_period 30s).
       - `pulse-redis`: image `redis:7-alpine`; command `redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru`; healthcheck `redis-cli ping`.
       - `pulse-backend`: `build: ./backend`; env_file `.env`; depends_on db + redis with `condition: service_healthy` (RESEARCH.md Pitfall #2); healthcheck via curl to `/api/v1/health` (start_period 40s).
       - `pulse-frontend`: `build: ./frontend`; depends_on pulse-backend (started, not necessarily healthy); healthcheck wget spider on `:80`.
       - `pulse-nginx`: `build: ./nginx`; ports: `${APP_HOST_PORT:-3399}:80`; depends_on pulse-backend (healthy) + pulse-frontend (started); healthcheck wget spider on `http://localhost/api/v1/health`.
       - `networks: pulse-net: { driver: bridge, name: pulse-net }` (explicit name to match DEC-002).
       - `volumes: pulse_db_data, pulse_redis_data, pulse_backups` (the last gets `driver_opts: type: none, o: bind, device: ${BACKUP_DIR:-/var/backups/pulse}` in Task 2).

    2. `docker-compose.override.yml` — dev-only overrides (auto-loaded by `docker compose`):
       - `pulse-backend`: bind-mount `./backend:/app:rw`; environment `RELOAD=true`; command override `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` (preserves prod gunicorn entrypoint).
       - `pulse-frontend`: dev-only — bind-mount `./frontend:/app:rw` and command `npm run dev -- --host 0.0.0.0 --port 80` (production Dockerfile builds static; this override switches to dev server).

    3. `infra/db/init/00-extensions.sh` — RESEARCH.md Pitfall #1 mandates SHELL not SQL:
       ```bash
       #!/bin/sh
       set -e
       psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
         CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
         CREATE EXTENSION IF NOT EXISTS "pgcrypto";
         CREATE EXTENSION IF NOT EXISTS "vector";
       EOSQL
       ```
       Set executable bit (commit with mode 0755 or document chmod step in README).

    4. `backend/Dockerfile` — multi-stage. Stage 1 (`builder`): `FROM python:3.11-slim`, install build-essential, copy pyproject.toml, `pip install --prefix=/install .[prod]`. Stage 2 (`runtime`): `FROM python:3.11-slim`, copy `/install` into `/usr/local`, install only `curl` (for healthcheck) + `libpq5`, copy `backend/app` and `backend/alembic*`, expose 8000, CMD `["./entrypoint.sh"]`. The pyproject.toml is created in Plan 03 — this Dockerfile references it correctly so Plan 03's build succeeds.

    5. `backend/entrypoint.sh` — RESEARCH.md Pitfall #2 prescribes "migrate THEN gunicorn":
       ```bash
       #!/bin/sh
       set -e
       echo "[entrypoint] running alembic migrations..."
       alembic upgrade head
       echo "[entrypoint] starting gunicorn..."
       exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker \
            -w 4 -b 0.0.0.0:8000 --access-logfile - --error-logfile -
       ```
       Mode 0755.

    6. `frontend/Dockerfile` — multi-stage. Stage 1 (`builder`): `FROM node:20-alpine`, install pnpm via corepack, copy package.json + lockfile, `pnpm install --frozen-lockfile`, copy src, `pnpm build` → `/app/dist`. Stage 2 (`runtime`): `FROM nginx:1.30-alpine`, copy `dist/` to `/usr/share/nginx/html`, copy `frontend/nginx.conf` to `/etc/nginx/conf.d/default.conf`, expose 80.

    7. `frontend/nginx.conf` — internal-only nginx for the frontend container. Listen 80; root `/usr/share/nginx/html`; SPA fallback `try_files $uri $uri/ /index.html`; gzip on; **no security headers here** (the outer pulse-nginx layer owns them).

    All identifiers exactly per DEC-002 — no `siskonkin`. All env-var references use `${VAR}` Compose syntax so `.env` from Plan 01 drives them.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        if (-not (Test-Path 'docker-compose.yml')) { exit 1 };
        $compose = Get-Content 'docker-compose.yml' -Raw;
        foreach ($svc in 'pulse-db','pulse-redis','pulse-backend','pulse-frontend','pulse-nginx','pulse-net') {
          if ($compose -notmatch [regex]::Escape($svc)) { Write-Output ('missing ' + $svc); exit 2 }
        };
        if ($compose -notmatch 'pgvector/pgvector:pg16') { exit 3 };
        if ($compose -match '5432:5432') { Write-Output 'Postgres exposed publicly — forbidden by CONSTR-host-port'; exit 4 };
        if (-not (Test-Path 'infra/db/init/00-extensions.sh')) { exit 5 };
        $ext = Get-Content 'infra/db/init/00-extensions.sh' -Raw;
        if ($ext -notmatch 'EXTENSION.+vector')  { exit 6 };
        if ($ext -notmatch 'EXTENSION.+uuid-ossp') { exit 7 };
        if (-not (Test-Path 'backend/Dockerfile')) { exit 8 };
        if (-not (Test-Path 'backend/entrypoint.sh')) { exit 9 };
        if (-not (Test-Path 'frontend/Dockerfile')) { exit 10 };
        docker compose config --quiet 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Output 'compose config invalid'; exit 11 };
        Write-Output 'compose config valid'
      "
    </automated>
  </verify>
  <done>
    `docker compose config` parses successfully; all six DEC-002 identifiers present in compose; pgvector image pinned; Postgres has no `ports:`; extension init is a `.sh` (not `.sql`); both Dockerfiles parse-readable.
  </done>
</task>

<task type="auto">
  <name>Task 2: Backup sidecar + cron + restore script</name>
  <files>
    docker-compose.yml,
    infra/backup/Dockerfile,
    infra/backup/scripts/backup.sh,
    infra/backup/scripts/restore.sh,
    infra/backup/scripts/run-cron.sh
  </files>
  <action>
    1. `infra/backup/Dockerfile` — `FROM postgres:16-alpine` (has `pg_dump` and `psql`). Install **`dcron`** (Alpine's standard cron daemon) — replaces the previously-planned `busybox-suid` per CONTEXT.md Claude's Discretion / W-08 fix. Also install `rsync` for the weekly NAS push:
       ```dockerfile
       FROM postgres:16-alpine
       RUN apk add --no-cache rsync dcron
       COPY scripts/ /scripts/
       RUN chmod 0755 /scripts/*.sh
       ENTRYPOINT ["/scripts/run-cron.sh"]
       ```
       Per RESEARCH.md Don't-Hand-Roll table: a sidecar with internal cron beats host-cron-into-container. `dcron` provides a more predictable Alpine cron experience than busybox-suid (which has been flaky in some Alpine releases per CONTEXT.md Claude's Discretion section).

    2. `infra/backup/scripts/backup.sh` — production-ready, idempotent, no-args:
       ```sh
       #!/bin/sh
       set -eu
       : "${BACKUP_DIR:?BACKUP_DIR must be set}"
       : "${PGUSER:?PGUSER must be set}"
       TS=$(date -u +%Y%m%dT%H%M%SZ)
       OUT="${BACKUP_DIR}/pulse-${TS}.sql.gz"
       echo "[backup] writing ${OUT}"
       pg_dump --no-owner --clean --if-exists -h "${PGHOST}" -U "${PGUSER}" "${PGDATABASE}" | gzip > "${OUT}"
       echo "[backup] retaining ${RETAIN_DAYS:-30} days"
       find "${BACKUP_DIR}" -name 'pulse-*.sql.gz' -mtime "+${RETAIN_DAYS:-30}" -delete
       ls -lh "${BACKUP_DIR}" | tail -10
       ```

    3. `infra/backup/scripts/restore.sh` — CONSTR-backup acceptance: "pipe into psql, accept backup filename":
       ```sh
       #!/bin/sh
       set -eu
       [ -z "${1:-}" ] && { echo "Usage: $0 <backup-file>"; exit 2; }
       FILE="$1"
       case "$FILE" in
         /*) ABS="$FILE" ;;
         *)  ABS="${BACKUP_DIR}/$FILE" ;;
       esac
       [ -f "$ABS" ] || { echo "Not found: $ABS"; exit 2; }
       echo "[restore] loading $ABS into $PGDATABASE on $PGHOST"
       gunzip -c "$ABS" | psql -v ON_ERROR_STOP=1 -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE"
       ```

    4. `infra/backup/scripts/run-cron.sh` — installs crontab and runs crond in foreground:
       ```sh
       #!/bin/sh
       set -eu
       echo "[init] installing cron schedule (daily 02:00 backup, Sunday 03:00 rsync)"
       cat > /etc/crontabs/root <<CRON
       0 2 * * * /scripts/backup.sh >> /backups/backup.log 2>&1
       0 3 * * 0 rsync -a /backups/ \${NAS_DEST:-/mnt/nas/pulse-backups}/ >> /backups/rsync.log 2>&1
       CRON
       echo "[init] crontab:"
       cat /etc/crontabs/root
       echo "[init] starting crond -f"
       exec crond -f -L /dev/stdout
       ```
       Per RESEARCH.md Assumption A7: NAS rsync may not be reachable from inside Docker — that's flagged in the open-questions table at the bottom of this plan. For Phase 1, daily local backup is the locked acceptance; rsync is best-effort (will silently fail if NAS_DEST unreachable, logged to rsync.log).

    5. Append to `docker-compose.yml` (extend Task 1 file):
       ```yaml
         pulse-backup:
           build: ./infra/backup
           container_name: pulse-backup
           restart: unless-stopped
           depends_on:
             pulse-db:
               condition: service_healthy
           environment:
             PGHOST: pulse-db
             PGUSER: ${POSTGRES_USER}
             PGPASSWORD: ${POSTGRES_PASSWORD}
             PGDATABASE: ${POSTGRES_DB}
             BACKUP_DIR: /backups
             RETAIN_DAYS: ${BACKUP_RETAIN_DAYS:-30}
             NAS_DEST: ${NAS_DEST:-/mnt/nas/pulse-backups}
           volumes:
             - pulse_backups:/backups
           networks: [pulse-net]
       ```
       And in the top-level `volumes:` block:
       ```yaml
         pulse_backups:
           driver: local
           driver_opts:
             type: none
             o: bind
             device: ${BACKUP_DIR:-/var/backups/pulse}
       ```
       Note: the bind device path `${BACKUP_DIR}` must exist on the host before `docker compose up` — document this in the SUMMARY (operator runs `mkdir -p $BACKUP_DIR`).
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $b = Get-Content 'infra/backup/scripts/backup.sh' -Raw;
        if ($b -notmatch 'pg_dump') { exit 1 };
        if ($b -notmatch 'gzip')    { exit 2 };
        $r = Get-Content 'infra/backup/scripts/restore.sh' -Raw;
        if ($r -notmatch 'gunzip')  { exit 3 };
        if ($r -notmatch 'psql')    { exit 4 };
        $c = Get-Content 'infra/backup/scripts/run-cron.sh' -Raw;
        if ($c -notmatch '0 2 \* \* \*') { exit 5 };
        if ($c -notmatch '0 3 \* \* 0') { exit 6 };
        $compose = Get-Content 'docker-compose.yml' -Raw;
        if ($compose -notmatch 'pulse-backup') { exit 7 };
        if ($compose -notmatch 'pulse_backups') { exit 8 };
        # Docker preflight (CONTEXT.md Test Infrastructure: every Wave-2+ docker shell call runs `docker info` first)
        docker info 1>$null 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Output 'docker engine not reachable; aborting'; exit 8 };
        docker compose config --quiet 2>&1
        if ($LASTEXITCODE -ne 0) { exit 9 };
        # B-06 fix: actually exercise the backup Dockerfile (proves dcron resolves and image builds)
        $dockerfile = Get-Content 'infra/backup/Dockerfile' -Raw;
        if ($dockerfile -notmatch 'dcron') { Write-Output 'backup Dockerfile must use dcron (W-08)'; exit 10 };
        if ($dockerfile -match 'busybox-suid') { Write-Output 'backup Dockerfile must NOT use busybox-suid'; exit 11 };
        docker compose build pulse-backup 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Output 'pulse-backup image build failed'; exit 12 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    backup.sh runs pg_dump → gzip; restore.sh pipes gunzip → psql; run-cron.sh installs the locked schedule (CONSTR-backup); pulse-backup service added to compose with bind-mount to host BACKUP_DIR.
  </done>
</task>

<task type="auto">
  <name>Task 3: Nginx reverse-proxy with security headers + rate limits</name>
  <files>
    nginx/Dockerfile,
    nginx/nginx.conf,
    nginx/conf.d/pulse.conf,
    nginx/conf.d/_proxy.inc
  </files>
  <action>
    1. `nginx/Dockerfile`:
       ```
       FROM nginx:1.30-alpine
       COPY nginx.conf /etc/nginx/nginx.conf
       COPY conf.d/ /etc/nginx/conf.d/
       # Defensive: remove the default vhost shipped by the base image
       RUN rm -f /etc/nginx/conf.d/default.conf || true
       EXPOSE 80
       ```

    2. `nginx/nginx.conf` — minimal top-level. Worker connections 1024; gzip on (`text/css application/javascript application/json image/svg+xml font/woff2`); `include /etc/nginx/conf.d/*.conf;`.

    3. `nginx/conf.d/_proxy.inc` — shared proxy headers:
       ```
       proxy_http_version 1.1;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_connect_timeout 5s;
       proxy_send_timeout 60s;
       proxy_read_timeout 60s;
       ```

    4. `nginx/conf.d/pulse.conf` — REQ-nginx-config full acceptance:
       ```
       upstream pulse_backend  { server pulse-backend:8000; }
       upstream pulse_frontend { server pulse-frontend:80; }

       limit_req_zone $binary_remote_addr zone=api_zone:10m rate=60r/s;
       limit_req_zone $binary_remote_addr zone=ai_zone:10m  rate=20r/m;
       limit_req_zone $binary_remote_addr zone=login_zone:10m rate=5r/m;

       server {
           listen 80;
           server_name pulse.tenayan.local _;

           # Locked security headers (CONSTR-security-headers)
           add_header X-Frame-Options              "DENY"                                always;
           add_header X-Content-Type-Options       "nosniff"                             always;
           add_header X-XSS-Protection             "1; mode=block"                       always;
           add_header Strict-Transport-Security    "max-age=31536000; includeSubDomains" always;
           add_header Referrer-Policy              "strict-origin-when-cross-origin"     always;

           # Cap multipart payload — REQ-no-evidence-upload defense in depth
           client_max_body_size 25M;

           # Auth login: strict per-IP throttle (defense against brute force)
           location = /api/v1/auth/login {
               limit_req zone=login_zone burst=3 nodelay;
               proxy_pass http://pulse_backend;
               include /etc/nginx/conf.d/_proxy.inc;
           }

           # AI endpoints — wired now to avoid retro-fits in Phase 5
           location ^~ /api/v1/ai/ {
               limit_req zone=ai_zone burst=5 nodelay;
               proxy_pass http://pulse_backend;
               include /etc/nginx/conf.d/_proxy.inc;
           }

           # General API
           location /api/ {
               limit_req zone=api_zone burst=20 nodelay;
               proxy_pass http://pulse_backend;
               include /etc/nginx/conf.d/_proxy.inc;
           }

           # WebSocket (stub for Phase 1; Phase 2 wires actual /ws/* routes)
           location /ws/ {
               proxy_pass http://pulse_backend;
               proxy_http_version 1.1;
               proxy_set_header Upgrade $http_upgrade;
               proxy_set_header Connection "upgrade";
               proxy_read_timeout 3600s;
           }

           # Static frontend
           location / {
               proxy_pass http://pulse_frontend;
               include /etc/nginx/conf.d/_proxy.inc;
           }
       }
       ```

    Notes:
    - HTTP only (port 80 inside container; mapped to host 3399). HTTPS / TLS deferred per DEC-011 (RESEARCH.md Assumption A8).
    - All headers use `always` so they fire on error pages too.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $conf = Get-Content 'nginx/conf.d/pulse.conf' -Raw;
        foreach ($p in 'X-Frame-Options','X-Content-Type-Options','Strict-Transport-Security','Referrer-Policy','limit_req_zone.*api_zone.*60r/s','limit_req_zone.*ai_zone.*20r/m','client_max_body_size 25M','upstream pulse_backend','upstream pulse_frontend') {
          if ($conf -notmatch $p) { Write-Output ('missing pattern: ' + $p); exit 1 }
        };
        # Validate nginx syntax by mounting into a temp container
        docker run --rm -v ${PWD}/nginx/nginx.conf:/etc/nginx/nginx.conf:ro -v ${PWD}/nginx/conf.d:/etc/nginx/conf.d:ro nginx:1.30-alpine nginx -t 2>&1
        if ($LASTEXITCODE -ne 0) { exit 2 };
        Write-Output 'nginx config valid'
      "
    </automated>
  </verify>
  <done>
    `nginx -t` reports `configuration file ... test is successful`; all five security headers present; api/ai/login rate-limit zones declared; `client_max_body_size 25M` set; WebSocket upgrade block present.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Internet → host port 3399 | Public ingress; only port published |
| pulse-nginx → pulse-backend | Internal `pulse-net`; trusted |
| pulse-backend → pulse-db | Internal; credentials from .env |
| Backup files at rest | Host filesystem under `${BACKUP_DIR}` |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-S-01 | Spoofing | Brute-force login | mitigate | Nginx `limit_req zone=login_zone rate=5r/m burst=3 nodelay` on `/api/v1/auth/login`. Backend lockout-on-failure planned in Plan 05. |
| T-02-T-01 | Tampering | Clickjacking via iframe | mitigate | `X-Frame-Options: DENY` set in `nginx/conf.d/pulse.conf`. |
| T-02-I-01 | Information disclosure | Postgres exposed publicly | mitigate | No `ports:` on pulse-db service; only reachable on `pulse-net`. |
| T-02-I-02 | Information disclosure | Backup files world-readable | accept | Host filesystem perms managed at install time; documented in SUMMARY. Tightening to mode 0600 is Phase 6 prod-checklist work. |
| T-02-D-01 | DoS | Compose-up race with pgvector init | mitigate | `depends_on: condition: service_healthy` (RESEARCH.md Pitfall #2). |
| T-02-D-02 | DoS | Large Excel upload OOMs backend | mitigate | `client_max_body_size 25M` at nginx + Plan 06 enforces openpyxl streaming. |
| T-02-E-01 | Elevation | Direct DB connect bypasses backend | mitigate | No `ports:` on pulse-db; firewall planned in Phase 6 prod checklist (`REQ-prod-checklist`). |
</threat_model>

<verification>
- `docker compose config --quiet` returns 0
- `docker run --rm ... nginx -t` returns "test is successful"
- Six DEC-002 service names present in compose; one network `pulse-net`; one host port `3399`
- pgvector init is `.sh` not `.sql` (Pitfall #1)
- Backup cron schedule matches CONSTR-backup verbatim (02:00 daily + 03:00 Sunday rsync)
</verification>

<success_criteria>
- All Dockerfiles parse-clean and reference correct base images
- `docker compose up -d --wait` will succeed once Plan 03 (backend/) and Plan 04 (frontend/) deliver their respective `app/` and `src/` trees (verified in Plan 07's checkpoint)
- Nginx config passes `nginx -t` lint
- pulse-backup sidecar is present and bind-mounted to host BACKUP_DIR
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-master-data-auth/01-02-SUMMARY.md` listing:
1. Final docker-compose service list with image/tag for each
2. The `nginx -t` output
3. The full backup cron schedule installed in pulse-backup
4. Any open question that affected implementation (e.g., NAS reachability per Assumption A7)
</output>
