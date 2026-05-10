# UPDATE-001 — Rebranding ke PULSE & Penambahan Fitur AI

> **Untuk:** Claude Code di VPS yang sedang mengerjakan blueprint SISKONKIN
> **Dari:** Budi (technical lead, CV Panda Global Teknologi)
> **Tanggal:** Mei 2026
> **Status:** ✅ APPROVED — segera diterapkan
> **Prioritas:** 🔴 High

---

## Cara Pakai Dokumen Ini

Dokumen ini adalah **patch/update** untuk blueprint yang sudah ada di repo (`docs/01-10`). Berisi 3 jenis update:

1. **Rebranding** — ganti nama aplikasi dari `SISKONKIN` jadi `PULSE`
2. **Penambahan fitur AI** — 2 fitur baru yang ditambahkan ke MVP
3. **Klarifikasi keputusan** — beberapa pertanyaan yang sudah dijawab

**Yang harus Anda lakukan, Claude Code:**
1. Baca dokumen ini secara lengkap dulu
2. Apply perubahan sesuai checklist di setiap section
3. Update CHANGELOG.md dengan entry baru
4. Commit dengan pesan: `feat: apply UPDATE-001 — rebranding PULSE + AI features expansion`
5. Setelah selesai, kasih tahu Budi untuk verifikasi

---

# BAGIAN 1 — REBRANDING: SISKONKIN → PULSE

## 1.1 Keputusan Final

**Nama aplikasi resmi:** **PULSE**
**Akronim:** **P**erformance & **U**nit **L**ive **S**coring **E**ngine
**Tagline utama:** *"Denyut Kinerja Pembangkit, Real-Time."*
**Tagline English (alternatif):** *"The Heartbeat of Power Performance."*
**Tagline formal:** *"Sistem Monitoring Kinerja Unit Pembangkit Real-Time PT PLN Nusantara Power."*

## 1.2 Filosofi Branding

Seperti denyut nadi yang menandakan kesehatan organ, NKO unit pembangkit adalah **pulse** organisasi. PULSE memantau denyut itu setiap saat — real-time, granular, transparan. Nama ini juga selaras dengan tema **control room digital** yang sudah ditetapkan di design system: instrumen monitoring (heart rate, oscilloscope, frekuensi).

## 1.3 Find & Replace Wajib

Lakukan find & replace di **seluruh repository**:

| Cari (case-sensitive) | Ganti dengan |
|---|---|
| `SISKONKIN` | `PULSE` |
| `Siskonkin` | `PULSE` |
| `siskonkin` | `pulse` |
| `siskonkin_blueprint` | `pulse_blueprint` |
| `siskonkin-net` | `pulse-net` |
| `siskonkin-db` | `pulse-db` |
| `siskonkin-backend` | `pulse-backend` |
| `siskonkin-frontend` | `pulse-frontend` |
| `siskonkin-redis` | `pulse-redis` |
| `siskonkin-nginx` | `pulse-nginx` |
| `siskonkin.tenayan.local` | `pulse.tenayan.local` |
| `POSTGRES_DB=siskonkin` | `POSTGRES_DB=pulse` |
| `POSTGRES_USER=siskonkin` | `POSTGRES_USER=pulse` |
| `BACKUP_DIR=/var/backups/siskonkin` | `BACKUP_DIR=/var/backups/pulse` |
| `Sistem Monitoring Kontrak Kinerja` | `PULSE — Performance & Unit Live Scoring Engine` |
| `siskonkin-blueprint.tar.gz` | `pulse-blueprint.tar.gz` |

