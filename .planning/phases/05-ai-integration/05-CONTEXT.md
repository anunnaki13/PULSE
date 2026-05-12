---
status: complete
phase: 05-ai-integration
created_at: "2026-05-12T03:35:00.000+07:00"
---

# Phase 05 Context - AI Integration

## Goal

PIC and asesor get opt-in AI assistance for drafting justifications, SMART recommendations, anomaly checks, inline help, and cross-period comparison, with PII masking, audit trail, rate limiting, cost tracking, and graceful fallback when OpenRouter is unavailable.

## Locked Decisions

- Provider: OpenRouter only.
- Routine model: `google/gemini-2.5-flash`.
- Complex model: `anthropic/claude-sonnet-4`.
- App metadata headers: `HTTP-Referer: https://pulse.tenayan.local` and app title `PULSE`.
- PII masking before outbound LLM calls is mandatory.
- Every AI request must be logged in `ai_suggestion_log`.
- `ai_inline_help` table is mandatory and one row per indikator.
- Phase 5 must keep assessment workflows functional when AI is unavailable.

## Local Development Constraint

`OPENROUTER_API_KEY` is not present in the current `.env`. Phase 5 implementation therefore uses a deterministic `AI_MOCK_MODE=true` local default so UAT can exercise the workflow without external spend or key provisioning. Production can set `AI_MOCK_MODE=false` and provide `OPENROUTER_API_KEY`.

## Primary Surfaces

- Backend `/api/v1/ai/*`.
- Frontend `AssessmentList` AI assist buttons and inline help drawer/panel.
- Admin health detail should include OpenRouter/AI availability.

## Verification Focus

- PII masking blocks NIP-like numbers, emails, and known vendor token patterns before LLM call.
- Draft justification returns 3-5 BI formal sentences.
- Draft recommendation returns SMART-shaped JSON.
- Anomaly check returns deterministic classification.
- Inline help is cached in `ai_inline_help`.
- Comparative analysis returns 3-5 sentence narrative and trend points.
- AI unavailable state disables buttons without blocking normal forms.
