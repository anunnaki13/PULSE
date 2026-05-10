# Tentang Nama — PULSE

> "Denyut Kinerja Pembangkit, Real-Time."

Halaman ini adalah **catatan kanonik** asal-usul nama, akronim, dan tagline aplikasi PULSE. Mengacu langsung pada keputusan terkunci di `UPDATE-001-pulse-rebrand-ai-features.md` (status APPROVED, precedence=0) dan tercantum di `.planning/PROJECT.md` sebagai **DEC-001**, **DEC-002**, dan **DEC-003**.

> **Catatan untuk reviewer:** Dokumen ini sengaja **tidak menuliskan literal token nama lama** di body teks. Daftar verbatim find-and-replace identifier-rename ada di file ADR `UPDATE-001-pulse-rebrand-ai-features.md` (di-ingest sebagai sumber sejarah) dan di `.planning/PROJECT.md` blok DEC-002. Ini supaya audit `grep -ri` brand-bersih bisa memakai kebijakan ketat tanpa kompromi.

---

## 1. Akronim

**PULSE** = **P**erformance & **U**nit **L**ive **S**coring **E**ngine.

Setiap huruf membawa makna:

| Huruf | Kata | Makna dalam konteks Konkin |
|------:|------|-----------------------------|
| **P** | Performance | Kinerja yang dipantau — NKO, KPI Kuantitatif, Maturity Level. |
| **U** | Unit | Unit pembangkit — fokus operasional di PLTU Tenayan. |
| **L** | Live | Real-time — angka selalu segar, snapshot per perubahan. |
| **S** | Scoring | Penilaian formal — formula bobot, polaritas, agregasi multi-tier. |
| **E** | Engine | Mesin — bukan dashboard pasif, tapi sistem yang menghitung dan mengarahkan tindak lanjut. |

## 2. Tagline

| Bentuk | Teks |
|--------|------|
| **Bahasa Indonesia (utama)** | "Denyut Kinerja Pembangkit, Real-Time." |
| **Bahasa Inggris (alternatif)** | "The Heartbeat of Power Performance." |
| **Formal (penuh)** | "Sistem Monitoring Kinerja Unit Pembangkit Real-Time PT PLN Nusantara Power." |

Tagline utama dipilih karena ia menyatukan **dua kata kunci**: *denyut* (heartbeat — mengikat ke DEC-003 Pulse Heartbeat animation) dan *real-time* (mengikat ke DEC-001 acronym slot **L**ive).

## 3. Asal — Rebrand DEC-001

Aplikasi semula bernama berdasarkan singkatan Indonesia *"Sistem Informasi Kontrak Kinerja"*. Nama itu deskriptif tetapi:

- Akronim Indonesia panjang dan susah di-search-engine-kan.
- Tidak punya identitas visual/motion bawaan.
- Tidak menyiratkan *real-time* — kesan yang justru jadi diferensiator utama versus workflow Excel.

ADR `UPDATE-001-pulse-rebrand-ai-features.md` (17 Juli 2025) mengunci rebrand ke **PULSE** sebagai **DEC-001**, dan setiap kemunculan nama lama (semua case) di dokumen, kode, konfigurasi, dan infrastruktur **harus** diganti. Daftar verbatim ada di file ADR tersebut dan disalin sebagai DEC-002 di `.planning/PROJECT.md`.

## 4. Audit Identifier — Find & Replace (DEC-002)

DEC-002 mengunci 12 baris penggantian *case-sensitive*. Daftar verbatim dapat dibaca di:

- `.planning/PROJECT.md` — blok `<decisions status="LOCKED">` → DEC-002.
- `UPDATE-001-pulse-rebrand-ai-features.md` — sumber otoritatif rebrand.

Cakupan tinggi-level (12 baris):

| Kategori | Skema penggantian |
|---|---|
| Network Docker | `<old>-net` → `pulse-net` |
| Container DB | `<old>-db` → `pulse-db` |
| Container backend | `<old>-backend` → `pulse-backend` |
| Container frontend | `<old>-frontend` → `pulse-frontend` |
| Container Redis | `<old>-redis` → `pulse-redis` |
| Container Nginx | `<old>-nginx` → `pulse-nginx` |
| Domain | `<old>.tenayan.local` → `pulse.tenayan.local` |
| DB name | `POSTGRES_DB=<old>` → `POSTGRES_DB=pulse` |
| DB user | `POSTGRES_USER=<old>` → `POSTGRES_USER=pulse` |
| Backup dir | `BACKUP_DIR=/var/backups/<old>` → `BACKUP_DIR=/var/backups/pulse` |
| Bundle archive | `<old>-blueprint.tar.gz` → `pulse-blueprint.tar.gz` |
| Repo identifier | `<old>_blueprint` → `pulse_blueprint` |

> **Kenapa case-sensitive?** Container/host/network namespace di Docker dan DNS label adalah lower-case-by-convention; sementara dokumentasi naratif kadang masih pakai capitalised form; sementara konstanta di kode kadang ALL-CAPS. Audit harus menyentuh ketiga case.

**Validasi:** `grep -ri --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.planning/intel/classifications "<old-token>" .` di repo PULSE harus mengembalikan nol hit di luar `.planning/intel/classifications/` (yang merupakan arsip ingest pra-rebrand, sengaja tidak di-edit).

## 5. Heartbeat sebagai Tanda Tangan Visual (DEC-003)

Nama PULSE bukan kebetulan dipilih bersamaan dengan **Pulse Heartbeat signature animation**:

- LED indicator (komponen `SkLed` di design system skeuomorphic) **berdenyut 60–80 BPM** pada kondisi *healthy* — kira-kira sama dengan denyut jantung manusia istirahat.
- Saat ada *alert* (angka NKO turun, deadline assessment terlewat), denyut bertambah cepat — meta-fora langsung dari *vital sign monitor* di control room pembangkit.
- *Loading state* memakai **horizontal pulse wave** alih-alih spinner generik — supaya gerakan visual selalu konsisten dengan tema.
- *Snapshot update* di NKO Gauge memantulkan *ripple animation* (300 ms ease-out).

Ini menjadikan nama **PULSE** literal: aplikasi memang berdenyut secara visual, mengikuti irama Konkin (triwulan = irama monitoring, semester = irama formal).

## 6. Kapan Nama PULSE Dipakai

| Konteks | Nama yang dipakai |
|---|---|
| Repo, kode sumber, dokumentasi developer | **PULSE** (selalu) |
| Branding aplikasi (login screen, header, tagline) | **PULSE** (selalu) |
| Container, network, DB identifier, env var | `pulse-*` (DEC-002) |
| Domain | `pulse.tenayan.local` |
| Arsip *intel* pra-rebrand di `.planning/intel/classifications/` | Tidak diedit (sumber sejarah) |
| Komunikasi formal ke stakeholder PLN (jika muncul referensi `Konkin`) | `Konkin` tetap istilah domain — bukan nama aplikasi |

## 7. Referensi Silang

- `.planning/PROJECT.md` — DEC-001, DEC-002, DEC-003.
- `UPDATE-001-pulse-rebrand-ai-features.md` — sumber otoritatif rebrand + daftar verbatim find-and-replace.
- `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` §"Tema Pulse — Sinyal Kehidupan Pembangkit" — implementasi heartbeat di design system.
- `README.md` — landing page yang merujuk balik ke dokumen ini.