**File yang perlu di-scan:**
- [ ] `README.md`
- [ ] `CHANGELOG.md`
- [ ] `docs/01_DOMAIN_MODEL.md`
- [ ] `docs/02_FUNCTIONAL_SPEC.md`
- [ ] `docs/03_DATA_MODEL.md`
- [ ] `docs/04_API_SPEC.md`
- [ ] `docs/05_FRONTEND_ARCHITECTURE.md`
- [ ] `docs/06_DESIGN_SYSTEM_SKEUOMORPHIC.md`
- [ ] `docs/07_AI_INTEGRATION.md`
- [ ] `docs/08_DEPLOYMENT.md`
- [ ] `docs/09_DEVELOPMENT_ROADMAP.md`
- [ ] `docs/10_CLAUDE_CODE_INSTRUCTIONS.md`
- [ ] `.env.example` (kalau sudah dibuat)
- [ ] `docker-compose.yml` (kalau sudah dibuat)
- [ ] `Makefile` (kalau sudah dibuat)
- [ ] Semua kode source (Python, TypeScript) yang sudah dibuat

## 1.4 Section Tambahan di README.md

Tambahkan section baru **setelah judul dan sebelum "Tentang Proyek"**:

```markdown
## About the Name

**PULSE** = Performance & Unit Live Scoring Engine

Seperti denyut nadi yang menandakan kesehatan organ, NKO unit pembangkit
adalah pulse organisasi. PULSE memantau denyut itu setiap saat —
real-time, granular, transparan.

> "Denyut Kinerja Pembangkit, Real-Time."
```

## 1.5 Update di Design System

Di `docs/06_DESIGN_SYSTEM_SKEUOMORPHIC.md`, **tambahkan paragraf di section "Filosofi Desain"**:

```markdown
### Tema Pulse — Sinyal Kehidupan Pembangkit

Nama aplikasi PULSE memperkuat metaphor visual: setiap elemen UI mencerminkan
denyut data kinerja yang hidup. LED indikator berdenyut dengan ritme yang
menggambarkan health state. Saat NKO di-update real-time, ada **pulse
animation** subtle di pojok screen (seperti EKG blip) yang mengonfirmasi
sistem masih "hidup" dan data masih mengalir.

**Signature animation: Pulse Heartbeat**
- LED status: pulse rate normal saat sistem sehat (60-80 BPM equivalent)
- Pulse rate naik saat ada anomali atau alert
- LCD screen kadang menampilkan waveform mini di header
- Loading state: pulse wave horizontal (bukan spinner generik)
```

Tambahkan juga **di section "Animation Patterns"** subsection baru:

```markdown
### 6.6 Pulse Signature Animation

Sebagai signature visual PULSE, tambahkan animasi pulse halus di:

**LED Heartbeat (default state):**
```css
@keyframes pulse-heartbeat {
  0%, 100% { transform: scale(1); opacity: 1; }
  50%      { transform: scale(1.08); opacity: 0.85; }
}

.sk-led[data-state="on"] {
  animation: pulse-heartbeat 1.2s ease-in-out infinite;
}
```

**NKO Update Pulse:**
Saat NKO snapshot di-update, tampilkan ripple animation dari pusat NKO Gauge
keluar ke seluruh dashboard (300ms ease-out, opacity fade).

**Loading Wave:**
Untuk loading indicator, gunakan SVG pulse wave horizontal mengganti spinner.
```

## 1.6 UI Copy Adjustment (Opsional, untuk memperkuat tema)

Beberapa label UI yang sebaiknya disesuaikan dengan tema PULSE:

| Konteks Lama | Diubah menjadi |
|---|---|
| "Dashboard NKO" | "Pulse Monitor" atau "Live NKO Dashboard" |
| "Update terakhir: X menit lalu" | "Pulse terakhir: X menit lalu" |
| "Sistem berjalan normal" | "Pulse stabil" |
| "Refresh data" | "Sync pulse" |

**Aturan:** Jangan over-do. Yang krusial tetap jelas kata "monitoring" dan "scoring". Pakai metaphor pulse hanya di tempat yang menguatkan, bukan menggantikan informasi penting.

---

# BAGIAN 2 — PENAMBAHAN FITUR AI

