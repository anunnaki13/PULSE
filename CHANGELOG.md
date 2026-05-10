# Changelog

Semua perubahan penting pada proyek SISKONKIN didokumentasikan di sini.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id-ID/1.0.0/),
dan proyek ini mengikuti [Semantic Versioning](https://semver.org/lang/id/).

## [Unreleased] — Blueprint Phase

### Added
- Dokumen blueprint awal (10 dokumen + README)
  - `01_DOMAIN_MODEL.md` — pemahaman bisnis Konkin 2026
  - `02_FUNCTIONAL_SPEC.md` — spesifikasi modul & user roles
  - `03_DATA_MODEL.md` — schema PostgreSQL + JSONB structure
  - `04_API_SPEC.md` — REST API contract (FastAPI)
  - `05_FRONTEND_ARCHITECTURE.md` — struktur React + state management
  - `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` — design tokens skeuomorphic
  - `07_AI_INTEGRATION.md` — strategi LLM (OpenRouter routing)
  - `08_DEPLOYMENT.md` — Docker Compose + Nginx + backup
  - `09_DEVELOPMENT_ROADMAP.md` — fase MVP → Full
  - `10_CLAUDE_CODE_INSTRUCTIONS.md` — instruksi Claude Code di VPS

### Domain Decisions
- TIDAK ada upload file evidence — hanya text/URL link eksternal
- Setiap stream maturity level pakai dynamic JSONB schema (struktur berbeda per stream)
- HCR & OCR ditunda ke Fase 6 (ruang sudah disiapkan)
- UI: gaya skeuomorphic (control room digital), bukan generic SaaS
- AI: Gemini 2.5 Flash untuk routine, Claude Sonnet untuk complex

## [0.1.0] — TBD (target end Fase 1)
Foundation release.

## [0.2.0] — TBD (target end Fase 3 = MVP)
End-to-end workflow + dashboard.
