# Context

> Domain, business, and operational context. DOC-class sources are appended verbatim with source attribution.
> The roadmap phase breakdown from 09_DEVELOPMENT_ROADMAP.md is preserved in full so the downstream
> roadmapper can consume it without round-tripping to the source files. Project-name references in the
> source DOCs still use "SISKONKIN"; per the locked ADR (UPDATE-001 / DEC-001) all such references
> are now "PULSE" — see decisions.md for the rebrand rule. The verbatim text below is preserved as the
> historical record; downstream consumers MUST treat the rebrand as authoritative.

---

## Topic 1 — Project overview (README.md)

- source: `C:/Users/ANUNNAKI/Projects/PULSE/README.md`

> PULSE (formerly SISKONKIN) is an internal application for monitoring, self-assessment, asesor review,
> and recommendation follow-up of the Kontrak Kinerja Unit (Konkin) at PLTU Tenayan, run quarterly.
> It replaces an Excel-based workflow (per-stream kertas kerja) with a structured, auditable, collaborative
> platform. Reference document: **Peraturan Direksi PT PLN Nusantara Power Nomor 0019.P/DIR/2025**
> (17 Juli 2025) about Pedoman Penilaian Kontrak Kinerja Unit; designed to accommodate Konkin 2026.

### Design philosophy (verbatim, README §"Filosofi Desain")
1. **Bukan sistem manajemen evidence.** Sistem ini adalah kertas kerja digital + workflow asesmen, bukan document repository. Evidence tetap dikelola oleh PIC bidang masing-masing di sistem internal mereka.
2. **Setiap stream punya rubrik unik.** Sistem dirancang dengan **dynamic schema per stream** — bukan one-size-fits-all form.
3. **Self-assessment → Asesor → Feedback → Tindak Lanjut.** Alur ini diterapkan konsisten di semua indikator, baik KPI kuantitatif maupun Maturity Level.
4. **Triwulan sebagai irama monitoring, semester sebagai irama formal.** Konkin formal dinilai per semester, tapi monitoring & koreksi arah dilakukan per triwulan.
5. **AI sebagai asisten, bukan pengganti asesor.** LLM membantu menulis rekomendasi, mendeteksi anomali, dan mempercepat self-assessment — keputusan tetap di manusia.

### Standing notes (verbatim, README §"Catatan Penting")
- **Tidak ada upload file evidence.** Field `link_eviden` cukup berupa text/URL ke sistem eksternal (Google Drive, SharePoint, atau path internal unit).
- **Setiap stream maturity level punya rubrik berbeda.** Schema database menggunakan pola JSONB untuk fleksibilitas, bukan tabel statis.
- **HCR akan ditambahkan kemudian.** Schema dan modul sudah disiapkan ruangnya, implementasi penuh setelah MVP stream lain stabil.

---

## Topic 2 — Domain hierarchy: Kontrak Kinerja Unit

- source: `C:/Users/ANUNNAKI/Projects/PULSE/01_DOMAIN_MODEL.md` §1

```
Kontrak Kinerja Unit (per tahun, ditetapkan oleh Direksi)
└── Periode (Semester 1, Semester 2)
    └── Perspektif (5 Pilar BUMN + Compliance)
        └── Indikator Kinerja Utama (KPI)
            └── Sub-Indikator / Stream Maturity Level (untuk indikator agregat)
                └── Area / Sub-Area (untuk Maturity Level)
                    └── Kriteria Level 0-5
```

---

## Topic 3 — Konkin 2026 PLTU Tenayan: Perspektif & Bobot

- source: `01_DOMAIN_MODEL.md` §2 (FMZ-12.1.2.1)

| Kode | Perspektif | Bobot | Sifat |
|------|-----------|------:|-------|
| I | Economic & Social Value | 46.00 | Penambah |
| II | Model Business Innovation | 25.00 | Penambah |
| III | Technology Leadership | 6.00 | Penambah |
| IV | Energize Investment | 8.00 | Penambah |
| V | Unleash Talent | 15.00 | Penambah |
| VI | Compliance | Max -10 | Pengurang |
| | **JUMLAH (I+II+III+IV+V)** | **100.00** | |