Blueprint inti `docs/07_AI_INTEGRATION.md` punya **6 fitur AI**. Sekarang kita tambahkan **2 fitur baru** yang masuk ke MVP.

## 2.1 Fitur AI Baru #1: AI Inline Help (Konteks Indikator)

### Konsep
Side panel atau hover tooltip yang otomatis menampilkan info kontekstual saat PIC/Asesor sedang berinteraksi dengan indikator tertentu. Bukan chat — lebih ke **assistive overlay**.

### Use Case
- PIC baru tidak tahu detail indikator → klik ikon ❓ di samping nama indikator → panel slide dari kanan dengan info
- Asesor butuh referensi cepat best practice nilai → hover → quick stat
- Saat isi maturity level → AI suggest level mana yang paling cocok berdasarkan deskripsi user

### Konten Panel
- **"Apa itu [Nama Indikator]?"** — penjelasan singkat dari Pedoman (auto-generated dari RAG)
- **Formula** — formula resmi dengan visualisasi
- **Best practice industri** — benchmark dari unit PLN sejenis (kalau ada data)
- **Indikator terkait** — mention indikator yang berkorelasi (mis. EAF ↔ EFOR ↔ Outage Mgmt)
- **Kesalahan umum** — common pitfalls saat self-assessment

### Implementasi
- **Pre-compute saat indikator dibuat** (cache hasil AI di DB) — hemat biaya
- **Re-generate** kalau struktur indikator berubah
- **Model:** Gemini 2.5 Flash (hasil di-cache, jadi 1× cost per indikator)

### Database Schema Tambahan

Tambahkan tabel baru di `docs/03_DATA_MODEL.md`:

```sql
CREATE TABLE ai_inline_help (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indikator_id UUID NOT NULL REFERENCES indikator(id) ON DELETE CASCADE,
    
    apa_itu TEXT,                            -- "Apa itu [indikator]?"
    formula_explanation TEXT,                -- penjelasan formula
    best_practice TEXT,                      -- benchmark industri
    common_pitfalls TEXT,                    -- kesalahan umum
    related_indikator JSONB,                 -- [{"id": "...", "code": "EFOR"}]
    
    generated_by_model VARCHAR(100),
    generated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,     -- regenerate after expiry
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(indikator_id)
);

CREATE INDEX idx_ai_inline_help_indikator ON ai_inline_help(indikator_id);
```

### API Endpoint Tambahan

Tambahkan di `docs/04_API_SPEC.md`:

```
GET    /api/v1/ai/inline-help/{indikator_id}    — fetch cached help
POST   /api/v1/ai/inline-help/{indikator_id}/regenerate    — admin: trigger regen
```

### UX Pattern

```
┌──────────────────────────────────────────────┐
│  EAF (Equivalent Availability Factor) [❓]   │  ← klik tanya
│  ↓ Form input...                             │
└──────────────────────────────────────────────┘
                                          
                    ┌────────────────────────────────┐
                    │ 💡 Tentang EAF                 │
                    │ ─────────────────────────────  │
                    │ Apa itu EAF?                   │
                    │ EAF mengukur ketersediaan...   │
                    │                                │
                    │ Formula                        │
                    │ Σ(AH-EPDH-EMDH-EFDH)×DMN×100  │
                    │ ───────────────────────────    │
                    │ Σ(PH × DMN)                    │
                    │                                │
                    │ Best Practice Industri         │
                    │ PLTU sejenis: 85-92%           │
                    │ Excellent: ≥92%                │
                    │                                │
                    │ Indikator Terkait              │
                    │ • EFOR (Forced Outage)         │
                    │ • Outage Management            │
                    │                                │
                    │ Kesalahan Umum                 │
                    │ • Salah hitung EFDH (lupa...   │
                    │ [Generate dengan Gemini Flash] │
                    └────────────────────────────────┘
```

