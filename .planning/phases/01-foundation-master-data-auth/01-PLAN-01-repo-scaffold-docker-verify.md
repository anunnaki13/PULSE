---
phase: 01-foundation-master-data-auth
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .gitignore
  - .env.example
  - Makefile
  - scripts/dev.ps1
  - scripts/dev.sh
  - README.md
  - docs/ABOUT-THE-NAME.md
autonomous: false
requirements:
  - REQ-pulse-branding
  - REQ-docker-compose-deploy
user_setup:
  - service: docker
    why: "Phase 1 cannot reach success criteria 1/4/5/6 without Docker Compose running locally (RESEARCH.md Environment Availability flagged Docker missing from PATH)."
    env_vars: []
    dashboard_config:
      - task: "Install Docker Desktop for Windows (or Docker Engine) and confirm `docker compose version` runs in PowerShell"
        location: "https://www.docker.com/products/docker-desktop/"
must_haves:
  truths:
    - "Repo root contains the six top-level seams expected by every later plan (frontend/, backend/, nginx/, infra/, docs/, docker-compose.yml will live here)"
    - "An operator cloning the repo can read README.md and ABOUT-THE-NAME.md and learn the PULSE brand and tagline without grepping source docs"
    - "Zero residual `siskonkin`/`SISKONKIN`/`Siskonkin` strings exist in any committed text outside `.planning/intel/classifications/` (treat that dir as ingest-archive, exempt)"
    - "Make/scripts entrypoint advertises the six developer verbs: up / down / seed / migrate / test / backup-restore"
    - "Docker Compose is verified to be installed on the host before any compose-up task is allowed to start"
  artifacts:
    - path: ".gitignore"
      provides: "Excludes .env, node_modules, __pycache__, dist, .venv, backups, .pytest_cache, .vitest"
      contains: ".env"
    - path: ".env.example"
      provides: "Documented environment variable template — no real secrets"
      contains: "JWT_SECRET_KEY="
    - path: "Makefile"
      provides: "Cross-platform DX entrypoint (Git Bash friendly)"
      contains: "up:"
    - path: "scripts/dev.ps1"
      provides: "PowerShell fallback for hosts without make"
      min_lines: 20
    - path: "README.md"
      provides: "Project landing page with About-the-Name section per REQ-pulse-branding acceptance"
      contains: "PULSE"
    - path: "docs/ABOUT-THE-NAME.md"
      provides: "Verbatim brand etymology + tagline + identifier-rename audit trail (DEC-001, DEC-002)"
      contains: "Performance & Unit Live Scoring Engine"
  key_links:
    - from: "README.md"
      to: "docs/ABOUT-THE-NAME.md"
      via: "Markdown link"
      pattern: "\\[.*About.*\\]\\(docs/ABOUT-THE-NAME\\.md\\)"
    - from: "Makefile"
      to: "scripts/dev.ps1"
      via: "PowerShell fallback documented in README"
      pattern: "scripts/dev"
---

## Revision History

- **Iteration 1 (initial):** Created.
- **Iteration 2 (this revision):** No functional changes. Wave structure for the phase has been restructured (B-06 + W-04 fixes documented in Plans 03/04/05/06/07). This plan remains Wave 1 (scaffold + Docker verify) and gates the new Wave 0 test bootstrap that runs inside Plans 03 and 04. No content edits required here.

<objective>
Establish the monorepo skeleton, developer-ergonomics scripts, and brand-of-record so every downstream Phase-1 plan has a stable filesystem layout and a verified Docker host to compose against.

