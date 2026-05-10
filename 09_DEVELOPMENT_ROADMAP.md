# 09 — Development Roadmap

> Rencana pengembangan SISKONKIN yang dipecah menjadi fase MVP → Fitur Lanjutan → AI → Stream Lengkap. Tiap fase punya deliverable konkret yang bisa di-demo.

---

## 1. Filosofi Roadmap

1. **MVP dulu, fitur kemudian.** Sistem harus bisa dipakai end-to-end dengan minimum stream sebelum mengejar kelengkapan.
2. **Bangun fondasi yang kokoh sekali.** Master data, auth, assessment workflow → harus solid sebelum lanjut.
3. **AI ditambahkan bertahap.** Mulai dari fitur sederhana (draft justifikasi), baru ke yang kompleks (RAG, summary).
4. **HCR & stream kompleks belakangan.** Sesuai instruksi: ruangnya disiapkan, implementasi penuh setelah stream lain stabil.

---

## 2. Visualisasi Fase

```
Fase 1  ─► Fase 2  ─► Fase 3  ─► Fase 4  ─► Fase 5  ─► Fase 6
Foundation Workflow   Dashboard  Compliance AI Assist  Full Coverage
(2-3 mgg) (2-3 mgg)  (1-2 mgg)  (1-2 mgg)  (2 mgg)    (3-4 mgg)
                                                       
Total estimasi: 11-16 minggu untuk full release.
MVP usable di akhir Fase 3 (≈ 5-8 minggu).
```

---

## 3. Fase 1 — Foundation (Master Data + Auth)

**Tujuan:** Aplikasi bisa di-login, master data Konkin 2026 sudah ter-input, struktur stream bisa dibrowse.

### Deliverable:
- ✅ Backend FastAPI skeleton + database PostgreSQL + migrasi awal
- ✅ Frontend React + routing + login page + auth flow
- ✅ Schema database lengkap (sesuai `03_DATA_MODEL.md`)
- ✅ Seed script untuk Konkin 2026 PLTU Tenayan (struktur perspektif + indikator + bobot)
- ✅ User management (CRUD user, assign role, assign bidang)
- ✅ Master Data UI: browse perspektif → indikator → stream ML structure (read-only)
- ✅ Editor JSONB structure untuk admin (input rubrik per stream)
- ✅ Setup Docker Compose dev + prod
- ✅ Auth: JWT, login/logout, refresh token, role-based middleware
- ✅ Skeuomorphic component primitives: SkButton, SkInput, SkPanel, SkScreenLcd

### Stream yang di-seed di fase ini:
- **Outage Management** (sudah lengkap rubriknya di Pedoman)
- **SMAP** (dari `kertas_kerja_Kepatuhan_2026.xlsx`)
- 1-2 KPI Kuantitatif sederhana: **EAF**, **EFOR**

### Acceptance Criteria:
- Admin bisa login, navigate ke /master/konkin-template/2026, lihat 6 perspektif + indikator
- PIC bisa login dan lihat indikator yang di-assign ke bidangnya (read-only)
- Health check `/api/v1/health` returns OK
- `make seed` jalan tanpa error

### Estimasi: **2-3 minggu**

---

## 4. Fase 2 — Assessment Workflow (PIC + Asesor)

**Tujuan:** End-to-end self-assessment + asesor review + rekomendasi untuk indikator pilot (Outage + SMAP + EAF + EFOR).

### Deliverable:
- ✅ Periode management UI (admin)
- ✅ Assessment Session creation (auto saat periode dibuka)
- ✅ Self-Assessment Form untuk **KPI Kuantitatif** (EAF, EFOR)
- ✅ Self-Assessment Form untuk **Maturity Level** (Outage, SMAP)
- ✅ Auto-save draft + dirty state indicator
- ✅ Asesor Workspace: antrian, review, approve/override/return
- ✅ Recommendation creation di asesmen
- ✅ Recommendation Tracker untuk PIC (update progress)
- ✅ Asesor verify & close recommendation
- ✅ Carry-over rekomendasi otomatis saat periode close
- ✅ Notification system (in-app, basic)
- ✅ Skeuomorphic components advanced: LevelSelector dial, MaturityLevelTree

### Acceptance Criteria:
- PIC dapat input self-assessment EAF dan submit
- PIC dapat isi maturity level Outage Management semua sub-area
- Asesor dapat review, override nilai, beri rekomendasi
- Rekomendasi muncul di dashboard PIC untuk triwulan berikutnya
- Workflow terjadi end-to-end dengan minimal 5 user (1 admin, 2 PIC, 1 asesor, 1 manajer)

### Estimasi: **2-3 minggu**

---

## 5. Fase 3 — NKO Calculator + Dashboard

**Tujuan:** NKO terhitung otomatis, dashboard eksekutif bisa dilihat manajer.

