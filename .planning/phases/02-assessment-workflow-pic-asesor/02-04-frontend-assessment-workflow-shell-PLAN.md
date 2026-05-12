# Plan 02-04 - Frontend Assessment Workflow Shell

## Objective

Expose the Phase 2 backend workflow in the React app: periode lifecycle controls, assessment queue, recommendation tracker actions, notification list, and the Phase 2 skeuomorphic input primitives needed by assessment forms.

## Scope

- Add authenticated routes for Phase 2 operational surfaces.
- Add API query/mutation helpers for periode, assessment sessions, recommendations, and notifications.
- Add `SkSlider`, `SkToggle`, and `SkLevelSelector` primitives to the skeuomorphic barrel.
- Make the local Docker Compose dev override run the frontend dev server from the correct Node/pnpm image stage.

## Verification

- `pnpm exec tsc -b --pretty false`
- `pnpm exec vite build --debug`
- `pnpm exec vitest run --passWithNoTests`
- `docker compose up -d --build pulse-frontend pulse-nginx`
- `curl http://127.0.0.1:3399/api/v1/health`
- `curl -I http://127.0.0.1:3399/`

## Deferred

- Full per-session detail screen with ML sub-area payload editor and 5-second IndexedDB offline auto-save queue.
- Asesor review detail screen with inline recommendation creation.
- Audit-log frontend route.