**Formula NKO Akhir:** `NKO = Σ(Nilai Pilar I s/d V) − Nilai Pengurang Compliance`

Worked example (NKO Semester 2 2025 PLTU Tenayan):
`NKO = 58.12 + 10.65 + 15.38 + 8.36 + 11.30 = 103.80`
`NKO Final = 103.80 − 0.44 = 103.36`

---

## Topic 4 — Indikator inventory (Konkin 2026)

- source: `01_DOMAIN_MODEL.md` §3

### 3.1 Economic & Social Value (Bobot 46)
- Pengendalian Komponen BPP Unit (18, Positif, Agregat 5 sub: a Biaya Pemeliharaan 70/30 split UP Tenayan/PLTU Tembilahan, b Fisik Pemeliharaan 70/30, c Biaya Administrasi, d Biaya Kimia & Pelumas, e Penghapusan ATTB)
- Optimalisasi Kesiapan Pasokan Pembangkit (6, Positif, KPI Kuantitatif)
- EAF (6, Positif, KPI Kuantitatif)
- EFOR (6, Negatif, KPI Kuantitatif)
- Pengelolaan SDGs (10, Positif, Agregat 7 sub: TJSL, Tingkat Proper Unit, ERM, Intensitas Emisi, Kepuasan Pelanggan & Tindaklanjut, Umur Persediaan Batubara, Implementasi Digitalisasi Pembayaran)

### 3.2 Model Business Innovation (Bobot 25)
- Maturity Level Manajemen Aset Pembangkitan (25, Maturity Level Agregat dari 14 sub-stream rata-rata: Outage, WPC, Operation, Reliability, Efficiency, LCCM, Pengelolaan Energi Primer, SCM, DPP, Pengelolaan Keuangan, Manajemen Lingkungan, Manajemen K3, Manajemen Keamanan, SMAP)

### 3.3 Technology Leadership (Bobot 6)
- SFC Batubara (6, Negatif, formula `Σ Volume Bahan Bakar / Σ kWh Produksi Bruto`)

### 3.4 Energize Investment (Bobot 8)
- Disburse Investasi & PRK Investasi Terkontrak (8, Agregat 4 sub: a1 Disburse UP Tenayan Non Tembilahan 70%, a2 Disburse PLTU Tembilahan 30%, b1 PRK UP Tenayan 70%, b2 PRK Tembilahan 30%)

### 3.5 Unleash Talent (Bobot 15)
- Pengelolaan Human Capital, Inovasi & Safety Culture (15, Agregat 8 sub: HCR, OCR, SPKI PLN NP, Penguatan Budaya, Diseminasi Karya Inovasi, Biaya Kesehatan, LTIFR target 0.106 indeks, Kontribusi Project Korporat)

### 3.6 Compliance (Pengurang Max -10)
Pengurang NKO atas: Komitmen Kepatuhan & Ketepatan Laporan & Validitas Data; Penyelesaian Temuan Audit; Penyelesaian Rekomendasi OFI; SLA Tiket & Awareness Cyber; HSSE & Regulasi; PACA; Critical Event; ICOFR; Pengendalian NAC sesuai RKAU 2026.

---

## Topic 5 — Two indicator types: KPI Kuantitatif vs Maturity Level

- source: `01_DOMAIN_MODEL.md` §4

### 5.1 KPI Kuantitatif
Pola umum: `Pencapaian (%) = f(Realisasi, Target)`; `Nilai = Pencapaian × Bobot`.

- **Polaritas Positif:** `Pencapaian = (Realisasi / Target) × 100%`
- **Polaritas Negatif:** `Pencapaian = {2 − (Realisasi / Target)} × 100%`
- **Range-based (Kepuasan Pelanggan):**
  - Jika realisasi < rentang_bawah: `Pencapaian = (realisasi / rentang_bawah) × 100%`
  - Jika rentang_bawah ≤ realisasi ≤ rentang_atas: `Pencapaian = 100%`
  - Jika realisasi > rentang_atas: `Pencapaian = (realisasi / rentang_atas) × 100%`