### Estimasi Effort
| Item | Effort |
|------|--------|
| Backend: model + cache table + service | 1-2 hari |
| Pre-compute job saat indikator dibuat | 0.5 hari |
| Frontend: side panel component | 2 hari |
| Total | **3-5 hari** |

### Estimasi Biaya AI
- One-time per indikator: ~62 indikator × 2000 tokens × Gemini Flash = ~$0.10 (Rp 1.500)
- Re-generate periodik: negligible

---

## 2.2 Fitur AI Baru #2: Comparative Analysis (Cross-Periode)

### Konsep
Tombol **"Bandingkan dengan TW Lalu"** di setiap form indikator. AI hasilkan **analisis kontekstual** apa yang berubah dan kenapa.

### Use Case
- PIC isi self-assessment EAF → klik "Bandingkan TW1 vs TW2"
- AI dapat: data komponen 2 periode + tren historis 4 periode
- AI hasilkan narasi pendek (3-5 kalimat) yang menjelaskan perubahan

### Output Contoh

```
┌─────────────────────────────────────────────────────┐
│ 📊 Analisis Komparatif: EAF                         │
│ TW1 2026 → TW2 2026                                 │
├─────────────────────────────────────────────────────┤
│ EAF di TW2 2026 (84.7%) lebih tinggi 2.6 poin      │
│ dibanding TW1 (82.1%). Faktor utama berdasarkan    │
│ data komponen: EFDH turun signifikan dari 24 jam   │
│ ke 12 jam, mengindikasikan penurunan forced outage.│
│                                                     │
│ EAF stabil di atas target 3 triwulan berturut-turut│
│ menunjukkan tren positif yang konsisten.           │
│ Kontributor lain: AH naik 18 jam akibat extended   │
│ operating window di Mei.                           │
│                                                     │
│ 📈 Tren 4 Periode Terakhir:                         │
│ TW3 2025: 79.8% → TW4 2025: 80.5% →                │
│ TW1 2026: 82.1% → TW2 2026: 84.7%                  │
│                                                     │
│ [Tutup]                                             │
└─────────────────────────────────────────────────────┘
```

### Implementasi

**Endpoint baru:**
```
POST /api/v1/ai/comparative-analysis
Body: {
  "indikator_id": "uuid",
  "period_a": "uuid",       // periode pertama
  "period_b": "uuid"        // periode kedua (biasanya yang aktif)
}
Response: {
  "narrative": "...",
  "data_points": {...},
  "trend_4_periods": [...],
  "model_used": "google/gemini-2.5-flash",
  "tokens_used": 1247
}
```

**Service:**
- Backend ambil data 2 periode lengkap (komponen, realisasi, pencapaian)
- Ambil 4 periode historis untuk konteks tren
- Kirim ke LLM dengan prompt khusus
- Cache hasil 1 jam (kalau request sama, tidak panggil LLM lagi)

**Prompt Template:**
```
Anda analis data kinerja PT PLN Nusantara Power. Tugas: bandingkan kinerja
indikator antar dua periode dan jelaskan perubahan secara faktual.

Indikator: {indikator.nama}
Polaritas: {polaritas}

Periode A ({period_a.label}):
  Realisasi: {period_a.realisasi}
  Komponen: {period_a.komponen}

Periode B ({period_b.label}):
  Realisasi: {period_b.realisasi}
  Komponen: {period_b.komponen}

Tren 4 Periode Sebelumnya: {trend_data}

Hasilkan analisis dalam 3-5 kalimat Bahasa Indonesia formal:
1. Sebutkan perubahan numerik dengan akurat
2. Identifikasi komponen yang paling berkontribusi terhadap perubahan
3. Tempatkan dalam konteks tren historis
4. Bersifat objektif — jangan over-claim atau over-warn
5. JANGAN tambah rekomendasi (itu tugas asesor)
```

### UX Pattern

Di setiap form indikator yang sudah ada history (minimal 1 periode sebelumnya), tambahkan tombol:

