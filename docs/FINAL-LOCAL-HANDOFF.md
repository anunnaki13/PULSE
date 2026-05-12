# PULSE Final Local Handoff

Status date: 2026-05-13

This document is the handoff point for the current local development build. It is intentionally practical: what is ready, what is blocked, which account to use, and what should happen next.

## Current Status

PULSE is locally feature-complete enough for study, walkthrough, and internal UAT.

Production go-live is not complete. Phase 6 production handover remains blocked by external deployment gates.

## Local Access

Local URL:

```text
http://127.0.0.1:3399/
```

Development accounts:

| Role | Email | Password |
|------|-------|----------|
| Super Admin | `super@pulse.tenayan.local` | `pulse-super-dev-2026` |
| Admin Unit | `admin@pulse.tenayan.local` | `pulse-admin-dev-2026` |
| Asesor | `asesor@pulse.tenayan.local` | `pulse-asesor-dev-2026` |
| PIC OM-1 | `pic.om1@pulse.tenayan.local` | `pulse-pic-dev-2026` |

These are development credentials only. Rotate all passwords and secrets before any real deployment.

## What Is Ready Locally

- Login and role-based access.
- Master data Konkin 2026 seed.
- Periode and assessment workflow.
- PIC self-assessment.
- Asesor review and approval.
- Recommendation tracker.
- Notifications and audit log.
- NKO calculation and dashboard.
- Compliance tracker and report export.
- AI assist surfaces in mock mode.
- Pedoman RAG, summary, and SMART action-plan endpoints.
- In-app learning pages:
  - `Panduan`
  - `Kamus Formula`
  - `Alur Kerja`

## Active UAT Context

Active dummy UAT periode:

```text
6765fedb-d75a-446c-b529-bdc7b273ac0b
```

Known local smoke result from Phase 6/9:

- Health detail: OK.
- AI mode: mock.
- Dashboard NKO: `2.2500`.
- PDF report export returns bytes.

## Production Blockers

Do not treat this build as production-ready until all of these are complete:

1. Rotate `.env` secrets and remove any development credentials.
2. Provision OpenRouter production key and quota.
3. Set `AI_MOCK_MODE=false` only after OpenRouter is verified.
4. Provision SSL certificate.
5. Apply VPS firewall rules.
6. Configure external health monitoring.
7. Run final production smoke after deployment.

Reference documents:

- `.planning/phases/06-stream-coverage-hcr-golive/06-PRODUCTION-CHECKLIST.md`
- `.planning/phases/06-stream-coverage-hcr-golive/06-GO-LIVE-RUNBOOK.md`
- `.planning/phases/06-stream-coverage-hcr-golive/06-FINAL-UAT.md`

## Freeze Rule

No more local feature/menu additions should be made before the next UX simplification pass.

The app is already powerful, but the operator journey is not simple enough yet. The next work should reduce surface area, clarify the main path per role, and move supporting reference material out of the primary path.

## Recommended Next Cycle

Start with `docs/UX-SIMPLIFICATION-BACKLOG.md`.

Target outcome: an operator can log in and immediately understand the one or two actions they are expected to do that day.