Example (Pedoman hal 5-6): Anggaran Biaya Har Rp 200 mly; Realisasi Rp 190 mly → `Pencapaian = (2 − 190/200) × 100% = 105%`; Bobot 3 → Nilai = 3.15.

### 5.2 Maturity Level — discrete rubric Level 0–5
| Level | Range | Definisi |
|-------|-------|----------|
| 0 | ≤1 | Fire Fighting |
| 1 | 1<x≤2 | Stabilizing |
| 2 | 2<x≤3 | Preventing |
| 3 | 3<x≤4 | Optimizing |
| 4 | 4<x≤5 | Excellence |

Each stream has its own area/sub-area breakdown with **distinct descriptive criteria per level**. Source of "rumit" — every kertas kerja unique. Examples: Outage Management (Long Term Planning → P3 → Pre/During/Post Outage); SMAP (klausul 4.1/4.2/6.2/7.4/7.5 → Pilar Pencegahan → Elemen → Sub-Elemen → Pengukuran → Indikator); HCR (Strategic Workforce Planning, Talent Acquisition, Talent Mgmt & Development, Performance Mgmt, Reward & Recognition, Industrial Relation, HC Operations).

### 5.3 Stream-level ML vs KPI weight (Tabel 1)
| Stream | Bobot ML | Bobot KPI |
|---|---:|---:|
| Outage Management | 50% | 50% |
| Reliability Management | 50% | 50% |
| SCM Pembangkit | 50% | 50% |
| Efficiency Management | 50% | 50% |
| Operation Management | 90% | 10% |
| WPC Management | 50% | 50% |
| Energi Primer (Batubara, Biomassa) | 50% | 50% |
| Energi Primer (Gas) | 70% | 30% |
| Energi Primer (BBM/BBN) | 70% | 30% |
| Digital Power Plant | 50% | 50% |
| LCCM | 50% | 50% |
| Manajemen Lingkungan & K3 | 75% | 25% |
| Manajemen Keamanan | 60% | 40% |
| HCR | 50% | 50% |
| OCR (per sub) | 50% | 50% |
| OCR OWM | 55% | 45% |
| Pengelolaan Bendungan | 50% | 50% |

### 5.4 Sub-KPI averaging rules (Tabel 2)
- Biaya & Fisik Pemeliharaan: 50/50; if fisik tidak dinilai, biaya = 100%.
- Pengelolaan Komunikasi/TJSL/Proper: rata-rata, Komunikasi & TJSL diatur pedoman terlampir.
- LCCM-PSM, ERM-Keuangan, WPC-Outage, Reliability-Efficiency, Operation-EnergiPrimer pairs: 50/50; if one not assessed, the other = 100%.
- Biaya & PRK Investasi Terkontrak: 50/50 (same rule).
- HCR/OCR/Pra Karya Inovasi: rata-rata, normalisasi bobot if missing.
- Manajemen Lingkungan/K3/Keamanan: rata-rata realisasi ML, normalisasi if missing.

---

## Topic 6 — Periode rhythm

- source: `01_DOMAIN_MODEL.md` §6

| Indikator | Periode |
|---|---|
| Sebagian besar KPI Kuantitatif | Semester (S1, S2) |
| Maturity Level | Semester |
| Beberapa monitoring (FRA, gratifikasi, dst) | Triwulan (TW1–TW4) |
| Sub-indikator HSE, Compliance | Bulanan/Triwulan |

**System strategy:** monitoring berbasis triwulan untuk semua indikator (TW1–TW4), agregasi resmi per semester (TW1+TW2 = S1, TW3+TW4 = S2). Granular visibility versus 2x/year-only.

---

## Topic 7 — Pemilik Proses (process owners) — partial seed list

- source: `01_DOMAIN_MODEL.md` §7