Purpose: Plans 02/03/04 (Wave 2) need the directory contract and Makefile verbs already in place; the Docker host must be verified BEFORE any `compose up` task tries to run (RESEARCH.md flagged Docker missing from PATH on the user's Windows host).
Output: `.gitignore`, `.env.example`, `Makefile`, `scripts/dev.{ps1,sh}`, `README.md` with "About the Name" section, `docs/ABOUT-THE-NAME.md`, and a verified Docker installation on the host.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-foundation-master-data-auth/01-CONTEXT.md
@.planning/phases/01-foundation-master-data-auth/01-RESEARCH.md

<interfaces>
<!-- Locked identifiers from DEC-002 (every later plan reads these) -->
- Network name: `pulse-net`
- Container names: `pulse-db`, `pulse-redis`, `pulse-backend`, `pulse-frontend`, `pulse-nginx`, `pulse-backup`
- DB: name=`pulse`, user=`pulse`, host=`pulse.tenayan.local`
- Backup dir on host: `/var/backups/pulse` (Linux); on Windows VPS adapt to bind path
- Repo top-level layout (per RESEARCH.md §Architecture):
    backend/  frontend/  nginx/  infra/backup/scripts/  docs/  scripts/  .planning/
    docker-compose.yml  docker-compose.override.yml  .env  .env.example  Makefile  README.md
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Scaffold monorepo top-level + brand artifacts</name>
  <files>
    .gitignore,
    .env.example,
    Makefile,
    scripts/dev.ps1,
    scripts/dev.sh,
    README.md,
    docs/ABOUT-THE-NAME.md
  </files>
  <action>
    1. `.gitignore`: ignore `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `node_modules/`, `dist/`, `build/`, `.pytest_cache/`, `.vitest/`, `coverage/`, `*.log`, `backups/`, `.idea/`, `.vscode/`, `.DS_Store`.

    2. `.env.example` (no real secrets — placeholders only, per DEC-002 identifiers):
       ```
       # Auth
       APP_SECRET_KEY=replace-me-with-32+-chars
       JWT_SECRET_KEY=replace-me-with-32+-chars
       JWT_ALGORITHM=HS256
       JWT_ACCESS_TTL_MIN=60
       JWT_REFRESH_TTL_DAYS=14

       # Postgres (DEC-002 identifiers)
       POSTGRES_HOST=pulse-db
       POSTGRES_PORT=5432
       POSTGRES_DB=pulse
       POSTGRES_USER=pulse
       POSTGRES_PASSWORD=replace-me

       # Redis
       REDIS_URL=redis://pulse-redis:6379/0

       # App
       APP_BASE_URL=https://pulse.tenayan.local
       APP_HOST_PORT=3399

       # Backup (DEC-002)
       BACKUP_DIR=/var/backups/pulse
       BACKUP_RETAIN_DAYS=30
       NAS_DEST=/mnt/nas/pulse-backups

       # First admin (per CONTEXT.md "Auth" — RESEARCH OQ#3 ADOPTED).
       # Seed will create one user with role `admin_unit` if no user has this email.
       INITIAL_ADMIN_EMAIL=admin@pulse.tenayan.local
       INITIAL_ADMIN_PASSWORD=replace-on-first-login
       ```

    3. `Makefile` — DX verbs (RESEARCH.md notes Git Bash is present on host; Make is not — Task 2 sets up the PowerShell fallback). Targets MUST be the six advertised verbs. Use shell-call indirection so the same target works under bash and Git Bash:
       ```
       .PHONY: up down build seed migrate test backup restore lint logs
       up:        ; docker compose up -d --wait
       down:      ; docker compose down
       build:     ; docker compose build
       seed:      ; docker compose exec pulse-backend python -m app.seed
       migrate:   ; docker compose exec pulse-backend alembic upgrade head
       test:      ; docker compose exec pulse-backend pytest -x -q && cd frontend && pnpm exec vitest run --reporter=basic
       backup:    ; docker compose exec pulse-backup /scripts/backup.sh
       restore:   ; @[ -n "$$FILE" ] || (echo "Usage: make restore FILE=<backup.sql.gz>"; exit 2); docker compose exec -T pulse-backup /scripts/restore.sh "$$FILE"
       logs:      ; docker compose logs -f --tail=200
       lint:      ; cd backend && ruff check . ; cd ../frontend && pnpm run lint
       ```
       Add a `help:` target listing all verbs.

    4. `scripts/dev.ps1` — PowerShell equivalents of every Make target (since Make is not on the user's PATH; RESEARCH.md Environment Availability). Param-based dispatcher: `./scripts/dev.ps1 up`, `... seed`, etc. Each branch invokes the same `docker compose ...` command.

    5. `scripts/dev.sh` — Bash equivalent (Git Bash on Windows; or any Linux/Mac VPS).

    6. `README.md` — Replace any existing README at repo root. Sections (BI primary, EN secondary per CONSTR-i18n-default):
       - Title: `# PULSE — Performance & Unit Live Scoring Engine`
       - Tagline: `> "Denyut Kinerja Pembangkit, Real-Time."` (DEC-001)
       - "## Tentang Nama" — link to `docs/ABOUT-THE-NAME.md`
       - "## Quick Start" — `cp .env.example .env`, fill secrets, `make up` (or `./scripts/dev.ps1 up`), wait for healthy, `make migrate && make seed`, open `http://localhost:3399`.
       - "## Stack" — bullet list from RESEARCH.md Standard Stack (versions pinned).
       - "## Developer Verbs" — table of Make / dev.ps1 targets.
       - "## Phase 1 Acceptance Criteria" — paste verbatim from ROADMAP.md success criteria. The Admin (success criterion #1) refers to a user with role **`admin_unit`** (CONTEXT.md "Auth" section).

    7. `docs/ABOUT-THE-NAME.md` — verbatim "About the Name" per ADR DEC-001 §1.4 expectation. Cover: acronym expansion, tagline (id/en/formal), the SISKONKIN→PULSE rebrand audit list from DEC-002, the heartbeat-as-signature decision (DEC-003).

    **Brand audit (final step of this task):** Run `grep -ri --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.planning/intel/classifications "siskonkin" .` — exit 0 hits expected (the planning intel classifications dir is an archive of pre-rebrand ingest material; whitelist it explicitly). If any hit fires outside that allow-list, rewrite that file in-place before commit. (Implements REQ-pulse-branding acceptance #4.)

    All file content stays in Bahasa Indonesia for user-facing strings; English allowed only for technical inline comments.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        if (-not (Test-Path '.env.example')) { exit 1 };
        if (-not (Test-Path 'README.md'))    { exit 1 };
        if (-not (Test-Path 'Makefile'))     { exit 1 };
        if (-not (Test-Path 'docs/ABOUT-THE-NAME.md')) { exit 1 };
        if (-not (Test-Path 'scripts/dev.ps1')) { exit 1 };
        Write-Output 'scaffold ok';
        $hits = Select-String -Path @('README.md','docs/ABOUT-THE-NAME.md','.env.example','Makefile','scripts/dev.ps1','scripts/dev.sh') -Pattern 'siskonkin' -CaseSensitive:$false -SimpleMatch;
        if ($hits) { Write-Output 'BRAND VIOLATION'; exit 2 };
        Write-Output 'brand clean';
        if (-not (Select-String -Path 'README.md' -Pattern 'Performance & Unit Live Scoring Engine')) { exit 3 };
        if (-not (Select-String -Path 'README.md' -Pattern 'Denyut Kinerja Pembangkit')) { exit 4 };
        if (-not (Select-String -Path 'README.md' -Pattern 'admin_unit')) { Write-Output 'README must mention admin_unit role per CONTEXT.md Auth'; exit 5 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    All seven files exist with correct content; README contains PULSE name, id-tagline, and the `admin_unit` role reference for ROADMAP success criterion #1; no `siskonkin` string in any new file; both Make (verb table) and PowerShell (parameter-dispatched script) entrypoints documented; .gitignore excludes .env.
  </done>
</task>

<task type="checkpoint:human-action" gate="blocking">
  <name>Task 2: Verify Docker Compose installed on host</name>
  <what-built>
    Repo scaffolding only — no compose stack started yet.
    This checkpoint pauses BEFORE Wave-2 plans (Plans 02/03/04) so the operator can confirm `docker compose` is available; if it isn't, Wave 2 cannot start.
  </what-built>
  <how-to-verify>
    In a fresh PowerShell terminal (the project Bash tool's shell), run:

    ```powershell
    docker --version
    docker compose version
    docker info
    ```

    Expected:
    - `docker --version` prints `Docker version 24.x` or newer.
    - `docker compose version` prints `Docker Compose version v2.x` or newer.
    - `docker info` reports a running Docker engine (no "Cannot connect to the Docker daemon" error).

    If any command fails:
    1. Install Docker Desktop for Windows from https://www.docker.com/products/docker-desktop/
    2. Launch Docker Desktop and wait for the engine status indicator to turn green
    3. Reopen the terminal so PATH refreshes
    4. Re-run the three commands above

    Once all three succeed, reply with the version strings (paste the output).
  </how-to-verify>
  <resume-signal>
    Type "docker ready" or paste the `docker --version` / `docker compose version` output.
    If Docker is intentionally NOT going to be installed (alternative: WSL2 / remote Docker host), reply with the chosen alternative and Wave 2 will be retargeted in revision.
  </resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Git repo → public mirror | If repo is ever pushed publicly, `.env` must never be committed. |
| Developer host → Docker daemon | `docker info` connects to the local daemon; the daemon runs with elevated privileges. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-S-01 | Spoofing | `.env` checked in | mitigate | `.gitignore` ignores `.env`; only `.env.example` (placeholders) tracked. |
| T-01-I-01 | Information disclosure | Secrets in README | mitigate | README links to `.env.example`; no real secret values copied into README/docs. |
| T-01-T-01 | Tampering | Brand drift | mitigate | grep-siskonkin audit in Task 1 verify step; gates phase commit. |
</threat_model>

<verification>
After Task 2 resumes, the phase precondition holds: an operator on this host can run `docker compose up -d --wait` without command-not-found.
</verification>

<success_criteria>
- `.env.example`, `Makefile`, `scripts/dev.ps1`, `scripts/dev.sh`, `README.md`, `docs/ABOUT-THE-NAME.md` present
- README contains the PULSE name, the Bahasa Indonesia tagline, and the `admin_unit` role reference
- `grep -ri siskonkin` against the new files returns zero hits
- Operator confirms `docker compose version` works on host
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-master-data-auth/01-01-SUMMARY.md` listing exact file paths created, the `docker compose version` string captured at the checkpoint, and the Make / dev.ps1 verb table.
</output>
</content>
</invoke>