---
status: complete
phase: 09-workflow-playbook
plan: 01
requirements_addressed:
  - REQ-workflow-playbook
---

# Plan 09-01 - In-App Workflow Playbook

## Objective

Create a workflow playbook page that guides operators through PULSE's Konkin workflow, status transitions, role handoffs, expected outputs, and common checks.

## Scope

- Create `frontend/src/routes/WorkflowPlaybook.tsx`.
- Register `/workflow-playbook` in `frontend/src/App.tsx`.
- Add `Alur Kerja` navigation link in `frontend/src/routes/AppShell.tsx`.
- Add i18n key `nav.workflowPlaybook`.
- Update GSD requirements/roadmap/state.

## Verification

- `pnpm --dir frontend build` passes.
- `pnpm --dir frontend test --run` passes.
- `GET /workflow-playbook` returns the SPA from local Nginx.
- Main smoke remains green.