| Indikator | Pemilik Proses |
|---|---|
| Biaya Pemeliharaan | BID FIN, BID ACT |
| Fisik Pemeliharaan | BID OM-1..5, OM-RE |
| EAF, EFOR, Optimalisasi Pasokan | BID OM (semua) |
| SFC Batubara | BID OM-1, 2, 3 |
| Reliability Management | BID REL-1, REL-2 |
| HCR, OCR | BID HTD (+ HSC for OCR) |
| Manajemen Lingkungan, K3 | BID HSE |
| ERM | BID RIS |
| SCM | SSCM |
| Komitmen Ketepatan Laporan | BID CPF |
| Penyelesaian Temuan Audit | BID AUD-I, II, III |

Full list lives in Pedoman Tabel 26; will be seeded as master data.

---

## Topic 8 — Compliance laporan rutin (Tabel 22)

- source: `01_DOMAIN_MODEL.md` §8

UP-level (e.g. UP Tenayan): total laporan **64/year**; pengurang per laporan tidak tepat waktu = **0.039**; pengurang per laporan tidak valid = **0.039**.

| # | Jenis Laporan | Frekuensi | PIC | Deadline |
|---|---|---|---|---|
| 1 | Laporan Pengusahaan | Bulanan | BID OM | Tgl 5 |
| 2 | Berita Acara Transfer Energi | Bulanan | BID CMR | Tgl 5 |
| 3 | Laporan Keuangan | Triwulan | BID ACT | Sesuai target KP |
| 4 | Panduan Monitoring & Evaluasi BPP | Triwulan | BID ACT | H+7 closing |
| 5 | Laporan Kinerja Investasi & Penurunan BPP | Bulanan | BID FIN | Tgl 5 |
| 6 | Laporan Manajemen Risiko & Kepatuhan | Triwulan | BID RIS | Akhir bulan periode |
| 7 | Laporan Self Assessment | Triwulan | BID CPF | Tgl 7 bulan berikutnya |
| 8 | Laporan Manajemen Material | Bulanan | BID LOG | Tgl 10 |
| 9 | Pengisian Navitas | Semester / Setiap Hari | BID OM | -0.01 per hari telat |

---

## Topic 9 — Glosarium (acronyms in scope)

- source: `01_DOMAIN_MODEL.md` §9

NKO Nilai Kinerja Organisasi · Konkin Kontrak Kinerja · RKAU Rencana Kerja Anggaran Unit · RKAP Rencana Kerja Anggaran Perusahaan · PRK Program Rencana Kerja · RUPS Rapat Umum Pemegang Saham · BPP Biaya Pokok Penyediaan · EAF Equivalent Availability Factor · EFOR Equivalent Forced Outage Rate · SFC Specific Fuel Consumption · ATTB Aktiva Tetap Tidak Beroperasi · DMN Daya Mampu Netto · DMP Daya Mampu Pasok · DPP Digital Power Plant · HCR Human Capital Readiness · OCR Organization Capital Readiness · LCCM Life Cycle Cost Management · WPC Work Planning & Control · SCM Supply Chain Management · ERM Enterprise Risk Management · SMAP Sistem Manajemen Anti Penyuapan · SDGs Sustainable Development Goals · TJSL Tanggung Jawab Sosial dan Lingkungan · K3/K3LH Keselamatan & Kesehatan Kerja (& Lingkungan Hidup) · LTIFR Lost Time Injury Frequency Rate · OFI Opportunity For Improvement · PACA Planning Accuracy Compliance Adjustment · ICOFR Internal Control Over Financial Reporting · NAC Non Allowable Cost · FKAP Fungsi Kepatuhan Anti Penyuapan · SPKI Sertifikasi Profesi Karya Inovasi (PLN NP) · BID Bidang · BID OM/REL/HSE/HTD/HSC/CMR/FIN/ACT/RIS/CPF/AUD/CSR/EPI/TDV — see source for full mapping · SSCM Satuan Supply Chain Management · SPRO Satuan Project · DIVPKP Divisi Penilaian Kinerja Perusahaan.

---

## Topic 10 — Onboarding instructions for the build agent

- source: `C:/Users/ANUNNAKI/Projects/PULSE/10_CLAUDE_CODE_INSTRUCTIONS.md`

