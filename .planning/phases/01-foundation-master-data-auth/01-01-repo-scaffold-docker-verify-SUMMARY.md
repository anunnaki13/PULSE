---
phase: 01-foundation-master-data-auth
plan: 01
subsystem: repo-scaffold
status: complete
tags: [scaffold, branding, docker-precondition, dx]
dependency_graph:
  requires: []
  provides:
    - repo-top-level-layout
    - dx-entrypoints-make-pwsh-bash
    - pulse-brand-of-record
    - env-example-template
  affects:
    - all-downstream-phase-1-plans  # 01-02 / 01-03 / 01-04 depend on this scaffold
tech_stack:
  added:
    - "GNU Make (Git Bash on Windows)"
    - "PowerShell 5.1+ (scripts/dev.ps1)"
    - "Bash 4+ (scripts/dev.sh)"
  patterns:
    - "Three-shell DX entrypoint mirror (Make / pwsh / bash) — same docker compose calls in all three so cross-platform behavior is identical"
key_files:
  created:
    - .gitignore
    - .env.example
    - Makefile
    - scripts/dev.ps1
    - scripts/dev.sh
    - docs/ABOUT-THE-NAME.md
  modified:
    - README.md  # replaced legacy SISKONKIN-branded README with PULSE landing page
decisions:
  - "Three-shell DX strategy: Make (Git Bash), PowerShell, Bash — kept in lockstep manually rather than auto-generated, since divergence will be loud and minimal."
  - "ABOUT-THE-NAME.md describes rebrand at narrative level WITHOUT writing the literal legacy token; verbatim find-and-replace list lives in the ADR (UPDATE-001) and PROJECT.md DEC-002. This is what makes the strict `grep -ri \"siskonkin\"` audit gate pass on the six new files."
  - "Numbered blueprint docs (01_DOMAIN_MODEL.md … 10_CLAUDE_CODE_INSTRUCTIONS.md) at repo root were NOT touched by this plan — they are pre-rebrand source-of-truth intel that will be migrated/replaced by Phase 1's later plans (frontend/backend/docs structure). Logged as deferred."
metrics:
  duration_minutes: 18
  completed_date: "2026-05-11"
  tasks_completed: 2
  tasks_paused_at_checkpoint: 0
  files_created: 6
  files_modified: 1
  commits: 1
---

# Phase 1 Plan 01: Repo Scaffold + Docker Verify — Summary

**One-liner:** Monorepo top-level scaffolded with PULSE brand artifacts, three-shell DX entrypoints (Make / PowerShell / Bash), and a `.env.example` carrying DEC-002 identifiers — paused at a `human-action` checkpoint until the operator confirms Docker Compose is installed on the Windows host.

---

## What was built (Task 1 — committed, hash `ae7130f`)

Seven files at repo root + `docs/`:

| Path                    | Role |
|-------------------------|------|
| `.gitignore`            | Excludes `.env`, venvs, `node_modules`, build/dist, caches, `backups/`, IDE artifacts |
| `.env.example`          | Documented env template — DEC-002 identifiers (`pulse-db`, `pulse-redis`, etc.), no real secrets, placeholders for `INITIAL_ADMIN_*` |
| `Makefile`              | Ten phony targets — `up`, `down`, `build`, `seed`, `migrate`, `test`, `backup`, `restore FILE=…`, `logs`, `lint` + `help` listing them |
| `scripts/dev.ps1`       | PowerShell parameter-dispatcher mirroring every Make target |
| `scripts/dev.sh`        | Bash equivalent (Git Bash + Linux + macOS) |
| `README.md`             | BI-first landing page — Tentang Nama (links to ABOUT-THE-NAME), Quick Start, Stack table, **Developer Verbs** table (cross-shell), **Verifikasi Docker** section, Roles table (six spec roles incl. `admin_unit`), Phase 1 Acceptance Criteria |
| `docs/ABOUT-THE-NAME.md`| Rebrand audit trail — DEC-001 acronym, DEC-002 narrative summary (verbatim list referenced in ADR), DEC-003 heartbeat motion |

### Verification gate run (plan's `<automated>` block)

Captured output of `Select-String` audit on the six new files:

```
brand clean
pass
```

- Zero `siskonkin` hits (case-insensitive, simple match) on `README.md`, `docs/ABOUT-THE-NAME.md`, `.env.example`, `Makefile`, `scripts/dev.ps1`, `scripts/dev.sh`.
- README contains `Performance & Unit Live Scoring Engine` (acronym), `Denyut Kinerja Pembangkit` (BI tagline), and `admin_unit` (role naming required by CONTEXT.md Auth).
- All seven files exist.

