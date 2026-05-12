# Phase 04 UAT - Compliance Tracker + Reports

Date: 2026-05-12
Status: PASS

## Scope

Phase 04 verifies that compliance records can be tracked, summarized, fed into NKO, surfaced in the frontend, and exported as deterministic artifacts.

## Results

| Check | Result | Evidence |
|---|---:|---|
| 9 routine report definitions seeded | PASS | `GET /api/v1/compliance/laporan-definisi` returned 9 rows |
| Pengusahaan late 2 days computes deduction | PASS | `summary.total_pengurang = 0.0780` |
| NKO uses persisted compliance deduction | PASS | dashboard snapshot returned `compliance_deduction = 0.0780`, `nko_total = 106.0420` |
| Compliance frontend renders after login | PASS | Chrome CDP smoke found `Compliance Control Desk`, `PENGUSAHAAN`, `0,0780`, exceptions `0` |
| Report export endpoints return downloadable artifacts | PASS | PDF/CSV/Word smoke returned non-empty artifacts and attachment header |
| Backend unit coverage | PASS | 12/12 Phase 4 focused backend tests passed |
| Frontend build/test | PASS | `pnpm build` passed; 12/12 focused frontend tests passed |

## Active Dummy Data

- Active periode: `d152b998-48e4-4d41-99fa-e1f901c7e2fe`
- Dummy report: `PENGUSAHAAN`, Mei, due `2026-05-10`, submitted `2026-05-12`, valid.
- Expected deduction: `2 x 0.039 = 0.0780`.

## Notes

- Early report artifacts are deterministic generated PDF/CSV/HTML-doc files. They satisfy Phase 04 export endpoints and remain ready for later formal template polish.
- WSL idle can briefly make host port `127.0.0.1:3399` refuse connections while containers rehydrate. Use `docker compose -f docker-compose.yml up -d --wait` from WSL before browser UAT if that happens.