### 10.1 Reading order (mandatory before coding)
1. README.md → 2. 01_DOMAIN_MODEL → 3. 02_FUNCTIONAL_SPEC → 4. 03_DATA_MODEL → 5. 04_API_SPEC → 6. 05_FRONTEND_ARCHITECTURE → 7. 06_DESIGN_SYSTEM_SKEUOMORPHIC → 8. 07_AI_INTEGRATION → 9. 08_DEPLOYMENT → 10. 09_DEVELOPMENT_ROADMAP. Summarize understanding to Budi before coding.

### 10.2 Coding rules (verbatim §5)

**Backend (Python):** 3.11+ with type hints; async/await for all DB & HTTP; Pydantic v2; SQLAlchemy 2.x async session; black + ruff; Google-style docstrings; snake_case/PascalCase/UPPER_CASE; **no raw SQL string concatenation**; structured logging (structlog or JSON); every mutating endpoint logs to `audit_log`.

**Frontend (TS/React):** strict TS (no `any` w/o comment); functional components + hooks; explicit `Props` interfaces; TanStack Query for all server state; React Hook Form + Zod for all forms; PascalCase components / camelCase utilities; no inline style — Tailwind utilities or design tokens; skeuomorphic components must follow the design system.

**Database:** descriptive migration filenames; soft delete via `deleted_at`; audit columns on all main tables; index frequently filtered/joined columns; JSONB for dynamic structures.

**Git commit:** Conventional Commits (`feat(scope):`, `fix(scope):`, `chore(scope):`, `docs(scope):`, `refactor(scope):`); BI or English consistently per repo.

### 10.3 Must-do (verbatim §6)
- Read all blueprint docs before starting
- Ask when ambiguous
- Manual test each feature
- BI for UI strings
- Follow skeuomorphic design system
- Implement audit log for every mutating action
- Pydantic + Zod validation (defense in depth)
- Soft delete, never hard delete
- Commit incrementally with clear messages
- Update docs when new technical decisions are made

### 10.4 Must-NOT-do (verbatim §7)
- Build evidence-upload subsystem (text/URL only)
- Hard-code maturity-level rubrics (use JSONB structure)
- Use generic fonts (Inter, Roboto, Arial) — use design-system fonts
- Generic SaaS styling (purple-pink gradient, flat white cards) — use skeuomorphic
- Send PII to LLM without filtering
- Auto-approve assessment — always asesor manual
- Duplicate NKO calculation logic in BE & FE — backend authoritative only
- Skip audit log for shortcuts
- Implement HCR fully now — defer to Fase 6
- Commit `.env` (only `.env.example`)

### 10.5 Open questions to confirm with Budi (verbatim §8)
1. Domain & SSL: final domain, Let's Encrypt vs internal CA?
2. OpenRouter API Key: ready and budget approved?
3. VPS spec: RAM/CPU/disk — drives gunicorn worker count and Redis limit.
4. First super admin: who?
5. Real vs dummy data for Fase 1-2?
6. External integration plans (Navitas, SAP) — webhook from start?
7. Internal SMTP available, or SendGrid/Mailgun?
8. Off-site backup (NAS or S3-compatible)?

(Items 1, 2, 7, 8 partially superseded by ADR DEC-011 — domain is `pulse.tenayan.local`; logo final, SSL, OpenRouter key, integrations all explicitly DEFERRED in the ADR.)

### 10.6 Definition of MVP stop point (verbatim §11)
- [x] Login berfungsi untuk semua role
- [x] Admin bisa setup periode TW2 2026
- [x] PIC bisa isi self-assessment EAF (KPI Kuantitatif)
- [x] PIC bisa isi self-assessment Outage Management (Maturity Level)
- [x] Asesor bisa review & beri rekomendasi
- [x] PIC bisa update progress rekomendasi
- [x] Asesor bisa close rekomendasi
- [x] Dashboard menampilkan NKO real-time dengan minimum 4 indikator
- [x] Export ke Excel kertas kerja berfungsi
- [x] Aplikasi accessible via `http://VPS_IP:3399`
- [x] Backup harian sudah scheduled

