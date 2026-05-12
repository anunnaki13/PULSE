# ROADMAP — PULSE

> Authoritative roadmap derived from the verbatim 7-phase breakdown in `09_DEVELOPMENT_ROADMAP.md` (preserved at `intel/context.md` §11), with Phase 5 deliverables updated per locked ADR DEC-008. Six phases (Phase 1–6) deliver the v1 MVP; Phase 2+ enhancements are explicitly out of scope.
>
> Phase numbering follows the source's "Phase N" naming. Each phase delivers a coherent, verifiable capability. Every requirement in `REQUIREMENTS.md` maps to exactly one phase.
>
> **MVP usable at end of Phase 3** (per source §5: "→ Akhir Phase 3 = MVP USABLE"). Phase 4–6 harden the system into full Konkin 2026 coverage and operational readiness.

---

## Phases

- [x] **Phase 1: Foundation (Master Data + Auth)** — App boots, login works, master data Konkin 2026 ter-seed, struktur stream bisa dibrowse, docker compose + nginx stack online di port 3399, design-system primitives dipakai. *Closed 2026-05-11 — operator-verified E2E.*
- [x] **Phase 2: Assessment Workflow (PIC + Asesor)** — End-to-end self-assessment + asesor review + rekomendasi tracker untuk indikator pilot (Outage + SMAP + EAF + EFOR), notifications + audit log live. *Closed 2026-05-12 — role-specific UAT passed for super_admin, pic_bidang, and asesor.*
- [x] **Phase 3: NKO Calculator + Dashboard** — NKO terhitung otomatis multi-tier, dashboard eksekutif + heatmap + trend live via WebSocket. Akhir fase ini = MVP USABLE. *Closed 2026-05-12 — Chrome headless operator verification passed.*
- [x] **Phase 4: Compliance Tracker + Reports** — 9 laporan rutin + komponen lain ter-track, pengurang terintegrasi ke NKO, export PDF/Excel/Word resmi. *Closed 2026-05-12 — compliance UI, NKO deduction, and report export UAT passed.*
- [x] **Phase 5: AI Integration** — OpenRouter routing + 5 fitur AI MVP (Draft Justifikasi, Draft Rekomendasi, Anomaly Detection, AI Inline Help, Comparative Analysis) + sub-fase 5b RAG/Summary/SMART. *Closed 2026-05-12 — Phase 5 core AI UAT passed; Phase 5b optional items deferred to Phase 6/go-live hardening.*
- [ ] **Phase 6: Stream Coverage Lengkap + HCR + Go-Live Hardening** — Semua 14 sub-stream ML Pilar II + HCR + sub-indikator Pilar I/IV/V ter-implementasi, prod checklist passed.
- [x] **Phase 7: Operator Onboarding + Guided Help** — Panduan menu dan alur Konkin tersedia langsung di aplikasi agar operator dapat mempelajari fungsi menu, role, dan perbedaan formula/satuan tiap stream sambil production gates Phase 6 diselesaikan. *Closed 2026-05-12 — `/guide` in-app guide build/test passed.*
- [x] **Phase 8: Formula + Stream Dictionary** — Kamus formula tersedia langsung di aplikasi untuk mempelajari family rumus, satuan, polaritas, bobot, agregasi, dan contoh stream. *Closed 2026-05-13 — `/formula-dictionary` build/test/smoke passed.*
- [x] **Phase 9: Workflow Playbook** — Playbook alur kerja tersedia langsung di aplikasi untuk memahami status, handoff role, checklist harian, dan kontrol sebelum finalisasi. *Closed 2026-05-13 — `/workflow-playbook` build/test/smoke passed.*
- [x] **Phase 10: Final Local Freeze + UX Simplification Backlog** — Local build dibekukan untuk studi/UAT, handoff akhir ditulis, dan backlog simplifikasi UX dicatat agar fase berikutnya mengurangi kebingungan alur sebelum menambah fitur. *Closed 2026-05-13 — documentation-only freeze, no new app surface added.*

---

## Phase Details

### Phase 1: Foundation (Master Data + Auth)
**Goal**: User dapat login ke aplikasi PULSE dan menelusuri struktur master data Konkin 2026 (perspektif → indikator → stream ML rubrik) di lingkungan Docker Compose yang sudah berjalan, dengan branding, design system, dan kebijakan no-evidence-upload sudah aktif sejak hari pertama.

**Depends on**: Nothing (first phase)

