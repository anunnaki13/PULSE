---
status: passed
phase: 05-ai-integration
completed_at: "2026-05-12T12:08:00.000+07:00"
---

# Phase 05 UAT - AI Integration

## Scope Verified

- AI backend foundation: persistence, OpenRouter/mock client, PII masking, audit log, fallback, and endpoints.
- AI frontend assist surfaces in assessment workflow.
- AI health/status exposure for operations.
- Phase 5b optional features documented as deferred.

## Automated Verification

- Backend compile: `python3 -m compileall -q app` passed.
- Backend tests: `pytest -q tests/test_ai_phase5.py tests/test_report_exports.py tests/test_compliance_summary.py` passed: 12/12.
- Frontend build: `pnpm build` passed.
- Frontend focused tests: `pnpm test -- --run src/routes/ProtectedRoute.test.tsx src/lib/dashboard-calculations.test.ts` passed: 12/12.
- Docker rebuilds completed for `pulse-backend` and `pulse-frontend`.

## API Verification

- `GET /api/v1/health` returned `status=ok`.
- `GET /api/v1/health/detail` returned AI diagnostics:
  - `ai_mode=mock`
  - `ai_available=True`
  - routine model `google/gemini-2.5-flash`
  - complex model `anthropic/claude-sonnet-4`
- `GET /api/v1/ai/status` returned AI available in mock mode.
- `POST /api/v1/ai/draft-justification` returned a 438-character Bahasa Indonesia suggestion with `fallback=True` and persisted `log_id=d5b64ad5-07e6-4106-9869-42bfa8793394`.
- `ai_suggestion_log` contains rows for all five MVP AI use cases:
  - `draft_justification`
  - `draft_recommendation`
  - `anomaly_check`
  - `inline_help`
  - `comparative_analysis`
- Mock-mode cost remained `0.000000`.

## Browser Verification

- Chrome headless smoke against `http://127.0.0.1:3399/assessment`:
  - Login as `super@pulse.tenayan.local` succeeded.
  - `AI mock`, `AI Help`, `Bandingkan`, and `Cek Anomali` were visible.
  - Initial render produced `patchCount=0`; assessment autosave no longer saves every visible draft row on page load.
  - No browser exception or error console events were captured.

## Issues Found And Fixed During UAT

- `super_admin` assessment smoke originally triggered many initial autosave `PATCH` requests because every editable row scheduled autosave immediately after first render.
- Fixed in `frontend/src/lib/offline-assessment-queue.ts`:
  - Initial payload per row is treated as persisted baseline.
  - Autosave fires only after payload changes.
  - Initial offline queue flush runs once per application, not once per assessment row.
- AI assessor controls were active for PIC users and could lead to endpoint-level 403.
- Fixed in `frontend/src/routes/AssessmentList.tsx` with role-aware UI gating.

## Operational Note

- WSL idle shutdown can stop Docker and cause `ERR_CONNECTION_REFUSED` or temporary Nginx `502` after the laptop has been idle.
- Current session is kept alive with a background WSL sleep process. If access drops again, restart with:

```powershell
Start-Process -FilePath "wsl.exe" -ArgumentList '-d Ubuntu-22.04 --exec sleep 86400' -WindowStyle Hidden
wsl -d Ubuntu-22.04 -- bash -lc "cd /mnt/c/Users/ANUNNAKI/projects/PULSE && docker compose -f docker-compose.yml up -d --wait"
```

## Phase 5b Deferred Status

The optional Phase 5b items are not implemented as production endpoints in this slice:

- RAG chat over Pedoman Konkin with pgvector source citations.
- Executive summary periode 400-600 words.
- SMART action-plan generator endpoint.

This is accepted for Phase 5 core because the roadmap success criterion explicitly marks Phase 5b as optional and non-blocking. The correct next placement is Phase 6, alongside full stream coverage, Pedoman Konkin indexing, OpenRouter key validation, and go-live hardening.

## Verdict

PASS for Phase 5 core AI Integration.