After MVP → demo to Budi before continuing to Fase 4.

---

## Topic 11 — Development roadmap (verbatim from 09_DEVELOPMENT_ROADMAP.md)

- source: `C:/Users/ANUNNAKI/Projects/PULSE/09_DEVELOPMENT_ROADMAP.md`
- note: This is preserved verbatim so the downstream `gsd-roadmapper` can lift the phasing without re-reading the source. The two AI features locked in by the ADR (DEC-004, DEC-005) are listed under Fase 5 with the updated deliverable list from `decisions.md` DEC-008.

### 11.1 Filosofi Roadmap (verbatim §1)
1. **MVP dulu, fitur kemudian.** Sistem harus bisa dipakai end-to-end dengan minimum stream sebelum mengejar kelengkapan.
2. **Bangun fondasi yang kokoh sekali.** Master data, auth, assessment workflow → harus solid sebelum lanjut.
3. **AI ditambahkan bertahap.** Mulai dari fitur sederhana (draft justifikasi), baru ke yang kompleks (RAG, summary).
4. **HCR & stream kompleks belakangan.** Sesuai instruksi: ruangnya disiapkan, implementasi penuh setelah stream lain stabil.

### 11.2 Visualisasi Fase (verbatim §2)
```
Fase 1  ─► Fase 2  ─► Fase 3  ─► Fase 4  ─► Fase 5  ─► Fase 6
Foundation Workflow   Dashboard  Compliance AI Assist  Full Coverage
(2-3 mgg) (2-3 mgg)  (1-2 mgg)  (1-2 mgg)  (2 mgg)    (3-4 mgg)

Total estimasi: 11-16 minggu untuk full release.
MVP usable di akhir Fase 3 (≈ 5-8 minggu).
```

### 11.3 Fase 1 — Foundation (Master Data + Auth) (verbatim §3)
**Tujuan:** Aplikasi bisa di-login, master data Konkin 2026 sudah ter-input, struktur stream bisa dibrowse.

**Deliverable:**
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

**Stream yang di-seed di fase ini:**
- Outage Management (sudah lengkap rubriknya di Pedoman)
- SMAP (dari `kertas_kerja_Kepatuhan_2026.xlsx`)
- 1-2 KPI Kuantitatif sederhana: EAF, EFOR

**Acceptance Criteria:**
- Admin bisa login, navigate ke /master/konkin-template/2026, lihat 6 perspektif + indikator
- PIC bisa login dan lihat indikator yang di-assign ke bidangnya (read-only)
- Health check `/api/v1/health` returns OK
- `make seed` jalan tanpa error

**Estimasi:** 2-3 minggu

### 11.4 Fase 2 — Assessment Workflow (PIC + Asesor) (verbatim §4)
**Tujuan:** End-to-end self-assessment + asesor review + rekomendasi untuk indikator pilot (Outage + SMAP + EAF + EFOR).

**Deliverable:**
- ✅ Periode management UI (admin)
- ✅ Assessment Session creation (auto saat periode dibuka)
- ✅ Self-Assessment Form untuk KPI Kuantitatif (EAF, EFOR)
- ✅ Self-Assessment Form untuk Maturity Level (Outage, SMAP)
- ✅ Auto-save draft + dirty state indicator
- ✅ Asesor Workspace: antrian, review, approve/override/return
- ✅ Recommendation creation di asesmen
- ✅ Recommendation Tracker untuk PIC (update progress)
- ✅ Asesor verify & close recommendation
- ✅ Carry-over rekomendasi otomatis saat periode close
- ✅ Notification system (in-app, basic)
- ✅ Skeuomorphic components advanced: LevelSelector dial, MaturityLevelTree

**Acceptance Criteria:**
- PIC dapat input self-assessment EAF dan submit
- PIC dapat isi maturity level Outage Management semua sub-area
- Asesor dapat review, override nilai, beri rekomendasi
- Rekomendasi muncul di dashboard PIC untuk triwulan berikutnya
- Workflow terjadi end-to-end dengan minimal 5 user (1 admin, 2 PIC, 1 asesor, 1 manajer)

