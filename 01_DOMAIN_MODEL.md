# 01 — Domain Model

> Pemahaman bisnis Kontrak Kinerja (Konkin) Unit Pembangkit PT PLN Nusantara Power, sebagai fondasi semua keputusan teknis selanjutnya.

---

## 1. Hierarki Kontrak Kinerja

```
Kontrak Kinerja Unit (per tahun, ditetapkan oleh Direksi)
└── Periode (Semester 1, Semester 2)
    └── Perspektif (5 Pilar BUMN + Compliance)
        └── Indikator Kinerja Utama (KPI)
            └── Sub-Indikator / Stream Maturity Level (untuk indikator agregat)
                └── Area / Sub-Area (untuk Maturity Level)
                    └── Kriteria Level 0-5
```

## 2. Perspektif & Bobot — Konkin 2026 PLTU Tenayan

Berdasarkan dokumen `KONKIN_TENAYAN_2026.pdf` (FMZ-12.1.2.1), bobot per perspektif untuk PLTU Tenayan tahun 2026:

| Kode | Perspektif | Bobot | Sifat |
|------|-----------|------:|-------|
| I | Economic & Social Value | 46.00 | Penambah |
| II | Model Business Innovation | 25.00 | Penambah |
| III | Technology Leadership | 6.00 | Penambah |
| IV | Energize Investment | 8.00 | Penambah |
| V | Unleash Talent | 15.00 | Penambah |
| VI | Compliance | Max -10 | Pengurang |
| | **JUMLAH (I+II+III+IV+V)** | **100.00** | |

### Formula NKO Akhir

```
NKO = Σ(Nilai Pilar I s/d V) − Nilai Pengurang Compliance
```

Contoh dari NKO Semester 2 2025 PLTU Tenayan:
```
NKO = 58.12 + 10.65 + 15.38 + 8.36 + 11.30 = 103.80
NKO Final = 103.80 − 0.44 = 103.36
```

## 3. Indikator Kinerja per Perspektif (Konkin 2026)

### 3.1 Economic & Social Value (Bobot 46)

| # | Indikator | Bobot | Polaritas | Tipe |
|---|----------|------:|-----------|------|
| 1 | Pengendalian Komponen BPP Unit | 18.00 | Positif | Agregat 5 sub |
| 2 | Optimalisasi Kesiapan Pasokan Pembangkit | 6.00 | Positif | KPI Kuantitatif |
| 3 | EAF (Equivalent Availability Factor) | 6.00 | Positif | KPI Kuantitatif |
| 4 | EFOR (Equivalent Forced Outage Rate) | 6.00 | Negatif | KPI Kuantitatif |
| 5 | Pengelolaan Sustainable Development Goals (SDGs) | 10.00 | Positif | Agregat 7 sub |

**Sub-indikator BPP Unit (no.1):**
- a. Biaya Pemeliharaan (proporsi 70% UP Tenayan, 30% PLTU Tembilahan)
- b. Fisik Pemeliharaan (proporsi 70% / 30%)
- c. Biaya Administrasi
- d. Biaya Kimia dan Pelumas
- e. Penghapusan ATTB

**Sub-indikator SDGs (no.5):**
- a. Pengelolaan Komunikasi dan TJSL
- b. Tingkat Proper Unit
- c. ERM (Enterprise Risk Management)
- d. Intensitas Emisi
- e. Kepuasan Pelanggan dan Tindaklanjut Keluhan
- f. Umur Persediaan Batubara
- g. Implementasi Digitalisasi Pembayaran

### 3.2 Model Business Innovation (Bobot 25)

| # | Indikator | Bobot | Tipe |
|---|----------|------:|------|
| 1 | Maturity Level Manajemen Aset Pembangkitan | 25.00 | Maturity Level Agregat |

Indikator ini adalah agregat dari **14 sub-stream maturity level** (rata-rata):
- a. Outage Management
- b. WPC (Work Planning & Control) Management
- c. Operation Management
- d. Reliability Management
- e. Efficiency Management
- f. LCCM (Life Cycle Cost Management)
- g. Pengelolaan Energi Primer
- h. Supply Chain Management
- i. DPP (Digital Power Plant) Maturity Level
- j. Pengelolaan Keuangan
- k. Manajemen Lingkungan
- l. Manajemen K3
- m. Manajemen Keamanan
- n. Manajemen Anti Penyuapan (SMAP)

### 3.3 Technology Leadership (Bobot 6)

| # | Indikator | Bobot | Polaritas | Formula |
|---|----------|------:|-----------|---------|
| 1 | SFC Batubara | 6.00 | Negatif | `Σ Volume Bahan Bakar / Σ kWh Produksi Bruto` |

### 3.4 Energize Investment (Bobot 8)

