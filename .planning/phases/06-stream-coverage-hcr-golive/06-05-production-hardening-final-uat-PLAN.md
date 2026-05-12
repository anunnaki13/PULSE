---
status: planned
phase: 06-stream-coverage-hcr-golive
plan: 05
requirements_addressed:
  - REQ-prod-checklist
---

# Plan 06-05 - Production Hardening Final UAT

## Objective

Prepare PULSE for handover/go-live with security, backup, monitoring, deployment, and final end-to-end UAT checks.

## Scope

- Validate `.env` secrets are unique/strong and no default dev password remains for go-live.
- Confirm Postgres is not exposed publicly.
- Run backup and restore drill.
- Document SSL/firewall strategy for ports 22 + 3399/443.
- Add/verify log rotation and external health monitor guidance.
- Validate OpenRouter key/quota path with mock-mode fallback retained.
- Run final E2E smoke: login -> create/open period -> create sessions -> self-assess -> submit -> asesor approve -> dashboard NKO -> export report.

## Verification

- Production checklist artifact.
- Final UAT artifact.
- `docker compose -f docker-compose.yml ps` healthy.
- Browser smoke on main workflows.
- Report export opens without error.