### Deliverable:
- ✅ NKO calculation engine (sesuai formula di `01_DOMAIN_MODEL.md`)
- ✅ Auto-trigger calculation setiap perubahan assessment
- ✅ NKO snapshot history
- ✅ Dashboard Eksekutif:
  - Big NKO Gauge (skeuomorphic analog meter)
  - Pilar cards dengan trend
  - Heatmap maturity level
  - Top performers / needs attention list
  - Forecast NKO akhir semester
- ✅ Trend charts per indikator
- ✅ WebSocket untuk real-time NKO update di dashboard
- ✅ Drill-down: Pilar → Indikator → Detail komponen

### Acceptance Criteria:
- Saat asesor approve sebuah indikator, NKO total update real-time di dashboard
- Manajer Unit bisa lihat dashboard dengan semua visualisasi
- Drill-down navigation berfungsi
- Forecast NKO masuk akal (linear regression dari TW yang sudah ada)

### Estimasi: **1-2 minggu**

### → Akhir Fase 3 = MVP USABLE

Aplikasi sudah bisa dipakai untuk operasional triwulanan dengan **minimum 4 indikator** (EAF, EFOR, Outage ML, SMAP). Sudah cukup untuk soft-launch internal.

---

## 6. Fase 4 — Compliance Tracker + Reports

**Tujuan:** Compliance pengurang NKO ter-track, laporan formal bisa di-export.

### Deliverable:
- ✅ Compliance Laporan Tracker:
  - Master 9 jenis laporan rutin
  - Form input submission (tanggal submit, valid data)
  - Auto-calculate pengurang
- ✅ Compliance Komponen lain (PACA, ICOFR, NAC, Critical Event)
- ✅ Total pengurang Compliance integrated ke NKO calculation
- ✅ Export Excel: kertas kerja per stream (mirror format existing)
- ✅ Export PDF: Laporan NKO semester resmi (template)
- ✅ Export Word: Executive summary
- ✅ Compliance dashboard view

### Acceptance Criteria:
- BID CPF dapat input bahwa Laporan Pengusahaan Mei terlambat 2 hari → pengurang otomatis -0.078
- NKO total terkoreksi setelah pengurang Compliance ditambahkan
- Manajer bisa export laporan NKO TW2 2026 ke PDF dengan format profesional
- Export Excel kertas kerja bisa dibuka di MS Excel tanpa error

### Estimasi: **1-2 minggu**

---

## 7. Fase 5 — AI Integration

**Tujuan:** Fitur AI yang menambah produktivitas user.

### Deliverable:
- ✅ Setup OpenRouter client + routing
- ✅ AI Suggestion Drawer component (UX pattern)
- ✅ **Draft Justifikasi** (PIC) — pakai Gemini Flash
- ✅ **Draft Rekomendasi** (Asesor) — pakai Gemini Flash
- ✅ **Anomaly Detection** rule-based + LLM hybrid
- ✅ AI Suggestion audit log (`ai_suggestion_log`)
- ✅ Rate limiting per user (20/min)
- ✅ Fallback graceful jika OpenRouter down

### Sub-fase 5b (opsional, bisa Phase 2):
- ✅ Index Pedoman Konkin ke pgvector (`index_pedoman.py`)
- ✅ Chat RAG dengan Pedoman (Claude Sonnet)
- ✅ Smart Summary periode
- ✅ Action Plan Generator SMART

### Acceptance Criteria:
- PIC klik AI Assist saat isi catatan EAF → suggestion muncul dalam < 5 detik
- Suggestion bisa di-edit, accept, atau reject
- Asesor klik AI Assist saat tulis rekomendasi → struktur SMART muncul
- Anomaly detection memflag self-assessment dengan deviasi > 30% dari historis
- Audit log mencatat 100% AI request

### Estimasi: **2 minggu** (untuk Fase 5 inti, +1-2 minggu untuk RAG chat)

---

## 8. Fase 6 — Stream Coverage Lengkap + HCR

**Tujuan:** Semua stream maturity level Konkin 2026 ter-implementasi, HCR sudah berfungsi.

### Deliverable bertahap (per stream):

#### Batch 1 (mudah, struktur mirip Outage):
- Reliability Management
- Efficiency Management
- WPC Management

#### Batch 2 (medium):
- Operation Management (bobot ML 90%)
- Energi Primer (Batubara, Gas, BBM)
- LCCM
- SCM

#### Batch 3 (kompleks):
- Manajemen Lingkungan & K3 (bobot ML 75%)
- Manajemen Keamanan (bobot ML 60%)
- Pengelolaan Bendungan
- DPP Maturity Level

#### Batch 4 (HCR & OCR — paling kompleks, terakhir):
- HCR (Strategic Workforce Planning, Talent, Performance, dll)
- OCR (6 sub-area dengan bobot khusus untuk OWM)