| # | Indikator | Bobot | Tipe |
|---|----------|------:|------|
| 1 | Disburse Investasi dan PRK Investasi Terkontrak | 8.00 | Agregat 4 sub |

**Sub-indikator:**
- a1. Disburse Investasi UP Tenayan Non Tembilahan (proporsi 70%)
- a2. Disburse Investasi PLTU Tembilahan (proporsi 30%)
- b1. PRK Investasi Terkontrak UP Tenayan Non Tembilahan (proporsi 70%)
- b2. PRK Investasi Terkontrak PLTU Tembilahan (proporsi 30%)

### 3.5 Unleash Talent (Bobot 15)

| # | Indikator | Bobot | Tipe |
|---|----------|------:|------|
| 1 | Pengelolaan Human Capital, Inovasi dan Safety Culture | 15.00 | Agregat 8 sub |

**Sub-indikator:**
- a. HCR (Human Capital Readiness)
- b. OCR (Organization Capital Readiness)
- c. Pengelolaan SPKI PLN NP
- d. Penguatan Budaya
- e. Diseminasi Karya Inovasi
- f. Biaya Kesehatan
- g. Lost Time Injury Frequency Rate (target 0.106 indeks)
- h. Kontribusi Keterlibatan Pada Project Korporat

### 3.6 Compliance (Pengurang Max-10)

Pengurang NKO atas:
- Komitmen terhadap Kepatuhan, Ketepatan Laporan dan Validitas Data
- Penyelesaian Temuan Audit (Rekomendasi Jatuh Tempo Yang Harus Sudah Selesai Ditindaklanjuti)
- Penyelesaian Rekomendasi Tindaklanjut OFI
- SLA Penyelesaian Tiket dan Awareness Terkait Keamanan Siber
- Kepatuhan pada HSSE, Regulasi
- Planning Accuracy Compliance Adjustment (PACA)
- Critical Event
- ICOFR
- Pengendalian Nilai NAC (Non Allowable Cost) sesuai RKAU 2026

---

## 4. Dua Tipe Indikator: KPI Kuantitatif vs Maturity Level

Ini adalah pembedaan paling penting di domain ini.

### 4.1 Tipe A — KPI Kuantitatif

Punya formula matematis dengan input numerik. Hasilnya adalah persentase atau rasio.

**Pola umum:**
```
Pencapaian (%) = f(Realisasi, Target)
Nilai = Pencapaian × Bobot
```

**Polaritas menentukan formula:**

- **Polaritas Positif** (lebih besar = lebih baik):
  ```
  Pencapaian = (Realisasi / Target) × 100%
  ```
  Contoh: EAF, Fisik Pemeliharaan, Optimalisasi Kesiapan Pasokan.

- **Polaritas Negatif** (lebih kecil = lebih baik):
  ```
  Pencapaian = {2 − (Realisasi / Target)} × 100%
  ```
  Contoh: Biaya Pemeliharaan, Biaya Administrasi, EFOR, SFC Batubara.

**Contoh konkret (Pedoman halaman 5-6):**
- Anggaran Biaya Har: Rp 200 miliar; Realisasi: Rp 190 miliar
- Pencapaian = (2 − 190/200) × 100% = 105%
- Bobot = 3 → Nilai Indikator = 105% × 3 = 3.15

**Khusus Kepuasan Pelanggan (range-based):**
```
Jika realisasi < rentang_bawah:    Pencapaian = (realisasi / rentang_bawah) × 100%
Jika rentang_bawah ≤ realisasi ≤ rentang_atas:  Pencapaian = 100%
Jika realisasi > rentang_atas:    Pencapaian = (realisasi / rentang_atas) × 100%
```

### 4.2 Tipe B — Maturity Level

Tidak ada formula numerik tunggal. Penilaian berdasarkan **rubrik diskrit Level 0–5**:

| Level | Range | Definisi |
|-------|-------|----------|
| 0 | ≤1 | Fire Fighting (tindakan setelah ada kejadian) |
| 1 | 1<x≤2 | Stabilizing (sebatas merespon kejadian) |
| 2 | 2<x≤3 | Preventing (ada usaha pencegahan) |
| 3 | 3<x≤4 | Optimizing (optimasi sumberdaya & improvement) |
| 4 | 4<x≤5 | Excellence (continuous improvement) |

Setiap stream maturity level punya **breakdown sub-area / area** sendiri, masing-masing dengan **kriteria deskriptif berbeda per level**. Inilah sumber kompleksitas yang Anda sebut "rumit" — setiap kertas kerja unik.

