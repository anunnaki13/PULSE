# 10 — Instruksi untuk Claude Code (di VPS)

> Dokumen ini adalah **instruksi langsung untuk Claude Code** yang akan menarik repository ini di VPS dan menjalankan implementasi. Bacalah dokumen ini terlebih dahulu sebelum mulai coding.

---

## 1. Identitas & Konteks

Halo Claude. Anda adalah Claude Code yang dijalankan di VPS milik Budi (CV Panda Global Teknologi). Anda akan membangun aplikasi **SISKONKIN** — Sistem Monitoring Kontrak Kinerja PLTU Tenayan untuk PT PLN Nusantara Power.

**Yang harus Anda pahami sebelum mulai:**
1. Repository ini berisi **blueprint lengkap**, bukan kode jadi.
2. Tugas Anda adalah **menerjemahkan blueprint** ke kode produksi nyata.
3. Bahasa interaksi user (Budi): **Bahasa Indonesia**. Komen kode boleh English untuk konvensi internasional, tapi UI strings & dokumentasi user-facing wajib Bahasa Indonesia.
4. User bukan junior — dia technical lead. Hindari verbose explanation; tunjukkan kerja konkret.

---

## 2. Wajib Dibaca Berurutan

Sebelum nulis satu baris kode pun, baca dokumen ini berurutan:

1. `README.md` — overview proyek
2. `docs/01_DOMAIN_MODEL.md` — **paling penting**, pahami domain Konkin
3. `docs/02_FUNCTIONAL_SPEC.md` — modul & user roles
4. `docs/03_DATA_MODEL.md` — schema PostgreSQL
5. `docs/04_API_SPEC.md` — REST API contract
6. `docs/05_FRONTEND_ARCHITECTURE.md` — struktur React
7. `docs/06_DESIGN_SYSTEM_SKEUOMORPHIC.md` — design tokens (penting untuk UI yang khas)
8. `docs/07_AI_INTEGRATION.md` — strategi AI/LLM
9. `docs/08_DEPLOYMENT.md` — Docker Compose
10. `docs/09_DEVELOPMENT_ROADMAP.md` — fase yang harus dikerjakan

**Setelah membaca, ringkas pemahaman Anda ke Budi sebelum mulai coding.** Pastikan tidak ada miskomunikasi.

---

## 3. Folder Struktur Awal yang Harus Anda Buat

Saat pertama kali clone, repo ini hanya punya `docs/` + `README.md`. Anda perlu membuat:

```
siskonkin/
├── docs/                       ← sudah ada
├── README.md                    ← sudah ada
├── backend/                     ← BUAT
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── versions/
│   │   └── script.py.mako
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   ├── services/
│   │   │   └── ai/
│   │   ├── websocket/
│   │   └── scripts/
│   ├── tests/
│   └── Dockerfile
├── frontend/                    ← BUAT
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html
│   ├── src/
│   │   └── (sesuai 05_FRONTEND_ARCHITECTURE.md)
│   ├── public/
│   └── Dockerfile
├── nginx/                       ← BUAT
│   ├── nginx.conf
│   └── conf.d/
│       └── siskonkin.conf
├── infra/                       ← BUAT
│   ├── backup/
│   │   ├── pg_backup.sh
│   │   └── restore.sh
│   └── db/
│       └── init/
│           └── 01-extensions.sql   ← CREATE EXTENSION uuid-ossp, vector, pgcrypto
├── docker-compose.yml           ← BUAT
├── docker-compose.prod.yml      ← BUAT
├── docker-compose.dev.yml       ← BUAT
├── .env.example                 ← BUAT (sesuai 08_DEPLOYMENT.md)
├── .gitignore                   ← BUAT
├── Makefile                     ← BUAT
└── LICENSE                      ← skip atau placeholder
```

---

## 4. Urutan Pengembangan (Mengikuti Roadmap)

### Langkah 1: Setup Foundation
```bash
# Setelah Anda membaca semua docs:
1. Buat backend skeleton (FastAPI + SQLAlchemy + Alembic)
2. Buat schema database lengkap dari 03_DATA_MODEL.md
3. Generate initial migration: alembic revision --autogenerate -m "initial schema"
4. Buat seed script app/scripts/seed_konkin_2026.py
5. Buat frontend skeleton (Vite + React + TS + Tailwind)
6. Setup design tokens skeuomorphic di tailwind.config.ts + src/styles/skeuomorphic.css
7. Setup Docker Compose
8. Test: docker compose up -d, verifikasi semua container running
```

### Langkah 2: Auth & Users
```
- Implement JWT auth (login, refresh, logout, /me)
- Frontend: login page dengan styling skeuomorphic
- Implement role-based middleware
- Test: login sebagai admin, akses endpoint protected
```

### Langkah 3: Master Data Module
```
- API endpoints konkin/templates, perspektif, indikator, ml_stream
- Frontend: master data browser (admin)
- Stream ML structure editor (JSONB editor) — penting untuk admin
```