#### Plus:
- Sub-indikator Pilar I (BPP komponen lengkap, SDGs komponen lengkap)
- Pilar IV: Disburse Investasi & PRK Terkontrak
- Pilar V: SPKI, Budaya, Diseminasi, dll

### Acceptance Criteria:
- Semua 14 sub-stream ML di Pilar II ter-input rubriknya
- Semua 5 indikator Pilar I ter-implementasi
- HCR self-assessment bisa dilakukan untuk minimal 1 area
- NKO total benar-benar mencakup semua kontribusi

### Estimasi: **3-4 minggu** (paralel dengan stabilisasi)

---

## 9. Phase 2+ — Future Enhancements

Setelah Fase 6 selesai dan aplikasi stabil di operasional:

### F+1: Multi-Unit
- Replikasi struktur untuk unit PLN NP lain (Paiton, Gresik, dll)
- Multi-tenant architecture (row-level security)
- Cross-unit benchmarking dashboard

### F+2: Advanced AI
- Forecasting NKO via ML time series (Prophet, ARIMA)
- Voice input untuk catatan via Whisper
- Auto-translate untuk laporan ke Bahasa Inggris
- Recommendation impact analysis (apakah rekomendasi yang ditindaklanjuti benar-benar improve next quarter?)

### F+3: Mobile App
- React Native untuk mobile (PIC bisa update progress di lapangan)
- Push notifications native

### F+4: Integration
- Sync dengan ERP/SAP untuk data BPP otomatis
- Sync dengan Navitas untuk data EAF/EFOR otomatis
- Webhook untuk Telegram/Teams notification

### F+5: Audit Trail Enhancements
- Compliance audit logs export
- Tamper-proof log via append-only with hash chain
- Independent auditor view (read-only role)

---

## 10. Resource Planning

### Tim Minimum (untuk Fase 1-3 paralel):
- 1 Tech Lead (Anda) — domain + arsitektur + review
- 1 Backend Developer (FastAPI + PostgreSQL)
- 1 Frontend Developer (React + skeuomorphic styling)
- 0.5 DevOps (deployment + infrastructure)

Untuk MVP cepat dengan 1 developer (Anda + Claude Code):
- Fase 1-3 estimasi 6-10 minggu (vs 5-8 minggu dengan tim 3 orang)
- Claude Code di VPS handle implementasi rutin, Anda fokus review + domain

---

## 11. Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Pedoman Konkin berubah di tahun depan | Schema sudah versioned per `konkin_template`, struktur baru = template baru, data lama tetap |
| Stream maturity level kompleks (HCR) | Ditunda ke Fase 6, ruang sudah disiapkan |
| User resistance ke sistem baru (terbiasa Excel) | Export Excel mirror format kertas kerja existing — user transisi gradually |
| OpenRouter quota habis / down | Fallback graceful, fitur AI optional, tidak block workflow inti |
| VPS spec terbatas | Backend pakai gunicorn 4 worker default, bisa scale dengan tambah CPU/RAM |
| Backup data hilang | Daily backup + weekly rsync ke external |
| Performance lambat saat banyak user | Index DB, materialized view dashboard, Redis cache, monitoring p95 |

---

## 12. Definition of Done (per fitur)

Setiap fitur dianggap "done" hanya kalau:
1. ✅ Backend endpoint berfungsi dengan auth + validation + audit log
2. ✅ Frontend UI sesuai design system skeuomorphic
3. ✅ Test scenario manual end-to-end pass
4. ✅ Database migration + seed (jika perlu) sudah committed
5. ✅ Dokumentasi minimal di docstring + update file blueprint kalau perlu
6. ✅ Logged: error rate, latency reasonable
7. ✅ Tidak ada regression di fitur sebelumnya

---

## 13. Milestone Demo Targets

| Milestone | Target Demo |
|-----------|-------------|
| End Fase 1 | Demo: login, browse master Konkin 2026, view stream Outage rubrik |
| End Fase 2 | Demo: Full workflow PIC isi EAF + Outage ML → asesor approve + beri rekomendasi |
| End Fase 3 | Demo: NKO live di dashboard, drill-down, heatmap |
| End Fase 4 | Demo: Compliance laporan terlambat → NKO terkoreksi, export PDF laporan |
| End Fase 5 | Demo: AI bantu draft justifikasi & rekomendasi, anomaly detected |
| End Fase 6 | Demo: Konkin 2026 PLTU Tenayan full coverage, semua indikator ter-track |

---

**Selanjutnya:** [`10_CLAUDE_CODE_INSTRUCTIONS.md`](10_CLAUDE_CODE_INSTRUCTIONS.md) — instruksi spesifik untuk Claude Code di VPS.