**Estimasi:** 2-3 minggu

### 11.5 Fase 3 — NKO Calculator + Dashboard (verbatim §5)
**Tujuan:** NKO terhitung otomatis, dashboard eksekutif bisa dilihat manajer.

**Deliverable:**
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

**Acceptance Criteria:**
- Saat asesor approve sebuah indikator, NKO total update real-time di dashboard
- Manajer Unit bisa lihat dashboard dengan semua visualisasi
- Drill-down navigation berfungsi
- Forecast NKO masuk akal (linear regression dari TW yang sudah ada)

**Estimasi:** 1-2 minggu

**→ Akhir Fase 3 = MVP USABLE**

Aplikasi sudah bisa dipakai untuk operasional triwulanan dengan minimum 4 indikator (EAF, EFOR, Outage ML, SMAP). Sudah cukup untuk soft-launch internal.

### 11.6 Fase 4 — Compliance Tracker + Reports (verbatim §6)
**Tujuan:** Compliance pengurang NKO ter-track, laporan formal bisa di-export.

**Deliverable:**
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

**Acceptance Criteria:**
- BID CPF dapat input bahwa Laporan Pengusahaan Mei terlambat 2 hari → pengurang otomatis -0.078
- NKO total terkoreksi setelah pengurang Compliance ditambahkan
- Manajer bisa export laporan NKO TW2 2026 ke PDF dengan format profesional
- Export Excel kertas kerja bisa dibuka di MS Excel tanpa error

**Estimasi:** 1-2 minggu

### 11.7 Fase 5 — AI Integration (UPDATED per ADR)
**Tujuan:** Fitur AI yang menambah produktivitas user.

