# PULSE — Performance & Unit Live Scoring Engine

> "Denyut Kinerja Pembangkit, Real-Time."

**PULSE** adalah kertas kerja digital + workflow asesmen Kontrak Kinerja Unit (Konkin) untuk PLTU Tenayan, PT PLN Nusantara Power. Sistem ini menggantikan workflow Excel (kertas kerja per stream) dengan platform terstruktur, auditable, dan kolaboratif yang menghitung **NKO (Nilai Kinerja Organisasi) secara real-time** dan mengelola self-assessment, asesor review, rekomendasi, serta tindak lanjut compliance.

Referensi: **Peraturan Direksi PT PLN Nusantara Power Nomor 0019.P/DIR/2025** (17 Juli 2025) tentang Pedoman Penilaian Kontrak Kinerja Unit; dirancang untuk Konkin 2026.

---

## Tentang Nama

Nama, akronim, tagline, dan riwayat rebrand (DEC-001) ke PULSE didokumentasikan lengkap di [`docs/ABOUT-THE-NAME.md`](docs/ABOUT-THE-NAME.md). Singkatnya: **P**erformance & **U**nit **L**ive **S**coring **E**ngine, dengan **Pulse Heartbeat** sebagai tanda tangan visual (LED berdenyut 60–80 BPM saat sehat).

Dokumentasi operator dan handoff:

- Panduan fungsi menu aplikasi: [`docs/MENU-GUIDE.md`](docs/MENU-GUIDE.md)
- Handoff final local build: [`docs/FINAL-LOCAL-HANDOFF.md`](docs/FINAL-LOCAL-HANDOFF.md)
- Backlog penyederhanaan UX: [`docs/UX-SIMPLIFICATION-BACKLOG.md`](docs/UX-SIMPLIFICATION-BACKLOG.md)

---

## Quick Start