**Requirements**: REQ-user-roles, REQ-auth-jwt, REQ-route-guards, REQ-konkin-template-crud, REQ-dynamic-ml-schema, REQ-bidang-master, REQ-frontend-stack, REQ-backend-stack, REQ-docker-compose-deploy, REQ-nginx-config, REQ-pulse-branding, REQ-pulse-heartbeat-animation, REQ-skeuomorphic-design-system, REQ-health-checks, REQ-no-evidence-upload, REQ-backup-restore

**Success Criteria** (what must be TRUE):
  1. Admin dapat login via `pulse.tenayan.local:3399` dengan kredensial JWT, dan navigasi ke `/master/konkin-template/2026` menampilkan 6 perspektif + indikator yang ter-seed.
  2. PIC dapat login dan hanya melihat indikator yang di-assign ke `bidang_id`-nya (read-only view); akses ke `/master/*` ditolak dengan redirect ke `/dashboard`.
  3. Halaman login menampilkan branding **PULSE** dengan tagline "Denyut Kinerja Pembangkit, Real-Time." dan animasi Pulse Heartbeat (LED 60–80 BPM) — verifikasi `grep -ri "siskonkin"` di repo zero hits.
  4. `make seed` populates bidang master + Konkin 2026 PLTU Tenayan struktur (perspektif + indikator + bobot, plus seed Outage + SMAP + EAF + EFOR rubrik) tanpa error; `GET /api/v1/health` returns 200.
  5. Tidak ada endpoint multipart untuk evidence file; `link_eviden` field hanya menerima URL; admin Excel-import endpoint adalah satu-satunya multipart endpoint.
  6. Daily backup cron at 02:00 sudah scheduled di VPS, restore script teruji manual sekali.

**Plans**: 7 plans across 5 waves (revised iteration 2 — see plan Revision History blocks)

| Wave | Plans | Notes |
|------|-------|-------|
| 1 | 01-01 | Repo scaffold + docker-verify checkpoint |
| 2 | 01-02, 01-03, 01-04 | Parallel: infra + backend skeleton + frontend skeleton. Plans 03/04 Task 1 is the **Wave 0 test bootstrap** (B-06): `pip install -e backend[dev]`, `pnpm install`, conftest, vitest globals types in tsconfig (B-05), test-runner smoke. |
| 3 | 01-05 | Auth backend (depends on 03). Six spec roles seeded (B-01/B-02). `users.bidang_id` NOT created here (B-04). Wires `metrics_admin_dep` to `require_role("super_admin","admin_unit")` (W-02). |
| 4 | 01-06 | Master data (depends on 03, 05). Sequential after 05 (W-04 Option A). 0003 migration adds master tables AND `users.bidang_id` + `fk_users_bidang_id` (B-04). Perspektif gets `is_pengurang` + `pengurang_cap` (W-07). `import-from-excel` adds `require_csrf` (B-07). |
| 5 | 01-07 | Integration (depends on 02, 04, 05, 06). Frontend Role union + ProtectedRoute use spec roles (B-01/B-02). Login + master screens consume the six skeuomorphic primitives via barrel (W-01/W-10). Seed sets perspektif VI as `is_pengurang=True` (W-07) and creates the admin user with role `admin_unit` (CONTEXT.md Auth). |