**Deliverable (post-ADR — supersedes the source's deliverable list):**
- ✅ Setup OpenRouter client + routing
- ✅ AI Suggestion Drawer component (UX pattern)
- ✅ **Draft Justifikasi** (PIC) — pakai Gemini Flash
- ✅ **Draft Rekomendasi** (Asesor) — pakai Gemini Flash
- ✅ **Anomaly Detection** rule-based + LLM hybrid
- ✅ **AI Inline Help** untuk indikator (NEW — DEC-004 / REQ-ai-inline-help)
- ✅ **Comparative Analysis** cross-periode (NEW — DEC-005 / REQ-ai-comparative-analysis)
- ✅ AI Suggestion audit log (`ai_suggestion_log`)
- ✅ Rate limiting per user (20/min)
- ✅ Fallback graceful jika OpenRouter down

**Sub-fase 5b (opsional, bisa Phase 2):**
- ✅ Index Pedoman Konkin ke pgvector (`index_pedoman.py`)
- ✅ Chat RAG dengan Pedoman (Claude Sonnet)
- ✅ Smart Summary periode
- ✅ Action Plan Generator SMART

**Acceptance Criteria:**
- PIC klik AI Assist saat isi catatan EAF → suggestion muncul dalam < 5 detik
- Suggestion bisa di-edit, accept, atau reject
- Asesor klik AI Assist saat tulis rekomendasi → struktur SMART muncul
- Anomaly detection memflag self-assessment dengan deviasi > 30% dari historis
- Audit log mencatat 100% AI request

**Estimasi:** 2 minggu (untuk Fase 5 inti, +1-2 minggu untuk RAG chat)

### 11.8 Fase 6 — Stream Coverage Lengkap + HCR (verbatim §8)
**Tujuan:** Semua stream maturity level Konkin 2026 ter-implementasi, HCR sudah berfungsi.

**Deliverable bertahap (per stream):**

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

**Acceptance Criteria:**
- Semua 14 sub-stream ML di Pilar II ter-input rubriknya
- Semua 5 indikator Pilar I ter-implementasi
- HCR self-assessment bisa dilakukan untuk minimal 1 area
- NKO total benar-benar mencakup semua kontribusi

**Estimasi:** 3-4 minggu (paralel dengan stabilisasi)

### 11.9 Phase 2+ — Future Enhancements (verbatim §9)

- **F+1: Multi-Unit** — replikasi struktur untuk unit PLN NP lain (Paiton, Gresik, dll); multi-tenant via row-level security; cross-unit benchmarking dashboard.
- **F+2: Advanced AI** — Forecasting NKO via ML time series (Prophet, ARIMA); voice input via Whisper; auto-translate to English; recommendation-impact analysis.
- **F+3: Mobile App** — React Native; push notifications native.
- **F+4: Integration** — Sync ERP/SAP for BPP; sync Navitas for EAF/EFOR; webhooks Telegram/Teams.
- **F+5: Audit Trail Enhancements** — Compliance audit-log export; tamper-proof append-only with hash chain; independent auditor view (read-only role).

### 11.10 Resource Planning (verbatim §10)
**Tim Minimum (untuk Fase 1-3 paralel):**
- 1 Tech Lead (domain + arsitektur + review)
- 1 Backend Developer (FastAPI + PostgreSQL)
- 1 Frontend Developer (React + skeuomorphic styling)
- 0.5 DevOps (deployment + infrastructure)

For solo MVP path (1 dev + Claude Code): Fase 1-3 estimate 6-10 weeks (vs 5-8 with 3-person team).

### 11.11 Risk & Mitigation (verbatim §11)
| Risk | Mitigation |
|------|-----------|
| Pedoman Konkin berubah di tahun depan | Schema sudah versioned per `konkin_template`, struktur baru = template baru, data lama tetap |
| Stream maturity level kompleks (HCR) | Ditunda ke Fase 6, ruang sudah disiapkan |
| User resistance ke sistem baru (terbiasa Excel) | Export Excel mirror format kertas kerja existing — user transisi gradually |
| OpenRouter quota habis / down | Fallback graceful, fitur AI optional, tidak block workflow inti |
| VPS spec terbatas | Backend pakai gunicorn 4 worker default, bisa scale dengan tambah CPU/RAM |
| Backup data hilang | Daily backup + weekly rsync ke external |
| Performance lambat saat banyak user | Index DB, materialized view dashboard, Redis cache, monitoring p95 |

### 11.12 Definition of Done per fitur (verbatim §12)
1. ✅ Backend endpoint berfungsi dengan auth + validation + audit log
2. ✅ Frontend UI sesuai design system skeuomorphic
3. ✅ Test scenario manual end-to-end pass
4. ✅ Database migration + seed (jika perlu) sudah committed
5. ✅ Dokumentasi minimal di docstring + update file blueprint kalau perlu
6. ✅ Logged: error rate, latency reasonable
7. ✅ Tidak ada regression di fitur sebelumnya

### 11.13 Milestone Demo Targets (verbatim §13)
| Milestone | Target Demo |
|-----------|-------------|
| End Fase 1 | Demo: login, browse master Konkin 2026, view stream Outage rubrik |
| End Fase 2 | Demo: Full workflow PIC isi EAF + Outage ML → asesor approve + beri rekomendasi |
| End Fase 3 | Demo: NKO live di dashboard, drill-down, heatmap |
| End Fase 4 | Demo: Compliance laporan terlambat → NKO terkoreksi, export PDF laporan |
| End Fase 5 | Demo: AI bantu draft justifikasi & rekomendasi, anomaly detected, **+ AI Inline Help & Comparative Analysis (per ADR)** |
| End Fase 6 | Demo: Konkin 2026 PLTU Tenayan full coverage, semua indikator ter-track |

---

## Topic 12 — Cross-cutting principles (carry-over from blueprint set)

- AI is assistive, never decisive — every suggestion editable / rejectable; audit trail mandatory.
- Backend is sole authority for NKO calculation — frontend never duplicates the math.
- Audit log is non-negotiable for every mutating operation.
- Every secret in `.env`, never committed; only `.env.example` in VCS.
- BI for all UI strings; English allowed in code identifiers/comments.
- Soft delete preferred; hard delete forbidden for record-of-truth tables.
- Skeuomorphic dark theme is the default look; light theme is a variant only.