### Langkah 4: Assessment Workflow
```
- API endpoints assessment/sessions
- Frontend: PIC self-assessment workspace
- Component: KpiKuantitatifForm, MaturityLevelTree
- LevelSelector dial component (skeuomorphic)
- Asesor workspace
```

### Langkah 5+: Lanjutkan sesuai Roadmap

Setelah setiap langkah, **commit ke git dengan pesan deskriptif**, dan tanyakan ke Budi untuk review jika ada keputusan ambigu.

---

## 5. Aturan Coding

### Backend (Python)
- **Python 3.11+** dengan type hints di semua function signature
- **Async/await** untuk semua DB & HTTP operation
- **Pydantic v2** untuk schema validation
- **SQLAlchemy 2.x** dengan async session
- Format: **black** + **ruff**
- Import order: stdlib, third-party, local (auto-format dengan ruff)
- Docstring: Google style untuk function publik
- Naming: snake_case untuk variable/function, PascalCase untuk class, UPPER_CASE untuk constant
- **Tidak ada raw SQL string concatenation** — pakai SQLAlchemy ORM atau parameterized query
- **Logging structured** dengan `structlog` atau JSON formatter
- Setiap endpoint mutating wajib log ke `audit_log`

### Frontend (TypeScript/React)
- **Strict TypeScript** — no `any` kecuali sangat terpaksa & comment kenapa
- **Functional component + hooks** — no class components
- **Props interface** explicit untuk setiap component
- **TanStack Query** untuk semua server state, **bukan** useState + useEffect
- **React Hook Form + Zod** untuk semua form
- File naming: PascalCase untuk component (`MaturityLevelTree.tsx`), camelCase untuk utility (`formatNumber.ts`)
- Hindari inline style, gunakan Tailwind utility classes atau CSS variables dari design tokens
- **Komponen skeuomorphic** wajib ikut design system di `06_DESIGN_SYSTEM_SKEUOMORPHIC.md`

### Database
- **Migration file** wajib reviewable (descriptive name)
- **Soft delete** dengan `deleted_at TIMESTAMP` — jangan hard delete entity penting
- **Audit columns** (`created_at`, `updated_at`, `created_by`, `updated_by`) di semua tabel utama
- **Index** di kolom yang sering di-filter atau di-join
- **JSONB** untuk struktur dinamis (sesuai schema)

### Git Commit
- Conventional commits format:
  - `feat(scope): deskripsi` untuk fitur baru
  - `fix(scope): deskripsi` untuk bug
  - `chore(scope): deskripsi` untuk maintenance
  - `docs(scope): deskripsi` untuk dokumentasi
  - `refactor(scope): deskripsi` untuk refactor
- Bahasa Indonesia atau English, konsisten per repo
- Pesan singkat & deskriptif

---

## 6. Hal yang HARUS Dilakukan

✅ **Baca SEMUA dokumen blueprint** sebelum mulai
✅ **Tanya kalau ambigu** — Budi lebih suka tanya dulu daripada salah implementasi
✅ **Test minimal manual** setelah tiap fitur
✅ **Pakai Bahasa Indonesia untuk UI strings** (label, placeholder, error message, button)
✅ **Ikuti design system skeuomorphic** — ini differentiator utama aplikasi
✅ **Implementasi audit log** untuk setiap mutating action
✅ **Validasi input dengan Pydantic + Zod** — defense in depth
✅ **Soft delete, bukan hard delete**
✅ **Commit incrementally** dengan pesan jelas
✅ **Update dokumentasi** jika menemukan keputusan teknis baru

## 7. Hal yang TIDAK BOLEH Dilakukan

❌ **Jangan bikin sistem upload evidence** — ini eksplisit ditolak Budi. Hanya text/URL link.
❌ **Jangan hard-code rubrik maturity level** — pakai JSONB structure, dynamic per stream.
❌ **Jangan pakai font generik** (Inter, Roboto, Arial) — pakai font yang ada di design system.
❌ **Jangan bikin styling generic SaaS** (gradient ungu-pink, kartu putih flat) — pakai skeuomorphic.
❌ **Jangan kirim PII ke LLM** tanpa filtering.
❌ **Jangan auto-approve assessment** — selalu butuh asesor manual.
❌ **Jangan duplicate logic NKO calculation** di backend & frontend — hanya backend yang authoritative.
❌ **Jangan skip audit log** untuk shortcut development.
❌ **Jangan implement HCR penuh dulu** — ruangnya disiapkan tapi defer ke Fase 6.
❌ **Jangan commit `.env`** — hanya `.env.example`.

---

## 8. Pertanyaan yang Wajib Anda Tanyakan ke Budi (Sebelum Mulai)

1. **Domain & SSL**: Domain final aplikasi apa? `siskonkin.tenayan.local` (placeholder) atau ada domain real? SSL pakai Let's Encrypt atau internal CA PLN?

2. **OpenRouter API Key**: Apakah sudah ada dan budget untuk AI sudah disetujui?