### Deletions sanity check

`git diff --diff-filter=D --name-only HEAD~1 HEAD` returned empty. No accidental deletions.

---

## Task 2 — Docker host verified (resolved via WSL2 alternative)

**Resume signal taken: WSL2 alternative path** (the plan's resume-signal block explicitly allows: *"If Docker is intentionally NOT going to be installed (alternative: WSL2 / remote Docker host), reply with the chosen alternative and Wave 2 will be retargeted in revision."*).

Resolution captured 2026-05-11:

```
$ wsl -d Ubuntu-22.04 -- docker --version
Docker version 29.4.3, build 055a478

$ wsl -d Ubuntu-22.04 -- docker compose version
Docker Compose version v5.1.3

$ wsl -d Ubuntu-22.04 -- docker info --format '{{.ServerVersion}}'
29.4.3
```

`docker run --rm hello-world` succeeded end-to-end (image pull + container run + clean exit), proving daemon + network + registry pipeline.

**Host topology (binds Wave 2):**
- Container runtime lives inside the `Ubuntu-22.04` WSL2 distro (`docker-ce 29.4.3` + `docker-compose-plugin v5.1.3` from `download.docker.com/linux/ubuntu jammy stable`). User `zzz` (gid 999 docker). Daemon auto-starts via systemd (`/etc/wsl.conf [boot] systemd=true`).
- **No `docker.exe` on the Windows host.** Any compose command in Wave-2+ plan verify blocks must be invoked through WSL. Two equivalent calling conventions:
  - From PowerShell: `wsl -d Ubuntu-22.04 -- docker compose -f /mnt/c/Users/ANUNNAKI/projects/PULSE/<file> <args>`
  - Or `cd` into the WSL shell first (`wsl -d Ubuntu-22.04`) then call `docker` natively
- Repo path translation: Windows `C:\Users\ANUNNAKI\projects\PULSE` ↔ WSL `/mnt/c/Users/ANUNNAKI/projects/PULSE` (drvfs mount; bind-mount sources resolve correctly; IO is ~5–10× slower than native ext4, acceptable for Phase 1 scaffolding).
- DNS hardened: `/etc/wsl.conf` `generateResolvConf=false`; `/etc/resolv.conf` `chattr +i` at `1.1.1.1` + `8.8.8.8` (WSL gateway `10.255.255.254` was not forwarding to host).

Wave 2 (Plans 01-02 / 01-03 / 01-04) is **unblocked**; orchestrator proceeds.

The user's environment was inspected at planning time (RESEARCH.md §Environment Availability):
- Docker / Docker Compose: ✗ not on PATH in current shell.
- Python 3.13.13: ✓ (host; backend container will use 3.11-slim).
- Node 25.8.1: ✓ (host; frontend container will use node:20-alpine).
- `make`: ✗ not on PowerShell PATH (Git Bash is available; `scripts/dev.ps1` is the documented Windows fallback now committed).
- `psql 17.2`: ✓.
- `git 2.39.1`: ✓.

The user must:
1. Install Docker Desktop for Windows (or any equivalent Docker Engine) — https://www.docker.com/products/docker-desktop/
2. Launch and wait for the engine indicator to turn green.
3. Reopen the PowerShell terminal so `PATH` refreshes.
4. Run these three commands in PowerShell and paste the output back to the orchestrator:
   ```powershell
   docker --version
   docker compose version
   docker info
   ```

Expected:
- `Docker version 24.x` or newer
- `Docker Compose version v2.x` or newer
- `docker info` reports a running engine (no "Cannot connect to the Docker daemon" error)

Resume signal (any of):
- Type `docker ready` after the three commands all succeed.
- Paste the version strings.
- If Docker is intentionally not going to be installed on this host (e.g. WSL2 / remote Docker host plan), reply with the chosen alternative and Wave 2 will be retargeted.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ABOUT-THE-NAME.md and README.md cannot quote the legacy token directly**

- **Found during:** Task 1 verification gate run.
- **Issue:** The plan body for Task 1 says (a) ABOUT-THE-NAME.md should "cover the SISKONKIN→PULSE rebrand audit list from DEC-002" and (b) README's Phase 1 Acceptance section should paste ROADMAP success criterion #3 verbatim — which itself contains `grep -ri "siskonkin"`. Both directly conflict with the plan's `<automated>` verify block, which hard-fails on any case-insensitive `siskonkin` hit in any of the six new files. The truth list ("Zero residual `siskonkin`/`SISKONKIN`/`Siskonkin` strings exist in any committed text outside `.planning/intel/classifications/`") is consistent with the verify gate, but the audit-trail authoring instructions are not.
- **Fix:**
  - ABOUT-THE-NAME.md: rewritten to describe the rebrand at the narrative level using indirection (`<old>-net`, "nama lama", "the legacy token") and to point to the ADR (`UPDATE-001-pulse-rebrand-ai-features.md`) and `.planning/PROJECT.md` DEC-002 for the verbatim find-and-replace list. The acronym, taglines, motion meaning, and 12-line audit cake are all preserved; only the literal old name is omitted from the body.
  - README.md success criterion #3: rewritten in spirit ("`grep` repo terhadap nama legacy pra-rebrand mengembalikan zero hits di luar `.planning/intel/classifications/`, lihat DEC-002 di docs/ABOUT-THE-NAME.md") instead of pasting the literal `grep -ri "siskonkin"` invocation.
- **Rationale:** This satisfies the truth list AND the verify gate AND keeps the audit-trail discoverable (one click to PROJECT.md DEC-002 or to UPDATE-001 ADR). Treated as Rule 1 because the plan as written would have produced a file that fails its own verify gate.
- **Files modified:** `README.md`, `docs/ABOUT-THE-NAME.md`.
- **Commit:** `ae7130f`.

### Authentication / Human-Action Gates

**1. [Plan-anticipated] Docker Desktop install on Windows host**
- **Task:** Task 2 (the checkpoint).
- **Why:** Docker is not on the user's PATH; CONTEXT.md Phase 1 success criteria 1/4/5/6 cannot be reached without it.
- **Outcome:** Paused awaiting user verification — see "Awaiting" block above. Not a deviation; this is the explicit purpose of Task 2.

---

## Deferred Items (Out of scope for this plan)

1. **Numbered blueprint docs at repo root** — `01_DOMAIN_MODEL.md`, `02_FUNCTIONAL_SPEC.md`, `04_API_SPEC.md`, `05_FRONTEND_ARCHITECTURE.md`, `06_DESIGN_SYSTEM_SKEUOMORPHIC.md`, `07_AI_INTEGRATION.md`, `08_DEPLOYMENT.md`, `09_DEVELOPMENT_ROADMAP.md`, `10_CLAUDE_CODE_INSTRUCTIONS.md`, `CHANGELOG.md`, `UPDATE-001-pulse-rebrand-ai-features.md` — all still contain pre-rebrand naming (the legacy token). These are pre-existing intel/ADR documents from the bootstrap commit (`9c96766`), not artifacts produced by this plan. Plan 01-01's `files_modified` frontmatter explicitly does NOT list them; the plan task body does NOT instruct rewriting them. They are functionally equivalent to the `.planning/intel/classifications/` exemption (sumber sejarah). When a downstream phase migrates them into proper `frontend/`, `backend/`, `nginx/`, `docs/` subdirectories, the rebrand cleanup happens there. Logged here so the verifier and Plan 01-07 (Wave 5 e2e brand audit) know they exist.

2. **Repo-wide `grep -ri siskonkin` audit** — RESEARCH.md "Phase Requirements → Test Map" lists `! grep -ri --exclude-dir=.git --exclude-dir=node_modules siskonkin .` as the smoke test for `REQ-pulse-branding`. That audit is plan 01-07's responsibility (Wave 5 final verification), not 01-01. Plan 01-01 only enforces brand-cleanliness on the seven new files it created.

---

## Threat Flags

None. The artifacts created in this plan are documentation and shell scripts; no new network endpoints, auth paths, or trust-boundary surface introduced.

---

## TDD Gate Compliance

Plan 01-01 frontmatter does not declare `type: tdd`, and Task 1 has no `tdd="true"` attribute — this is documentation/scaffolding only, no behavior to test-first. Skipped. Wave 0 test bootstrap is allocated to Plans 03/04 per CONTEXT.md "Test Infrastructure" (B-06 fix).

---

## Self-Check: PASSED

Verified after writing this SUMMARY:

```
[ -f .gitignore ]                          → FOUND
[ -f .env.example ]                        → FOUND
[ -f Makefile ]                            → FOUND
[ -f scripts/dev.ps1 ]                     → FOUND
[ -f scripts/dev.sh ]                      → FOUND
[ -f README.md ]                           → FOUND
[ -f docs/ABOUT-THE-NAME.md ]              → FOUND
git log --oneline | grep ae7130f           → FOUND
```

The brand audit ran clean (`brand clean / pass`) at the end of Task 1, captured in the verification block above.
