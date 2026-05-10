# SISKONKIN — Sistem Monitoring Kontrak Kinerja Unit Pembangkit

> **Sistem informasi monitoring & self-assessment Kontrak Kinerja PLTU Tenayan**
> PT PLN Nusantara Power UP Tenayan — 2026

---

## Tentang Proyek

SISKONKIN adalah aplikasi internal untuk memantau, melakukan self-assessment, melakukan asesmen oleh asesor, dan mengelola tindak lanjut rekomendasi atas Kontrak Kinerja Unit (Konkin) PLTU Tenayan setiap triwulan. Sistem ini menggantikan workflow berbasis Excel (kertas kerja yang berbeda-beda per stream) dengan platform terstruktur yang konsisten, dapat ditelusuri, dan kolaboratif.

Sistem mengacu pada **Peraturan Direksi PT PLN Nusantara Power Nomor 0019.P/DIR/2025** tanggal 17 Juli 2025 tentang Pedoman Penilaian Kontrak Kinerja Unit, dan dirancang untuk mengakomodasi struktur Konkin 2026.

## Filosofi Desain

1. **Bukan sistem manajemen evidence.** Sistem ini adalah kertas kerja digital + workflow asesmen, bukan document repository. Evidence tetap dikelola oleh PIC bidang masing-masing di sistem internal mereka.
2. **Setiap stream punya rubrik unik.** Sistem dirancang dengan **dynamic schema per stream** — bukan one-size-fits-all form.
3. **Self-assessment → Asesor → Feedback → Tindak Lanjut.** Alur ini diterapkan konsisten di semua indikator, baik KPI kuantitatif maupun Maturity Level.
4. **Triwulan sebagai irama monitoring, semester sebagai irama formal.** Konkin formal dinilai per semester, tapi monitoring & koreksi arah dilakukan per triwulan.
5. **AI sebagai asisten, bukan pengganti asesor.** LLM membantu menulis rekomendasi, mendeteksi anomali, dan mempercepat self-assessment — keputusan tetap di manusia.

## Struktur Dokumen Blueprint

Dokumen ini disusun dalam beberapa file. Baca berurutan untuk pemahaman utuh:

| # | Dokumen | Isi |
|---|---|---|
| 1 | [`01_DOMAIN_MODEL.md`](docs/01_DOMAIN_MODEL.md) | Pemahaman bisnis: hierarki Konkin, jenis indikator, formula, polaritas, pemilik proses |
| 2 | [`02_FUNCTIONAL_SPEC.md`](docs/02_FUNCTIONAL_SPEC.md) | Modul fungsional, user roles, alur kerja, fitur per modul |
| 3 | [`03_DATA_MODEL.md`](docs/03_DATA_MODEL.md) | Database schema (PostgreSQL), relasi entitas, sample data |
| 4 | [`04_API_SPEC.md`](docs/04_API_SPEC.md) | Endpoint REST API (FastAPI), request/response schema |
| 5 | [`05_FRONTEND_ARCHITECTURE.md`](docs/05_FRONTEND_ARCHITECTURE.md) | Struktur React, routing, state management, komponen kunci |
| 6 | [`06_DESIGN_SYSTEM_SKEUOMORPHIC.md`](docs/06_DESIGN_SYSTEM_SKEUOMORPHIC.md) | Design tokens, skeuomorphic visual language, komponen UI |
| 7 | [`07_AI_INTEGRATION.md`](docs/07_AI_INTEGRATION.md) | Integrasi LLM (OpenRouter), use case AI, prompt patterns |
| 8 | [`08_DEPLOYMENT.md`](docs/08_DEPLOYMENT.md) | Docker Compose, environment variables, Nginx, backup |
| 9 | [`09_DEVELOPMENT_ROADMAP.md`](docs/09_DEVELOPMENT_ROADMAP.md) | Fase pengembangan MVP → Full, milestone, prioritas |
| 10 | [`10_CLAUDE_CODE_INSTRUCTIONS.md`](docs/10_CLAUDE_CODE_INSTRUCTIONS.md) | Instruksi spesifik untuk Claude Code di VPS |

## Tech Stack

```
Backend:    FastAPI (Python 3.11+) + SQLAlchemy 2.x + Alembic
Database:   PostgreSQL 16
Frontend:   React 18 + Vite + TypeScript + TanStack Query + Zustand
Styling:    Tailwind CSS + custom skeuomorphic design tokens
LLM:        OpenRouter (Gemini 2.5 Flash for routine, Claude Sonnet for complex)
Container:  Docker Compose + Nginx reverse proxy
Auth:       JWT + httpOnly cookies, role-based access
Port:       3399 (production), 5173 (dev frontend), 8000 (dev backend)
```

## Identitas Visual

Aplikasi mengadopsi gaya **Skeuomorphic / Neumorphic** dengan warna dasar PLN (biru gelap navy + kuning aksen) yang didekati sebagai material fisik: tombol seperti hardware, dial pengukur seperti instrumen kontrol pembangkit, kartu seperti panel logam. Ini bukan kebetulan — pembangkit listrik adalah dunia instrumen fisik, dan UI harus terasa seperti control room digital.

Detail lengkap di [`06_DESIGN_SYSTEM_SKEUOMORPHIC.md`](docs/06_DESIGN_SYSTEM_SKEUOMORPHIC.md).

## Quick Start (untuk developer / Claude Code)

```bash
# 1. Clone repo
git clone <repo_url> siskonkin
cd siskonkin

# 2. Baca dokumen secara berurutan (1 → 10)
# 3. Mulai dari MVP scope di docs/09_DEVELOPMENT_ROADMAP.md
# 4. Setup environment
cp .env.example .env
docker compose up -d

# 5. Migrasi database
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed_konkin_2026
```

## Catatan Penting

- **Tidak ada upload file evidence.** Field `link_eviden` cukup berupa text/URL ke sistem eksternal (Google Drive, SharePoint, atau path internal unit).
- **Setiap stream maturity level punya rubrik berbeda.** Schema database menggunakan pola JSONB untuk fleksibilitas, bukan tabel statis.
- **HCR akan ditambahkan kemudian.** Schema dan modul sudah disiapkan ruangnya, implementasi penuh setelah MVP stream lain stabil.

## Lisensi & Kerahasiaan

Proyek internal CV Panda Global Teknologi untuk PT PLN Nusantara Power UP Tenayan. Tidak untuk distribusi publik.