Prasyarat: Docker Desktop (atau Docker Engine) terpasang dan engine berjalan. Lihat [Verifikasi Docker](#verifikasi-docker) di bawah.

```bash
# 1. Salin template environment dan isi secret-nya (JWT keys, POSTGRES_PASSWORD, dll.)
cp .env.example .env

# 2. Naikkan seluruh stack (db, redis, backend, frontend, nginx, backup sidecar)
make up
# Windows tanpa make:
./scripts/dev.ps1 up

# 3. Jalankan migrasi + seed master data
make migrate
make seed

# 4. Buka aplikasi
#    http://localhost:3399
```

Login pertama menggunakan kredensial `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD` dari `.env`. Akun ini dibuat seed dengan role **`admin_unit`** (lihat [Roles](#roles)) dan password **wajib** dirotasi setelah login pertama.

---

## Stack

Versi locked di `.planning/phases/01-foundation-master-data-auth/01-RESEARCH.md` Standard Stack.

- **Frontend:** React 18 + Vite 7 + TypeScript 5.9; TanStack Query v5; Zustand; React Hook Form + Zod; React Router v6; Tailwind v4 + skeuomorphic tokens; Recharts/ECharts; Motion (framer-motion); Sonner.
- **Backend:** FastAPI 0.136 di Python 3.11-slim; gunicorn 26 + UvicornWorker (4 worker); Pydantic v2; SQLAlchemy 2.0 async + asyncpg; Alembic 1.18; python-jose 3.5 (JWT); passlib + bcrypt 5.
- **Database:** PostgreSQL 16 via `pgvector/pgvector:pg16`; ekstensi `uuid-ossp`, `pgcrypto`, `vector`. UUID PK + JSONB dynamic schema (GIN index).
- **Cache:** Redis 7-alpine (256 MB, `allkeys-lru`).
- **Reverse Proxy:** Nginx 1.30-alpine; publish hanya host port 3399.
- **LLM (Phase 5+):** OpenRouter — `google/gemini-2.5-flash` (rutin) + `anthropic/claude-sonnet-4` (kompleks).
- **Deploy:** Docker Compose, single VPS, domain `pulse.tenayan.local`.

---

## Developer Verbs

Dua entrypoint, perilaku identik. `make` untuk Linux/macOS/Git Bash; `./scripts/dev.ps1` untuk PowerShell murni; `./scripts/dev.sh` sebagai bash fallback.

| Verb     | Make            | PowerShell                          | Bash                                   | Deskripsi                                         |
|----------|-----------------|-------------------------------------|----------------------------------------|---------------------------------------------------|
| up       | `make up`       | `./scripts/dev.ps1 up`              | `./scripts/dev.sh up`                  | `docker compose up -d --wait` (semua service)     |
| down     | `make down`     | `./scripts/dev.ps1 down`            | `./scripts/dev.sh down`                | Stop + hapus container                            |
| build    | `make build`    | `./scripts/dev.ps1 build`           | `./scripts/dev.sh build`               | Build semua image                                 |
| seed     | `make seed`     | `./scripts/dev.ps1 seed`            | `./scripts/dev.sh seed`                | `python -m app.seed` (bidang + Konkin 2026)       |
| migrate  | `make migrate`  | `./scripts/dev.ps1 migrate`         | `./scripts/dev.sh migrate`             | `alembic upgrade head`                            |
| test     | `make test`     | `./scripts/dev.ps1 test`            | `./scripts/dev.sh test`                | pytest backend + vitest frontend                  |
| backup   | `make backup`   | `./scripts/dev.ps1 backup`          | `./scripts/dev.sh backup`              | Trigger `backup.sh` di sidecar `pulse-backup`     |
| restore  | `make restore FILE=…` | `./scripts/dev.ps1 restore -File …` | `FILE=… ./scripts/dev.sh restore`   | Restore dari file backup `.sql.gz`                |
| logs     | `make logs`     | `./scripts/dev.ps1 logs`            | `./scripts/dev.sh logs`                | `docker compose logs -f --tail=200`               |
| lint     | `make lint`     | `./scripts/dev.ps1 lint`            | `./scripts/dev.sh lint`                | ruff (backend) + eslint (frontend)                |
| prod-env | `make prod-env` | `./scripts/dev.ps1 prod-env`        | `./scripts/dev.sh prod-env`            | Generate `.env.production.generated`              |
| prod-check | `make prod-check` | `./scripts/dev.ps1 prod-check`   | `./scripts/dev.sh prod-check`          | Validasi gate go-live production                  |
| prod-smoke | `BASE_URL=… EMAIL=… PASSWORD=… make prod-smoke` | `./scripts/dev.ps1 prod-smoke -BaseUrl … -Email … -Password …` | `BASE_URL=… EMAIL=… PASSWORD=… ./scripts/dev.sh prod-smoke` | Smoke test deploy production/local                |

---

## Verifikasi Docker

Sebelum `make up` bisa berjalan, pastikan tiga perintah berikut sukses (terutama di Windows host):

```powershell
docker --version
docker compose version
docker info
```

Output yang diharapkan:
- `docker --version` → `Docker version 24.x` atau lebih baru.
- `docker compose version` → `Docker Compose version v2.x` atau lebih baru.
- `docker info` → engine berjalan tanpa error "Cannot connect to the Docker daemon".

Jika gagal: pasang Docker Desktop ([docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)), tunggu indikator engine hijau, buka ulang terminal, lalu jalankan ulang.

---

## Roles

PULSE menyemai enam role (penamaan verbatim sesuai `REQ-user-roles` + `REQ-route-guards`):

| Role            | Cakupan |
|-----------------|---------|
| `super_admin`   | Akses penuh ke seluruh modul + master data + konfigurasi sistem. |
| `admin_unit`    | Admin di tingkat unit (PLTU Tenayan); pengelola Konkin template, master bidang, dan akun. |
| `pic_bidang`    | PIC bidang; mengisi self-assessment indikator yang ter-assign ke `bidang_id`-nya. Akses `/master/*` ditolak (redirect ke `/dashboard`). |
| `asesor`        | Reviewer; approve/override/return submission self-assessment dan menulis rekomendasi. |
| `manajer_unit`  | Manajer Unit; melihat dashboard NKO + drill-down + trend. |
| `viewer`        | Read-only; tidak bisa memutasikan apa pun. |

ROADMAP.md success criterion #1 ("Admin dapat login…") merujuk ke pengguna dengan role **`admin_unit`**.

---

## Phase 1 Acceptance Criteria

Disalin verbatim dari `.planning/ROADMAP.md` §"Phase 1: Foundation (Master Data + Auth)". Phase ini adalah *runnable shell* — login + navigasi master data + Docker Compose stack hijau.

1. Admin dapat login via `pulse.tenayan.local:3399` dengan kredensial JWT, dan navigasi ke `/master/konkin-template/2026` menampilkan 6 perspektif + indikator yang ter-seed.
2. PIC dapat login dan hanya melihat indikator yang di-assign ke `bidang_id`-nya (read-only view); akses ke `/master/*` ditolak dengan redirect ke `/dashboard`.
3. Halaman login menampilkan branding **PULSE** dengan tagline "Denyut Kinerja Pembangkit, Real-Time." dan animasi Pulse Heartbeat (LED 60–80 BPM) — `grep` repo terhadap nama legacy pra-rebrand mengembalikan zero hits di luar `.planning/intel/classifications/` (lihat DEC-002 di [`docs/ABOUT-THE-NAME.md`](docs/ABOUT-THE-NAME.md) untuk daftar identifier yang diaudit).
4. `make seed` populates bidang master + Konkin 2026 PLTU Tenayan struktur (perspektif + indikator + bobot, plus seed Outage + SMAP + EAF + EFOR rubrik) tanpa error; `GET /api/v1/health` returns 200.
5. Tidak ada endpoint multipart untuk evidence file; `link_eviden` field hanya menerima URL; admin Excel-import endpoint adalah satu-satunya multipart endpoint.
6. Daily backup cron at 02:00 sudah scheduled di VPS, restore script teruji manual sekali.

---

## Struktur Repo (target Phase 1)

```
PULSE/
├── docker-compose.yml             # 6 service (db, redis, backend, frontend, nginx, backup)
├── docker-compose.override.yml    # dev-only (volume mount, hot-reload)
├── .env.example                   # template env, nol secret asli
├── .env                           # gitignored
├── Makefile                       # entrypoint DX (Git Bash / Linux / macOS)
├── scripts/
│   ├── dev.ps1                    # PowerShell fallback (Windows tanpa make)
│   └── dev.sh                     # bash fallback
├── backend/                       # FastAPI app + Alembic + tests
├── frontend/                      # React 18 + Vite + TypeScript + tests
├── nginx/                         # konfigurasi reverse proxy
├── infra/backup/                  # backup sidecar (cron + pg_dump + rsync)
├── docs/                          # ABOUT-THE-NAME.md + dokumentasi naratif
└── .planning/                     # GSD planning artifacts (PHASE/PLAN/SUMMARY)
```

Tambahan Phase 6 production hardening:
`infra/production/` berisi template host Nginx TLS, script firewall UFW, dan contoh konfigurasi external monitor untuk go-live.

---