**Pola Outage Management (contoh):**
```
Stream: Outage Management
├── Area: Long Term Planning
│   └── Sub-Area: Rencana dan Jadwal Planned Outage Jangka Panjang
│       ├── Level 0 ≤1: [kriteria deskriptif]
│       ├── Level 1 1<x≤2: [kriteria deskriptif]
│       ├── Level 2 2<x≤3: [kriteria deskriptif]
│       ├── Level 3 3<x≤4: [kriteria deskriptif]
│       └── Level 4 4<x≤5: [kriteria deskriptif]
├── Area: P3 (1 Week Planning)
│   ├── Sub-Area: Reviu Progres Meeting P2 & Hasil OH
│   ├── Sub-Area: Penambahan Scope Pekerjaan Overhaul
│   └── ...
└── Area: Pre Outage / During / Post Outage
    └── ...
```

**Pola SMAP/Kepatuhan (contoh dari `kertas_kerja_Kepatuhan_2026.xlsx`):**
```
Stream: SMAP (Sistem Manajemen Anti Penyuapan)
├── Klausul 4.1, 4.2, 6.2, 7.4, 7.5
│   └── Pilar: Pencegahan
│       └── Elemen: Informasi Terdokumentasi SMAP
│           └── Sub-Elemen: Informasi Terdokumentasi SMAP
│               └── Pengukuran: Kualitas Buku Manual Utama
│                   ├── Indikator: Buku manual utama memenuhi kualitas
│                   ├── Evidence: Buku manual utama
│                   ├── Level 0/1/2/3/4/5 (kriteria %)
│                   ├── Target Eviden: 5
│                   ├── Realisasi Eviden: 3
│                   ├── Pencapaian (Level): 1.5
│                   └── Pencapaian (%): 0.3
└── ... (55 indikator total)
```

**Pola HCR (Human Capital Readiness):**
Berdasarkan Pedoman halaman 59-66, HCR diukur per area:
- Strategic Workforce Planning
- Talent Acquisition
- Talent Management & Development
- Performance Management
- Reward & Recognition
- Industrial Relation
- HC Operations

Setiap area punya level 0–5. (Implementasi penuh akan menyusul, struktur data sudah disiapkan.)

### 4.3 Pembobotan ML vs KPI per Stream

Tabel 1 Pedoman menunjukkan bahwa **stream maturity level juga punya komponen KPI kuantitatif** dengan rasio pembobotan tertentu:

| Stream | Bobot ML | Bobot KPI |
|---|---:|---:|
| Outage Management | 50% | 50% |
| Reliability Management | 50% | 50% |
| SCM Pembangkit | 50% | 50% |
| Efficiency Management | 50% | 50% |
| **Operation Management** | **90%** | **10%** |
| WPC Management | 50% | 50% |
| Energi Primer (Batubara, Biomassa) | 50% | 50% |
| Energi Primer (Gas) | 70% | 30% |
| Energi Primer (BBM/BBN) | 70% | 30% |
| Digital Power Plant | 50% | 50% |
| LCCM | 50% | 50% |
| **Manajemen Lingkungan & K3** | **75%** | **25%** |
| **Manajemen Keamanan** | **60%** | **40%** |
| HCR | 50% | 50% |
| OCR (per sub) | 50% | 50% |
| OCR OWM | 55% | 45% |
| Pengelolaan Bendungan | 50% | 50% |

**Implikasi sistem:** Setiap stream punya 2 komponen yang masing-masing dihitung terpisah lalu dirata-rata berbobot.

## 5. Tabel Pembobotan Sub-KPI (Tabel 2 Pedoman)

Untuk indikator agregat, perhitungan rata-rata dengan aturan khusus jika ada sub yang tidak dinilai:

| KPI Agregat | Aturan |
|---|---|
| Biaya & Fisik Pemeliharaan | Rata-rata (50/50). Jika fisik tidak dinilai, biaya = 100% |
| Pengelolaan Komunikasi, TJSL & Proper | Rata-rata, Komunikasi & TJSL diatur pedoman terlampir |
| KPI proses manajemen aset (LCCM-PSM, ERM-Keuangan, WPC-Outage, Reliability-Efficiency, Operation-EnergiPrimer) | Rata-rata 50/50 berdasarkan realisasi maturity level. Jika salah satu tidak dinilai, KPI lain = 100% |
| Biaya & PRK Investasi Terkontrak | Rata-rata 50/50. Jika salah satu tidak dinilai, lainnya = 100% |
| HCR, OCR & Pra Karya Inovasi | Rata-rata. Jika salah satu tidak dinilai, normalisasi bobot |
| Manajemen Lingkungan, K3 & Keamanan | Rata-rata realisasi maturity level. Normalisasi jika ada yang tidak dinilai |

## 6. Periode Assessment

| Indikator | Periode |
|---|---|
| Sebagian besar KPI Kuantitatif | Semester (S1, S2) |
| Maturity Level | Semester |
| Beberapa monitoring (FRA, gratifikasi, dst) | Triwulan (TW1–TW4) |
| Sub-indikator HSE, Compliance | Bulanan/Triwulan |