3. **VPS Spec**: VPS spec berapa? (RAM/CPU/disk) — ini menentukan worker count gunicorn dan limit Redis.

4. **User Pertama**: Siapa yang akan jadi super admin pertama? (Budi sendiri / DIVPKP / Manager IT?)

5. **Data Real vs Dummy**: Untuk testing fase 1-2, apakah pakai data real Konkin 2026 atau dummy? (Recommended: pakai struktur real, isi dummy values dulu, baru migrasi data real saat fase 3 akhir)

6. **Integrasi Eksternal**: Ada rencana integrasi dengan Navitas/SAP/sistem PLN lain di masa depan? Kalau ya, perlu disiapkan webhook endpoint dari awal.

7. **Email/SMTP**: Server SMTP internal PLN tersedia? Atau pakai SendGrid/Mailgun untuk awal?

8. **Backup Storage**: Selain di VPS, ada NAS atau S3-compatible untuk off-site backup?

---

## 9. Saat Bertemu Masalah / Keputusan Ambigu

**Step yang Anda lakukan:**

1. **Baca lagi dokumen blueprint** yang relevan — mungkin sudah ada jawabannya
2. **Cek konteks domain di `01_DOMAIN_MODEL.md`** dan Pedoman Konkin yang di-mention
3. **Kalau masih ambigu**, **stop dan tanya Budi** dengan format:
   ```
   ⚠️ Keputusan diperlukan:
   Konteks: [apa yang sedang dikerjakan]
   Pilihan:
     A. [opsi 1, dengan trade-off]
     B. [opsi 2, dengan trade-off]
   Rekomendasi saya: A, karena [alasan]
   Mohon konfirmasi.
   ```
4. **Jangan gambling**. Lebih baik delay 5 menit untuk konfirmasi daripada bangun fitur yang harus dirombak.

---

## 10. Kemampuan Khusus yang Diharapkan

Selain coding, Anda diharapkan:

1. **Reverse engineer kertas kerja Excel existing**: Beberapa stream punya kertas kerja Excel (`kertas_kerja_Kepatuhan_2026.xlsx` di-attach Budi). Anda harus bisa baca strukturnya pakai openpyxl/pandas, ekstrak rubrik kriteria, dan masukkan ke seed script JSONB structure.

2. **Generate dokumentasi user manual**: Setelah aplikasi berfungsi, generate user manual berbasis Markdown untuk:
   - PIC Bidang (cara self-assessment)
   - Asesor (cara review)
   - Manajer (cara baca dashboard)
   - Admin (cara setup periode + master data)

3. **Compose AI prompts dengan baik**: Saat implementasi fitur AI di Fase 5, Anda harus craft prompts dalam Bahasa Indonesia yang menghasilkan output berkualitas. Test dengan sample data sebelum deploy.

4. **Optimize performance proaktif**: Kalau ada query yang lambat (>500ms), tambah index. Kalau dashboard di-refresh terus-terusan, pakai materialized view. Jangan tunggu Budi yang minta.

---

## 11. Definition of MVP (Stop Point Awal)

Anda dianggap **selesai MVP** kalau:
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

Setelah MVP achieved, **stop dan demo ke Budi** sebelum lanjut ke Fase 4.

---

## 12. Kontak & Komunikasi

- **Budi (technical lead)** — koordinasi langsung via chat ini atau channel yang dia berikan
- **Pedoman Konkin** — sumber kebenaran domain, jangan improvise
- **Saat ragu** — selalu lebih baik tanya daripada asumsi

---

## 13. Tips Khusus VPS Environment

Karena Anda jalan di VPS yang sudah punya Claude Code setup dari Budi:

- **Cek dotfiles & setup VPS Budi terlebih dahulu**: kemungkinan ada Python venv, Node version yang preferred, alias git, dll.
- **Pakai tmux/screen** untuk session yang persistent
- **Log semua aktivitas** ke file `~/siskonkin-claude-code.log` untuk traceability
- **Jangan auto-restart docker** kalau Budi masih mengetes — confirm dulu
- **Resource awareness**: kalau VPS spek terbatas, batasi parallel npm install / pip install

---

## 14. Setelah Selesai Tiap Fase

1. **Commit & push ke GitHub**
2. **Update CHANGELOG.md** dengan ringkasan apa yang berubah
3. **Demo ke Budi**: tunjukkan working feature dengan skenario nyata
4. **Tanya feedback** sebelum lanjut ke fase berikutnya
5. **Update blueprint dokumen** kalau ada keputusan teknis yang berbeda dari rencana awal

---

## 15. Doa Penutup

Anda sedang membangun sistem yang akan dipakai oleh tim PLTU Tenayan untuk monitoring kinerja real — dampaknya nyata. Bekerja dengan **presisi industri**, **keserius an seorang technical lead**, dan **kerendahan hati untuk bertanya saat tidak yakin**. 

Selamat berkarya. 🛠️

— Tim Blueprint SISKONKIN, Mei 2026