- [x] 01-01-repo-scaffold-docker-verify-PLAN.md — **Wave 1.** Monorepo scaffold, .env.example, Makefile + PowerShell fallback, README "About the Name" (mentions admin_unit role per CONTEXT.md Auth), Docker-installed verify checkpoint. *Status (2026-05-11):* Task 1 complete (commit `ae7130f`); Task 2 resolved via WSL2 alternative — `docker compose version` returns v5.1.3 inside `Ubuntu-22.04` WSL2 distro. SUMMARY: `01-01-repo-scaffold-docker-verify-SUMMARY.md`.
- [x] 01-02-infra-compose-nginx-backup-PLAN.md — **Wave 2.** 6-service Docker Compose (pgvector + Redis + backend + frontend + nginx + backup sidecar), Nginx with security headers + rate-limit zones; backup sidecar uses **dcron** (W-08); Task 2 verify runs `docker compose build pulse-backup` (B-06). *Status (2026-05-11):* Complete via WSL2 docker. SUMMARY: `01-02-infra-compose-nginx-backup-SUMMARY.md`.
- [x] 01-03-backend-skeleton-health-PLAN.md — **Wave 2.** FastAPI app skeleton (pinned stack with `[dev]` extras); `/api/v1/health` plus admin-only `/api/v1/health/detail` and `/api/v1/metrics` (Prometheus text — W-02); Wave-0 test bootstrap with real `pytest --collect-only` smoke (B-06); router + model auto-discovery; `metrics_admin_dep` placeholder for Plan 05 to swap. *Status (2026-05-11):* Complete. 7/7 tests pass. SUMMARY: `01-03-backend-skeleton-health-SUMMARY.md`.
- [x] 01-04-frontend-skeleton-design-system-PLAN.md — **Wave 2.** React 18 + Vite + Tailwind v4 + motion 12; full DEC-003 token palette plus `--sk-led-glow` / `--sk-led-alert-glow`; **two** heartbeat keyframes (healthy / alert — B-03); reduced-motion gate; **six** primitives `SkLed`/`SkButton`/`SkPanel`/`SkInput`/`SkSelect`/`SkBadge` + barrel `@/components/skeuomorphic` (W-01/W-10); vitest globals + jest-dom in `tsconfig.app.json` (B-05); BI i18n lookup; real `pnpm install` + `vitest --passWithNoTests` smoke (B-06). *Status (2026-05-11):* Complete. 31/31 tests pass. SUMMARY: `01-04-frontend-skeleton-design-system-SUMMARY.md`.
- [x] 01-05-auth-backend-jwt-rbac-PLAN.md — **Wave 3.** Users/roles models + Alembic 0002 seeding **six spec roles** (`super_admin`, `admin_unit`, `pic_bidang`, `asesor`, `manajer_unit`, `viewer` — B-01/B-02); JWT dual-mode (Bearer/cookie) with refresh-token jti rotation in Redis; `require_role` dep; CSRF double-submit; brute-force lockout; `users.bidang_id` is NOT created (B-04 — moves to Plan 06); wires `metrics_admin_dep` to `require_role("super_admin","admin_unit")` (W-02 closure). *Status (2026-05-11):* Complete. 22/22 backend tests pass. SUMMARY: `01-05-auth-backend-jwt-rbac-SUMMARY.md`.
- [x] 01-06-master-data-backend-PLAN.md — **Wave 4 (sequential).** Bidang / Konkin / Perspektif (with `is_pengurang` + `pengurang_cap` — W-07) / Indikator / MlStream / `konkin_import_log` models + Alembic 0003 (JSONB+GIN) **plus `users.bidang_id` column + `fk_users_bidang_id` FK (B-04)**; admin-gated CRUD via spec role names (`super_admin`, `admin_unit`); template lock filters bobot by `is_pengurang=False` (W-07); admin-only Excel import as the single multipart endpoint **with `require_csrf`** (B-07). *Status (2026-05-11):* Complete in 14m18s. B-04 / W-07 / B-07 / B-01-B-02 all closed. SUMMARY: `01-06-master-data-backend-SUMMARY.md`.
- [x] 01-07-frontend-wire-seed-verify-PLAN.md — **Wave 5.** Zustand auth store; `Role` TS union and `ProtectedRoute` use the six spec names (B-01/B-02); Login + master screens consume only skeuomorphic primitives via barrel (W-01/W-10); idempotent seed (bidang + Konkin 2026 with VI as pengurang per W-07 + Outage/SMAP/EAF/EFOR + **admin_unit** user per CONTEXT.md Auth); Phase-1 e2e verification checkpoint covering W-02/W-07/W-08/B-03/B-04/B-07 evidence steps. *Status (2026-05-11):* Complete. Automation + operator browser walk PASS (admin login, 6 perspektif + 26 bidang + ml_stream tree, PIC/manajer redirect from /master/*). 44/44 vitest. SUMMARY: `01-07-frontend-wire-seed-verify-SUMMARY.md`.

**UI hint**: yes

---

### Phase 2: Assessment Workflow (PIC + Asesor)
**Goal**: PIC dapat melakukan self-assessment end-to-end (KPI Kuantitatif + Maturity Level) untuk indikator pilot, asesor dapat review/override/return, dan setiap rekomendasi yang dibuat dapat di-track sampai close atau carry-over ke periode berikutnya — semua perubahan tercatat di audit log dan notifikasi terkirim.

**Depends on**: Phase 1

**Requirements**: REQ-periode-lifecycle, REQ-self-assessment-kpi-form, REQ-self-assessment-ml-form, REQ-auto-save, REQ-pic-actions, REQ-asesor-review, REQ-recommendation-create, REQ-recommendation-lifecycle, REQ-notifications, REQ-audit-log

**Success Criteria** (what must be TRUE):
  1. Admin dapat membuka periode TW2 2026, transisi `draft → aktif → self_assessment` membuat assessment_session otomatis untuk setiap indikator-bidang pair.
  2. PIC dapat mengisi self-assessment EAF (KPI Kuantitatif) dengan polaritas-aware formula auto-compute (positif/negatif/range-based), mengisi maturity level Outage Management semua sub-area via LevelSelector dial, dan form auto-save tiap 5 detik dengan indikator "Saved Xs ago".
  3. Asesor dapat review submission, melakukan approve/override/request_revision dengan justifikasi mandatory pada override, dan menempelkan rekomendasi inline saat review.
  4. PIC dapat update progress rekomendasi (`PATCH /recommendations/{id}/progress`), mark-completed → pending_review; asesor verify-close menutup rekomendasi; periode close otomatis carry-over rekomendasi yang belum tuntas.
  5. Notifikasi `assessment_due` / `review_pending` / `recommendation_assigned` terkirim via WebSocket `/ws/notifications` dan email SMTP untuk deadline; setiap mutating action tercatat di `audit_log` dengan `before_data`/`after_data`.

**Plans**: 4 plans across 4 waves

- [x] 02-01-backend-schema-and-migrations-PLAN.md — Backend schema, Alembic migrations, assessment/periode/recommendation foundations. SUMMARY: `02-01-backend-schema-and-migrations-SUMMARY.md`.
- [x] 02-02-periode-assessment-recommendation-routers-PLAN.md — Periode lifecycle, assessment-session, recommendation routers and services. SUMMARY: `02-02-periode-assessment-recommendation-routers-SUMMARY.md`.
- [x] 02-03-audit-middleware-notifications-websocket-PLAN.md — Audit log, notification dispatcher, REST routes, WebSocket notifications. SUMMARY: `02-03-audit-middleware-notifications-websocket-SUMMARY.md`.
- [x] 02-04-frontend-assessment-workflow-shell-PLAN.md — Frontend periode, assessment, recommendation, notification, audit-log surfaces plus ML rubric rendering and autosave support. SUMMARY: `02-04-frontend-assessment-workflow-shell-SUMMARY.md`.

**UAT**: `02-UAT.md` — 7/7 automated role-specific tests passed on 2026-05-12.
**UI hint**: yes

---

### Phase 3: NKO Calculator + Dashboard
**Goal**: Manajer Unit dapat melihat dashboard eksekutif PULSE dengan NKO real-time yang dihitung otomatis multi-tier (sub-area → area → stream → indikator → pilar → NKO), drill-down ke detail komponen, dan visualisasi trend + heatmap maturity.

**Depends on**: Phase 2

**Requirements**: REQ-nko-calc-engine, REQ-nko-aggregation-rules, REQ-nko-realtime-ws, REQ-dashboard-executive, REQ-dashboard-heatmap, REQ-dashboard-trend

**Success Criteria** (what must be TRUE):
  1. Setiap perubahan `assessment_session` (PIC submit, asesor approve/override) men-trigger recompute NKO dan persist `nko_snapshot` dengan breakdown JSONB; rumus `NKO = Σ(Pilar I..V) − Pengurang Compliance` terbukti dengan worked example PLTU Tenayan SMT 2 2025 (NKO Final ≈ 103.36).
  2. Aggregate-indikator averaging rules (Tabel 2) menangani kasus "tidak dinilai" — Biaya/Fisik Pemeliharaan 50/50 dengan fallback ke 100% jika satu missing, LCCM-PSM/ERM-Keuangan/WPC-Outage/Reliability-Efficiency/Operation-EnergiPrimer pairs idem, HCR/OCR normalisasi bobot.
  3. Manajer Unit membuka `/dashboard/executive?periode_id=` dan melihat NkoGauge (skeuomorphic analog meter dengan ripple Pulse Heartbeat saat update), PilarPanel (5 cards dengan trend), HeatmapMaturity (streams × triwulan), TrendChart per indikator, dan Forecast NKO (linear regression).
  4. Saat asesor approve sebuah indikator di workspace, NkoGauge di dashboard manajer ter-update tanpa manual refresh via `WS /ws/dashboard` payload `{type: "nko_updated", periode_id, nko_total, changed_indikator}`.
  5. Drill-down navigation berfungsi: Pilar → Indikator → komponen detail; minimum 4 indikator (EAF, EFOR, Outage ML, SMAP) sudah ter-track dan terhitung dalam NKO total — **MVP USABLE**.

**Plans**: 2 planned execution slices (created 2026-05-12)

- [x] 03-01-nko-snapshot-engine-dashboard-api-PLAN.md — Persisted NKO snapshot engine, blueprint-aware aggregation rules, executive dashboard/heatmap/trend APIs, and dashboard WebSocket broadcast. SUMMARY: `03-01-nko-snapshot-engine-dashboard-api-SUMMARY.md`.
- [x] 03-02-executive-dashboard-live-integration-PLAN.md — Connect the existing dashboard prototype to live APIs/WS, keep dummy fallback data for unavailable live history, and preserve stream-specific formulas/units in drilldowns. SUMMARY: `03-02-executive-dashboard-live-integration-SUMMARY.md`.
**UI hint**: yes

---

### Phase 4: Compliance Tracker + Reports
**Goal**: BID CPF dan auditor dapat track 9 laporan rutin + komponen compliance lain (PACA/ICOFR/NAC/Critical Event) dengan pengurang otomatis terintegrasi ke NKO, dan manajer dapat export laporan formal NKO Semester (PDF/Excel/Word) yang siap dikirim ke Direksi PT PLN NP.

**Depends on**: Phase 3

**Requirements**: REQ-compliance-laporan-tracker, REQ-compliance-komponen, REQ-compliance-summary, REQ-report-nko-semester, REQ-report-assessment-sheet, REQ-report-compliance-detail, REQ-report-recommendation-tracker

**Success Criteria** (what must be TRUE):
  1. `compliance_laporan_definisi` ter-seed dengan 9 laporan rutin (Pengusahaan, BA Transfer Energi, Keuangan, Monev BPP, Kinerja Investasi, Manajemen Risiko, Self Assessment, Manajemen Material, Navitas) dengan default `pengurang_per_keterlambatan` = 0.039 dan `keterlambatan_hari` sebagai GENERATED column.
  2. BID CPF input bahwa Laporan Pengusahaan Mei terlambat 2 hari → sistem otomatis hitung pengurang −0.078 dan memunculkannya di `GET /compliance/summary?periode_id=`; total pengurang ter-cap di −10.
  3. NKO total terkoreksi setelah pengurang Compliance ditambahkan — dashboard menampilkan NKO Final (Σ Pilar minus Compliance) di NkoGauge.
  4. Komponen non-laporan (PACA, Critical Event, ICOFR, NAC) ter-track via `compliance_komponen` + `compliance_komponen_realisasi` dengan formula configurable per komponen.
  5. Manajer dapat export `GET /reports/nko-semester?periode_id=&format=pdf` dengan format mirror `08_Draft_NKO_UP_Tenayan_SMT_2_2025`, export Excel kertas-kerja per session, multi-sheet compliance detail, dan recommendation tracker — semua membuka tanpa error di MS Excel/Word/Acrobat.

**Plans**: 3 planned execution slices (created 2026-05-12)

- [x] 04-01-compliance-backend-summary-nko-PLAN.md — Compliance persistence, deduction summary, and NKO integration. SUMMARY: `04-01-compliance-backend-summary-nko-SUMMARY.md`.
- [x] 04-02-compliance-frontend-dashboard-PLAN.md — Compliance tracker UI and dashboard deduction surfacing. SUMMARY: `04-02-compliance-frontend-dashboard-SUMMARY.md`.
- [x] 04-03-report-exports-PLAN.md — NKO, assessment, compliance, and recommendation export endpoints. SUMMARY: `04-03-report-exports-SUMMARY.md`.

**UAT**: `04-UAT.md` — compliance API/UI/NKO/export checks passed on 2026-05-12.

---

### Phase 5: AI Integration
**Goal**: PIC dan asesor mendapat asistensi AI yang menambah produktivitas (draft justifikasi, draft rekomendasi SMART, anomaly detection, inline help per indikator, comparative analysis cross-periode) dengan biaya ~$3.15/bulan, full audit trail, PII masking, rate-limit 20/min/user, dan fallback graceful saat OpenRouter down — plus sub-fase 5b RAG chat / executive summary / SMART action-plan generator.

**Depends on**: Phase 4

**Requirements**: REQ-ai-draft-justification, REQ-ai-draft-recommendation, REQ-ai-anomaly-detection, REQ-ai-inline-help, REQ-ai-comparative-analysis, REQ-ai-rate-limiting, REQ-ai-pii-masking, REQ-ai-fallback, REQ-ai-audit-trail, REQ-rate-limiting-general, REQ-ai-rag-chat, REQ-ai-summary-periode, REQ-ai-action-plan-generator

**Success Criteria** (what must be TRUE):
  1. PIC klik "AI Assist" pada catatan EAF → suggestion 3–5 kalimat BI formal muncul di AI Suggestion Drawer dalam < 5 detik (Gemini Flash); suggestion bisa di-edit/accept/reject dan tercatat di `ai_suggestion_log`. Asesor klik AI Assist saat tulis rekomendasi → output struktur SMART JSON (severity, deskripsi, action_items, target_outcome).
  2. PIC klik ikon ❓ di samping nama indikator → side panel slide-in menampilkan AI Inline Help (Apa itu / Formula / Best practice / Indikator terkait / Kesalahan umum) dari cache `ai_inline_help`; admin dapat trigger regenerate via `POST /api/v1/ai/inline-help/{id}/regenerate`. Tombol "Bandingkan dengan TW Lalu" pada form (visible jika ≥1 prior period) memunculkan modal dengan narasi 3–5 kalimat + 4-period trend chart, di-cache 1 jam.
  3. Hybrid anomaly detection memflag self-assessment dengan deviasi >30% / >2σ / ML jump >1.5 levels; LLM classifier mereturn salah satu dari `legitimate_improvement | data_entry_error | needs_verification | suspicious` dengan reason yang muncul sebagai warning badge di Asesor Workspace.
  4. PII masking layer memblok NIP / personal email / vendor names sebelum payload dikirim ke OpenRouter (verifikasi via test); header `X-Title: PULSE` dan `HTTP-Referer: https://pulse.tenayan.local` ter-set; rate limit 20 req/min/user enforced di Nginx + backend, 100 req/min mutating dan 1000 req/min dashboard read juga enforced.
  5. Saat OpenRouter unavailable, semua AI button disabled dengan tooltip "Layanan AI sementara tidak tersedia"; form workflows tetap fungsional 100%; error tercatat dengan exponential backoff. Sub-fase 5b: chat RAG dengan Pedoman Konkin (Claude Sonnet, k=5 ivfflat cosine, sources cited) + summary periode 400–600 kata + SMART action-plan generator JSON — semua opsional, tidak block Phase 5 inti.
  6. Total biaya AI ter-track per use-case dan per user; bulan pertama actual spend ≤ $5 (target ~$3.15); 100% AI request tercatat di `ai_suggestion_log`.

**Plans**: 3 planned execution slices (created 2026-05-12)

- [x] 05-01-ai-backend-foundation-PLAN.md — AI persistence, PII masking, OpenRouter/mock client, and backend endpoints. SUMMARY: `05-01-ai-backend-foundation-SUMMARY.md`.
- [x] 05-02-ai-frontend-assist-surfaces-PLAN.md — AI Assist controls in assessment workflow with fallback disabled state. SUMMARY: `05-02-ai-frontend-assist-surfaces-SUMMARY.md`.
- [x] 05-03-ai-uat-eval-hardening-PLAN.md — UAT, eval notes, audit verification, and Phase 5b gap handling. SUMMARY: `05-03-ai-uat-eval-hardening-SUMMARY.md`.
**UAT**: `05-UAT.md` — core AI integration checks passed on 2026-05-12; optional Phase 5b items deferred.
**UI hint**: yes

---

### Phase 6: Stream Coverage Lengkap + HCR + Go-Live Hardening
**Goal**: Semua sub-stream maturity level Konkin 2026 (Reliability, Efficiency, WPC, Operation, Energi Primer, LCCM, SCM, Manajemen Lingkungan, K3, Keamanan, Pengelolaan Bendungan, DPP) plus HCR/OCR ter-implementasi, sub-indikator Pilar I/IV/V lengkap, dan production go-live checklist passed sehingga sistem dapat diserahkan untuk operasional resmi UP Tenayan.

**Depends on**: Phase 5

**Requirements**: REQ-prod-checklist

**Success Criteria** (what must be TRUE):
  1. Batch 1 (Reliability, Efficiency, WPC) + Batch 2 (Operation, Energi Primer Batubara/Gas/BBM, LCCM, SCM) + Batch 3 (Manajemen Lingkungan & K3, Manajemen Keamanan, Pengelolaan Bendungan, DPP) — semua 14 sub-stream ML Pilar II ter-input rubriknya via JSONB tree-editor dan dapat di-self-assess oleh PIC bidang masing-masing.
  2. Batch 4 — HCR (Strategic Workforce Planning, Talent Acquisition, Talent Mgmt & Development, Performance Mgmt, Reward & Recognition, Industrial Relation, HC Operations) dan OCR (6 sub-area dengan bobot khusus untuk OWM 55/45) — self-assessment bisa dilakukan untuk minimal 1 area HCR dan seluruh 6 sub-area OCR.
  3. Sub-indikator Pilar I lengkap: BPP komponen (Biaya Har 70/30, Fisik Har 70/30, Biaya Adm, Biaya Kimia & Pelumas, Penghapusan ATTB), SDGs 7 sub (TJSL, Proper, ERM, Intensitas Emisi, Kepuasan Pelanggan range-based, Umur Persediaan Batubara, Implementasi Digitalisasi); Pilar IV Disburse Investasi & PRK Terkontrak 4 sub; Pilar V SPKI/Budaya/Diseminasi/LTIFR target 0.106. NKO total benar-benar mencakup semua kontribusi.
  4. Production go-live checklist passed: semua `.env` secrets unique dan strong, Postgres tidak exposed publicly, backup verified (test restore sukses), SSL provisioned, firewall hanya 22 + 3399/443, log rotation configured, health-check external monitor live, first super_admin dengan strong password, Konkin 2026 master data fully seeded, Pedoman Konkin indexed ke pgvector, OpenRouter key valid + quota approved, end-to-end smoke test (login + create assessment + submit) pass.
  5. Demo final: Konkin 2026 PLTU Tenayan full coverage, semua indikator ter-track, NKO Semester 1 2026 dapat di-finalisasi dan di-export sebagai laporan resmi.

**Plans**: 5 planned execution slices (created 2026-05-12)

- [x] 06-01-stream-blueprint-seed-and-tree-editor-PLAN.md — Seed remaining Pilar II maturity stream blueprints and admin tree editing support. SUMMARY: `06-01-stream-blueprint-seed-and-tree-editor-SUMMARY.md`.
- [x] 06-02-hcr-ocr-assessment-coverage-PLAN.md — HCR/OCR dynamic maturity assessment coverage and special OCR weighting. SUMMARY: `06-02-hcr-ocr-assessment-coverage-SUMMARY.md`.
- [x] 06-03-subindikator-formula-coverage-nko-PLAN.md — Complete Pilar I/IV/V formula coverage and NKO integration. SUMMARY: `06-03-subindikator-formula-coverage-nko-SUMMARY.md`.
- [x] 06-04-pedoman-rag-summary-action-plan-PLAN.md — Deferred Phase 5b RAG, summary, and SMART action-plan endpoints. SUMMARY: `06-04-pedoman-rag-summary-action-plan-SUMMARY.md`.
- [ ] 06-05-production-hardening-final-uat-PLAN.md — Production checklist, backup/restore, security, OpenRouter, and final UAT. SUMMARY: `06-05-production-hardening-final-uat-SUMMARY.md`; local hardening/UAT passed, production gates remain blocked.

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation (Master Data + Auth) | 7/7 | **Complete** | 2026-05-11 |
| 2. Assessment Workflow (PIC + Asesor) | 4/4 | **Complete** | 2026-05-12 |
| 3. NKO Calculator + Dashboard | 2/2 | **Complete** | 2026-05-12 |
| 4. Compliance Tracker + Reports | 3/3 | **Complete** | 2026-05-12 |
| 5. AI Integration | 3/3 | **Complete** | 2026-05-12 |
| 6. Stream Coverage Lengkap + HCR + Go-Live Hardening | 5/5 local, prod gates blocked | Blocked | - |
| 7. Operator Onboarding + Guided Help | 1/1 | **Complete** | 2026-05-12 |
| 8. Formula + Stream Dictionary | 1/1 | **Complete** | 2026-05-13 |
| 9. Workflow Playbook | 1/1 | **Complete** | 2026-05-13 |
| 10. Final Local Freeze + UX Simplification Backlog | 1/1 | **Complete** | 2026-05-13 |

---

### Phase 7: Operator Onboarding + Guided Help
**Goal**: Operator dapat mempelajari fungsi menu, role, alur Konkin, dan perbedaan formula/satuan stream langsung dari aplikasi tanpa harus membuka dokumen terpisah.

**Depends on**: Phase 6 local build (production go-live gates may remain blocked)

**Requirements**: REQ-operator-onboarding-guide

**Success Criteria** (what must be TRUE):
  1. User authenticated melihat menu `Panduan` di header aplikasi.
  2. `/guide` menjelaskan fungsi Dasbor, Assessment, Rekomendasi, Periode, Compliance, Audit, Master Data, dan Notifikasi.
  3. `/guide` menjelaskan role utama dan alur end-to-end Konkin.
  4. `/guide` menjelaskan bahwa tiap stream dapat memiliki formula, satuan, polaritas, bobot, dan agregasi berbeda.
  5. Frontend build pass.

**Plans**: 1 planned execution slice

- [x] 07-01-in-app-menu-guide-PLAN.md — In-app menu guide and operator onboarding surface. SUMMARY: `07-01-in-app-menu-guide-SUMMARY.md`.

---

### Phase 8: Formula + Stream Dictionary
**Goal**: Operator dapat membuka kamus formula di aplikasi untuk memahami perbedaan family rumus, satuan, polaritas, bobot, agregasi, dan contoh stream tanpa harus membaca file blueprint.

**Depends on**: Phase 7

**Requirements**: REQ-formula-stream-dictionary

**Success Criteria** (what must be TRUE):
  1. User authenticated melihat menu `Kamus Formula` di header aplikasi.
  2. `/formula-dictionary` menjelaskan family rumus positif, negatif, range, maturity, weighted maturity, dan compliance pengurang.
  3. `/formula-dictionary` memuat contoh stream KPI, maturity, HCR/OCR, sub-indikator, dan compliance.
  4. Halaman memiliki filter pencarian dan filter family formula.
  5. Frontend build dan test pass.

**Plans**: 1 planned execution slice

- [x] 08-01-formula-stream-dictionary-PLAN.md — In-app formula and stream dictionary. SUMMARY: `08-01-formula-stream-dictionary-SUMMARY.md`.

---

### Phase 9: Workflow Playbook
**Goal**: Operator dapat mengikuti alur operasional PULSE dari setup periode sampai finalisasi melalui playbook in-app berisi langkah, owner, status, handoff, dan checklist kontrol.

**Depends on**: Phase 8

**Requirements**: REQ-workflow-playbook

**Success Criteria** (what must be TRUE):
  1. User authenticated melihat menu `Alur Kerja` di header aplikasi.
  2. `/workflow-playbook` menjelaskan langkah setup periode, generate session, self-assessment, review asesor, rekomendasi, compliance, dan dashboard/laporan.
  3. `/workflow-playbook` menjelaskan status periode, assessment, rekomendasi, dan compliance.
  4. `/workflow-playbook` memuat handoff antar role dan checklist harian.
  5. Frontend build dan test pass.

**Plans**: 1 planned execution slice

- [x] 09-01-in-app-workflow-playbook-PLAN.md — In-app workflow playbook. SUMMARY: `09-01-in-app-workflow-playbook-SUMMARY.md`.

---

### Phase 10: Final Local Freeze + UX Simplification Backlog
**Goal**: Local build dibekukan untuk dipelajari/UAT tanpa menambah menu baru, production blockers tetap jelas, dan backlog perbaikan UX dicatat untuk menyederhanakan alur berikutnya.

**Depends on**: Phase 9

**Requirements**: REQ-final-local-freeze

**Success Criteria** (what must be TRUE):
  1. `docs/FINAL-LOCAL-HANDOFF.md` menjelaskan status local-ready vs production-blocked, credential dev, active dummy periode, dan gate production tersisa.
  2. `docs/UX-SIMPLIFICATION-BACKLOG.md` mencatat backlog simplifikasi navigasi, role-based home, dashboard density, dummy data label, terminology, dan formula/help placement.
  3. README menautkan handoff dan UX backlog.
  4. Planning state mencatat Phase 10 complete tanpa mengubah status blocked Phase 6 production handover.
  5. Tidak ada app route, menu, schema, endpoint, atau fitur baru yang ditambahkan.

**Plans**: 1 planned execution slice

- [x] 10-01-final-local-freeze-PLAN.md — Final local freeze and UX simplification backlog. SUMMARY: `10-01-final-local-freeze-SUMMARY.md`.

---

## Out-of-Scope (Phase 2+ — explicitly deferred per source §9 + DEC-011)

- **F+1: Multi-Unit** — replikasi struktur untuk unit PLN NP lain (Paiton, Gresik, dll); multi-tenant via row-level security; cross-unit benchmarking dashboard.
- **F+2: Advanced AI** — Forecasting NKO via ML time series (Prophet, ARIMA); voice input (Whisper); auto-translate ke English; recommendation-impact analysis.
- **F+3: Mobile App** — React Native; push notifications native.
- **F+4: Integration** — Sync ERP/SAP for BPP; sync Navitas for EAF/EFOR; webhooks Telegram/Teams.
- **F+5: Audit Trail Enhancements** — Compliance audit-log export; tamper-proof append-only with hash chain; independent auditor view.
- **Open items deferred (DEC-011):** Final logo, SSL certificate strategy, OpenRouter API key provisioning, external integrations (Navitas, SAP).