**Strategi sistem SISKONKIN:** monitoring berbasis **triwulan** untuk semua indikator (TW1–TW4), dengan agregasi resmi per **semester** (TW1+TW2 = S1, TW3+TW4 = S2). Ini memberikan visibilitas yang lebih granular daripada hanya 2x per tahun.

## 7. Pemilik Proses

Setiap indikator punya **bidang pemilik proses** (Pedoman Tabel 26). Beberapa contoh utama untuk PLTU Tenayan:

| Indikator | Pemilik Proses |
|---|---|
| Biaya Pemeliharaan | BID FIN, BID ACT |
| Fisik Pemeliharaan | BID OM-1, OM-2, OM-3, OM-4, OM-5, OM-RE |
| EAF, EFOR, Optimalisasi Pasokan | BID OM (semua) |
| SFC Batubara | BID OM-1, OM-2, OM-3 |
| Reliability Management | BID REL-1 & REL-2 |
| HCR, OCR | BID HTD (+ HSC untuk OCR) |
| Manajemen Lingkungan, K3 | BID HSE |
| ERM | BID RIS |
| SCM | SSCM |
| Komitmen Ketepatan Laporan | BID CPF |
| Penyelesaian Temuan Audit | BID AUD-I, II, III |

Daftar lengkap di Pedoman Tabel 26 (akan di-seed ke database sebagai master data).

## 8. Compliance Detail

Tabel 22 Pedoman: Pengurang NKO untuk ketepatan laporan & validitas data.

**Untuk UP (seperti UP Tenayan):**
- Total laporan: 64 per tahun
- Pengurang per laporan tidak tepat waktu: 0.039
- Pengurang per laporan tidak valid datanya: 0.039
- Maksimal pengurang dari komponen ini: terbatas implisit

**Daftar laporan rutin:**

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

## 9. Glosarium Singkatan Penting

| Singkatan | Kepanjangan |
|---|---|
| NKO | Nilai Kinerja Organisasi |
| Konkin | Kontrak Kinerja |
| RKAU | Rencana Kerja Anggaran Unit |
| RKAP | Rencana Kerja Anggaran Perusahaan |
| PRK | Program Rencana Kerja |
| RUPS | Rapat Umum Pemegang Saham |
| BPP | Biaya Pokok Penyediaan |
| EAF | Equivalent Availability Factor |
| EFOR | Equivalent Forced Outage Rate |
| SFC | Specific Fuel Consumption |
| ATTB | Aktiva Tetap Tidak Beroperasi |
| DMN | Daya Mampu Netto |
| DMP | Daya Mampu Pasok |
| DPP | Digital Power Plant |
| HCR | Human Capital Readiness |
| OCR | Organization Capital Readiness |
| LCCM | Life Cycle Cost Management |
| WPC | Work Planning & Control |
| SCM | Supply Chain Management |
| ERM | Enterprise Risk Management |
| SMAP | Sistem Manajemen Anti Penyuapan |
| SDGs | Sustainable Development Goals |
| TJSL | Tanggung Jawab Sosial dan Lingkungan |
| K3 / K3LH | Keselamatan & Kesehatan Kerja (& Lingkungan Hidup) |
| LTIFR | Lost Time Injury Frequency Rate |
| OFI | Opportunity For Improvement |
| PACA | Planning Accuracy Compliance Adjustment |
| ICOFR | Internal Control Over Financial Reporting |
| NAC | Non Allowable Cost |
| FKAP | Fungsi Kepatuhan Anti Penyuapan |
| SPKI | Sertifikasi Profesi Karya Inovasi (PLN NP) |
| BID | Bidang |
| BID OM | Bidang Operasi & Maintenance |
| BID REL | Bidang Reliability |
| BID HSE | Bidang Health, Safety, Environment |
| BID HTD | Bidang Human Talent Development |
| BID HSC | Bidang Human Capital Strategic |
| BID CMR | Bidang Customer Relationship |
| BID FIN | Bidang Finance |
| BID ACT | Bidang Accounting |
| BID RIS | Bidang Risk |
| BID CPF | Bidang Compliance |
| BID AUD | Bidang Audit |
| BID CSR | Bidang Corporate Social Responsibility |
| BID EPI | Bidang Energi Primer |
| BID TDV | Bidang Transformasi Digital & Vendor |
| SSCM | Satuan Supply Chain Management |
| SPRO | Satuan Project |
| DIVPKP | Divisi Penilaian Kinerja Perusahaan |

---

**Selanjutnya:** [`02_FUNCTIONAL_SPEC.md`](02_FUNCTIONAL_SPEC.md) — bagaimana semua ini diterjemahkan ke modul fungsional aplikasi.