```
[ 📊 Bandingkan dengan TW Lalu ]
```

Klik → modal/drawer dengan output di atas.

### Estimasi Effort
| Item | Effort |
|------|--------|
| Backend: comparative service + prompt | 1 hari |
| Frontend: button + modal | 1 hari |
| Total | **2 hari** |

### Estimasi Biaya AI
- ~50 request/bulan × 2500 tokens × Gemini Flash = ~$0.20/bulan

---

## 2.3 Update di `docs/07_AI_INTEGRATION.md`

Setelah Section 3.6 (Action Plan Generator), **tambahkan dua section baru**:

```markdown
### 3.7 AI Inline Help (Konteks Indikator)

[konten dari section 2.1 di atas]

### 3.8 Comparative Analysis (Cross-Periode)

[konten dari section 2.2 di atas]
```

**Update juga Section 9 (Roadmap AI Features)** dengan menambah dua fitur ini ke MVP/Fase 5:

```markdown
| Fase | Fitur | Kompleksitas |
|------|-------|-------------|
| MVP (Fase 1-3) | Draft justifikasi + draft rekomendasi | Low |
| MVP+1 (Fase 4) | Anomaly detection rule-based + LLM | Medium |
| **Fase 5** | **AI Inline Help (#7)** | **Low-Medium** |
| **Fase 5** | **Comparative Analysis (#8)** | **Low** |
| Phase 2 (Fase 5b) | RAG chat dengan Pedoman | Medium |
| Phase 2 | Smart summary periode | Medium |
| Phase 2 | Action plan generator SMART | Medium |
| Future | Forecasting NKO (time series ML) | High |
| Future | Recommendation Effectiveness Tracker | High |
| Future | Auto-categorize Cluster | High |
```

## 2.4 Update di `docs/09_DEVELOPMENT_ROADMAP.md`

Di **Section 7 (Fase 5 — AI Integration)**, tambahkan deliverable baru:

```markdown
### Deliverable Fase 5 (Updated):
- ✅ Setup OpenRouter client + routing
- ✅ AI Suggestion Drawer component (UX pattern)
- ✅ **Draft Justifikasi** (PIC) — pakai Gemini Flash
- ✅ **Draft Rekomendasi** (Asesor) — pakai Gemini Flash
- ✅ **Anomaly Detection** rule-based + LLM hybrid
- ✅ **AI Inline Help** untuk indikator (NEW)
- ✅ **Comparative Analysis** cross-periode (NEW)
- ✅ AI Suggestion audit log (`ai_suggestion_log`)
- ✅ Rate limiting per user (20/min)
- ✅ Fallback graceful jika OpenRouter down
```

## 2.5 Estimasi Biaya AI Total (Updated)

Update biaya estimasi total di `docs/07_AI_INTEGRATION.md` Section 2:

```markdown
### Estimasi Biaya (untuk skala UP Tenayan) — UPDATED

| Use Case | Volume/bulan | Cost |
|----------|-------------:|-----:|
| Draft justifikasi | 200 | $0.50 |
| Draft rekomendasi | 50 | $0.20 |
| Anomaly check | 100 | $0.30 |
| Chat RAG | 100 | $1.50 |
| Summary periode | 4 | $0.30 |
| Embedding (RAG) | one-time + 100/bln | $0.05 |
| **AI Inline Help (NEW)** | **62 indikator (cached)** | **$0.10** |
| **Comparative Analysis (NEW)** | **50** | **$0.20** |

**Estimasi total:** ~$3.15/bulan (Rp 50.000) untuk MVP awal.
Naik proporsional dengan adoption.
```

---

# BAGIAN 3 — KLARIFIKASI KEPUTUSAN

Beberapa pertanyaan terbuka yang sudah dijawab dan perlu di-update di blueprint:

## 3.1 Branding Final
- ✅ **Nama aplikasi:** PULSE (Performance & Unit Live Scoring Engine)
- ✅ **Tagline:** "Denyut Kinerja Pembangkit, Real-Time."
- ✅ **Domain placeholder:** `pulse.tenayan.local`

## 3.2 Tetap Berlaku (Tidak Berubah)
Berikut keputusan dari blueprint asli yang tetap berlaku:
- ✅ Tidak ada upload evidence file
- ✅ Setiap stream maturity level pakai dynamic JSONB schema
- ✅ HCR ditunda ke Fase 6
- ✅ UI: skeuomorphic dark theme (control room digital)
- ✅ AI: Gemini 2.5 Flash untuk routine + Claude Sonnet untuk complex
- ✅ Tech stack: FastAPI + React 18 + PostgreSQL 16 + Docker Compose

## 3.3 Hal yang BELUM Diputuskan (Untuk Update Berikutnya)
Item-item ini **tidak perlu diapply sekarang**, tapi awareness:
- ❓ Logo final — akan dibuatkan terpisah atau pakai konsep dari designer
- ❓ SSL certificate strategy — keputusan saat deploy
- ❓ OpenRouter API key — Budi akan setup sendiri
- ❓ Integrasi Navitas, SAP, dll — Phase 2+

---

# BAGIAN 4 — CHECKLIST EKSEKUSI UNTUK CLAUDE CODE

Berikut langkah konkret yang harus Anda lakukan, urut:

## Step 1: Backup
- [ ] Buat branch baru: `git checkout -b feature/update-001-pulse-rebrand-ai-features`
- [ ] Pastikan tidak ada uncommitted changes di main branch

## Step 2: Rebranding
- [ ] Apply find & replace dari Section 1.3 di **semua file**
- [ ] Tambahkan section "About the Name" di README.md (Section 1.4)
- [ ] Tambahkan paragraf "Tema Pulse" di `06_DESIGN_SYSTEM_SKEUOMORPHIC.md` (Section 1.5)
- [ ] Tambahkan signature animation pulse heartbeat (Section 1.5)
- [ ] (Opsional) Update UI copy seperti di Section 1.6 — diskusi dulu dengan Budi kalau ragu

## Step 3: Database Schema Update
- [ ] Tambahkan tabel `ai_inline_help` di `docs/03_DATA_MODEL.md` (Section 2.1)
- [ ] Kalau migrasi sudah dibuat: buat migration baru `alembic revision -m "add ai_inline_help table"`
- [ ] Run migrasi: `alembic upgrade head`

## Step 4: API Endpoints
- [ ] Tambahkan endpoint AI Inline Help di `docs/04_API_SPEC.md`
- [ ] Tambahkan endpoint Comparative Analysis di `docs/04_API_SPEC.md`
- [ ] Implement endpoint di backend kalau Fase 5 sudah dimulai

## Step 5: Update Dokumentasi
- [ ] Tambahkan Section 3.7 (AI Inline Help) di `docs/07_AI_INTEGRATION.md`
- [ ] Tambahkan Section 3.8 (Comparative Analysis) di `docs/07_AI_INTEGRATION.md`
- [ ] Update Roadmap AI Features di `docs/07_AI_INTEGRATION.md` Section 9
- [ ] Update Estimasi Biaya AI di `docs/07_AI_INTEGRATION.md` Section 2
- [ ] Update Deliverable Fase 5 di `docs/09_DEVELOPMENT_ROADMAP.md`

## Step 6: Update CHANGELOG
Tambahkan entry baru di `CHANGELOG.md`:

```markdown
## [Unreleased]

### Changed
- **BREAKING:** Rebrand aplikasi dari `SISKONKIN` menjadi `PULSE` (Performance & Unit Live Scoring Engine)
  - Tagline: "Denyut Kinerja Pembangkit, Real-Time."
  - Find & replace di seluruh dokumentasi dan kode
  - Container & database name diupdate ke `pulse-*`

### Added
- Tema "Pulse Heartbeat" di design system (LED animation, NKO update ripple, loading pulse wave)
- Fitur AI #7: AI Inline Help (Konteks Indikator) — pre-computed contextual help per indikator
- Fitur AI #8: Comparative Analysis (Cross-Periode) — narasi otomatis perbandingan antar periode
- Tabel database `ai_inline_help` untuk caching
- Endpoint API `/ai/inline-help/{indikator_id}` dan `/ai/comparative-analysis`

### Updated
- Roadmap Fase 5 menambah 2 deliverable AI baru
- Estimasi biaya AI: ~$3.15/bulan (Rp 50.000)
```

## Step 7: Verifikasi
- [ ] Run grep untuk pastikan tidak ada lagi `SISKONKIN`/`siskonkin` yang lupa: `grep -ri "siskonkin\|SISKONKIN" .`
- [ ] Run docker-compose build untuk pastikan tidak error
- [ ] Test login + dashboard render normal (kalau Fase 1-3 sudah selesai)
- [ ] Update README badges/links jika ada

## Step 8: Commit & Push
```bash
git add .
git commit -m "feat: apply UPDATE-001 — rebranding PULSE + AI features expansion

- Rebrand SISKONKIN to PULSE (Performance & Unit Live Scoring Engine)
- Add tagline 'Denyut Kinerja Pembangkit, Real-Time.'
- Add Pulse Heartbeat signature animation in design system
- Add AI Feature #7: Inline Help with cached context per indicator
- Add AI Feature #8: Comparative Analysis cross-periode
- Update DB schema with ai_inline_help table
- Update API spec with 2 new endpoints
- Update roadmap Fase 5 deliverables"

git push origin feature/update-001-pulse-rebrand-ai-features
```

## Step 9: Lapor ke Budi
Setelah selesai, beri tahu Budi dengan format:

```
✅ UPDATE-001 selesai diaplikasikan.

Summary:
- File yang diubah: [jumlah]
- Migration baru: [yes/no]
- Build status: [success/error]
- Pending decisions: [list, kalau ada]

Branch: feature/update-001-pulse-rebrand-ai-features
PR/MR: [link kalau sudah dibuat]

Ready for review.
```

---

# CATATAN PENTING

## A. Kalau Ada Konflik dengan Kerjaan yang Sudah Selesai
Beberapa skenario kemungkinan:

**Skenario 1:** Anda sudah selesai Fase 1 (foundation) dengan nama SISKONKIN.
→ Apply rebranding penuh. Tidak ada masalah teknis besar, hanya naming.

**Skenario 2:** Sudah ada user data di production dengan database `siskonkin`.
→ **JANGAN drop database!** Buat database baru `pulse`, dump data dari `siskonkin`, restore ke `pulse`. Atau pakai PostgreSQL `ALTER DATABASE siskonkin RENAME TO pulse;` (perlu disconnect users dulu).

**Skenario 3:** Sudah ada commit history dengan nama lama.
→ Tidak perlu rewrite history. Mulai dari sekarang pakai nama baru.

## B. Pertanyaan untuk Budi (Ajukan Kalau Ragu)
- Apakah saat rebrand, hostname VPS juga perlu diubah? (Mis. dari `siskonkin.tenayan.local` ke `pulse.tenayan.local`?)
- Apakah ada user yang sudah dibuat dengan email mention SISKONKIN yang perlu di-update?
- Logo & favicon: apa yang dipakai? Atau pakai placeholder dulu?

## C. Future Updates
Akan ada `UPDATE-002`, `UPDATE-003`, dst untuk update berikutnya. Setiap update tunggal akan dikirim sebagai 1 file Markdown seperti ini.

---

**Selesai membaca?** Mulai dari Step 1 di Section 4 (Checklist Eksekusi).

**Stuck di tengah jalan?** Stop, log issue, lapor ke Budi sebelum lanjut.

— Tim Blueprint PULSE, Mei 2026
