---
title: "Blueprint Aplikasi Monitoring Kontrak Kinerja Unit 2026"
subtitle: "PT PLN Nusantara Power - Unit Pembangkitan Tenayan"
author: "Disusun dari dokumen KONKIN TENAYAN 2026"
date: "2026-05-13"
geometry: margin=1in
fontsize: 10pt
---

# Blueprint Aplikasi Monitoring Kontrak Kinerja Unit 2026

**Unit:** PT PLN Nusantara Power - Unit Pembangkitan Tenayan  
**Tahun:** 2026  
**Sumber:** Dokumen `KONKIN TENAYAN 2026.pdf`, halaman 1.

> Catatan: PDF sumber berupa hasil scan/gambar, sehingga sebagian teks kecil perlu divalidasi ulang saat input final. Struktur parent indicator, sub indicator, bobot, polaritas, satuan, formula utama, dan target utama telah dibaca dari tabel pada dokumen.

---

# 1. Tujuan Dokumen

Dokumen ini dibuat sebagai blueprint untuk Codex/developer dalam membangun aplikasi monitoring Kontrak Kinerja Unit. Aplikasi harus mampu memodelkan struktur indikator Konkin secara hierarkis, mulai dari indikator utama, sub indikator, maturity level/komponen penyusun, target, realisasi, bobot, polaritas, dan hasil perhitungan nilai.

Struktur utama yang harus dipahami:

```text
Kontrak Kinerja 2026
|
|-- Parent Indicator / Indikator Utama
|   |-- Sub Indikator Kinerja
|   |   |-- Maturity Level / Komponen Penyusun / Formula Item
|   |   |-- Satuan
|   |   |-- Bobot
|   |   |-- Polaritas
|   |   |-- Target Semester 1
|   |   |-- Target Semester 2
|   |   |-- Realisasi Triwulan 1-4
|
|-- Compliance / Nilai Pengurang
```

Parent indicator I sampai V memiliki total bobot 100. Parent VI yaitu Compliance tidak menambah nilai, tetapi menjadi nilai pengurang maksimal -10.

---

# 2. Definisi Level Hierarki

## 2.1 Level 1 - Parent Indicator

Parent indicator adalah kelompok besar indikator Kontrak Kinerja.

| Kode | Parent Indicator | Bobot | Tipe |
|---|---|---:|---|
| I | Economic & Social Value | 46.00 | Penambah nilai |
| II | Model Business Innovation | 25.00 | Penambah nilai |
| III | Technology Leadership | 6.00 | Penambah nilai |
| IV | Energize Investment | 8.00 | Penambah nilai |
| V | Unleash Talent | 15.00 | Penambah nilai |
| VI | Compliance | Max -10 | Pengurang nilai |

Validasi total bobot parent I sampai V:

```text
46 + 25 + 6 + 8 + 15 = 100
```

## 2.2 Level 2 - Sub Indikator Kinerja

Sub indikator adalah turunan langsung dari parent indicator. Setiap sub indikator memiliki bobot, satuan, polaritas, target, dan formula/perhitungan.

Contoh pada parent I:

```text
I. Economic & Social Value - Bobot 46
|
|-- I.1 Pengendalian Komponen BPP Unit - Bobot 18
|-- I.2 Optimalisasi Kesiapan Pasokan Pembangkit - Bobot 6
|-- I.3 EAF / Equivalent Availability Factor - Bobot 6
|-- I.4 EFOR / Equivalent Forced Outage Rate - Bobot 6
|-- I.5 Pengelolaan Sustainable Development Goals / SDGs - Bobot 10
```

Validasi bobot parent I:

```text
18 + 6 + 6 + 6 + 10 = 46
```

## 2.3 Level 3 - Maturity Level / Formula Component

Maturity level adalah item penyusun nilai pada sub indikator. Tidak semua sub indikator memiliki maturity level; beberapa menggunakan formula langsung seperti EAF, EFOR, atau SFC.

Contoh:

```text
Sub Indikator: I.1 Pengendalian Komponen BPP Unit
|
|-- a. Biaya Pemeliharaan
|   |-- a1. Biaya Pemeliharaan UP Tenayan Non Tembilahan - Proporsi 70%
|   |-- a2. Biaya Pemeliharaan PLTU Tembilahan - Proporsi 30%
|
|-- b. Fisik Pemeliharaan
|   |-- b1. Fisik Pemeliharaan UP Tenayan Non Tembilahan - Proporsi 70%
|   |-- b2. Fisik Pemeliharaan PLTU Tembilahan - Proporsi 30%
|
|-- c. Biaya Administrasi
|-- d. Biaya Kimia dan Pelumas
|-- e. Penghapusan ATTB
```

Setiap maturity level dapat memiliki kertas kerja berbeda, metode hitung berbeda, bukti/evidence berbeda, dan target berbeda.

---

# 3. Struktur Lengkap Indikator Kontrak Kinerja

# I. Economic & Social Value

**Total Bobot Parent:** 46.00

## I.1 Pengendalian Komponen BPP Unit

| Field | Nilai |
|---|---|
| Kode | I.1 |
| Sub Indikator | Pengendalian Komponen BPP Unit |
| Polaritas | UP / semakin tinggi semakin baik |
| Satuan | % |
| Bobot | 18.00 |
| Formula Type | AVERAGE_COMPONENT / rerata pencapaian komponen |
| Formula Text | Rerata pencapaian dari komponen biaya dan fisik |

### Maturity Level / Komponen Penyusun

| Kode | Komponen | Turunan | Proporsi |
|---|---|---|---:|
| a | Biaya Pemeliharaan | - | - |
| a1 | Biaya Pemeliharaan UP Tenayan Non Tembilahan | Anak dari a | 70% |
| a2 | Biaya Pemeliharaan PLTU Tembilahan | Anak dari a | 30% |
| b | Fisik Pemeliharaan | - | - |
| b1 | Fisik Pemeliharaan UP Tenayan Non Tembilahan | Anak dari b | 70% |
| b2 | Fisik Pemeliharaan PLTU Tembilahan | Anak dari b | 30% |
| c | Biaya Administrasi | - | - |
| d | Biaya Kimia dan Pelumas | - | - |
| e | Penghapusan ATTB | - | - |

### Target

| Komponen | Semester 1 | Semester 2 |
|---|---:|---:|
| a. Biaya Pemeliharaan | 100% | 100% |
| b. Fisik Pemeliharaan | 100% | 100% |
| c. Biaya Administrasi | 98% | 98% |
| d. Biaya Kimia dan Pelumas | 100% | 100% |
| e. Penghapusan ATTB | 100% | 100% |

## I.2 Optimalisasi Kesiapan Pasokan Pembangkit

| Field | Nilai |
|---|---|
| Kode | I.2 |
| Sub Indikator | Optimalisasi Kesiapan Pasokan Pembangkit |
| Polaritas | UP / semakin tinggi semakin baik |
| Satuan | % |
| Bobot | 6.00 |
| Formula Type | CUSTOM |
| Formula Text | Sigma(Daya Mampu Pasok / Daya Mampu Netto x rata-rata tertimbang DMN x 100%) |

### Target

| Semester 1 | Semester 2 |
|---:|---:|
| 83.77% | 83.77% |

## I.3 EAF / Equivalent Availability Factor

| Field | Nilai |
|---|---|
| Kode | I.3 |
| Sub Indikator | EAF / Equivalent Availability Factor |
| Polaritas | UP / semakin tinggi semakin baik |
| Satuan | % |
| Bobot | 6.00 |
| Formula Type | CUSTOM |

### Formula

```text
Sigma(AH - EPDH - EMDH - EFDH) x DMN x 100%
------------------------------------------------
Sigma(PH x DMN)
```

### Target

| Semester 1 | Semester 2 |
|---:|---:|
| 77.00% | 80.27% |

## I.4 EFOR / Equivalent Forced Outage Rate

| Field | Nilai |
|---|---|
| Kode | I.4 |
| Sub Indikator | EFOR / Equivalent Forced Outage Rate |
| Polaritas | DOWN / semakin rendah semakin baik |
| Satuan | % |
| Bobot | 6.00 |
| Formula Type | CUSTOM |

### Formula

```text
Sigma[(FOH + EFDH) x DMN]
---------------------------------------- x 100%
Sigma[(FOH + SH + EFDHRS) x DMN]
```

### Target

| Semester 1 | Semester 2 |
|---:|---:|
| 3.02% | 3.44% |

## I.5 Pengelolaan Sustainable Development Goals / SDGs

| Field | Nilai |
|---|---|
| Kode | I.5 |
| Sub Indikator | Pengelolaan Sustainable Development Goals / SDGs |
| Polaritas | UP / semakin tinggi semakin baik |
| Satuan | % |
| Bobot | 10.00 |
| Formula Type | AVERAGE_COMPONENT |
| Formula Text | Rerata pencapaian dari komponen SDGs |

### Maturity Level / Komponen Penyusun

| Kode | Komponen |
|---|---|
| a | Pengelolaan Komunikasi dan TJSL |
| b | Tingkat Proper Unit |
| c | ERM / Enterprise Risk Management |
| d | Intensitas Emisi |
| e | Kepuasan Pelanggan dan Tindak Lanjut Keluhan Saran Pelanggan |
| f | Umur Persediaan Batubara |
| g | Implementasi Digitalisasi Pembayaran |

### Target

| Komponen | Semester 1 | Semester 2 |
|---|---|---|
| a. Pengelolaan Komunikasi dan TJSL | 100% | 100% |
| b. Tingkat Proper Unit | - | Beyond Compliance |
| c. ERM / Enterprise Risk Management | 100% | 100% |
| d. Intensitas Emisi | 100% | 100% |
| e. Kepuasan Pelanggan dan Tindak Lanjut Keluhan Saran Pelanggan | 100% | Sangat Memuaskan |
| f. Umur Persediaan Batubara | 100% | 100% |
| g. Implementasi Digitalisasi Pembayaran | 75% | 95% |

---

# II. Model Business Innovation

**Total Bobot Parent:** 25.00

## II.1 Maturity Level Manajemen Aset Pembangkit

| Field | Nilai |
|---|---|
| Kode | II.1 |
| Sub Indikator | Maturity Level Manajemen Aset Pembangkit |
| Polaritas | UP / semakin tinggi semakin baik |
| Satuan | Level |
| Bobot | 25.00 |
| Formula Type | MATURITY_AVERAGE |
| Formula Text | Rerata hasil assessment maturity level |

### Maturity Level / Komponen Penyusun

| Kode | Komponen |
|---|---|
| a | Outage Management |
| b | WPC / Work Planning & Control Management |
| c | Operation Management |
| d | Reliability Management |
| e | Efficiency Management |
| f | LCCM / Life Cycle Cost Management |
| g | Pengelolaan Energi Primer |
| h | Supply Chain Management |
| i | DPP / Digital Power Plant Maturity Level |
| j | Pengelolaan Keuangan |
| k | Manajemen Lingkungan |
| l | Manajemen K3 |
| m | Manajemen Keamanan |
| n | Manajemen Anti Penyuapan |

### Target

| Semester 1 | Semester 2 |
|---:|---:|
| 3.27 | 3.34 |

---

# III. Technology Leadership

**Total Bobot Parent:** 6.00

## III.1 SFC / Specific Fuel Consumption Batubara

| Field | Nilai |
|---|---|
| Kode | III.1 |
| Sub Indikator | SFC / Specific Fuel Consumption Batubara |
| Polaritas | DOWN / semakin rendah semakin baik |
| Satuan | kg/kWh |
| Bobot | 6.00 |
| Formula Type | CUSTOM |

### Formula

```text
Sigma Volume Pemakaian Bahan Bakar
-----------------------------------
Sigma kWh Produksi Bruto
```

### Target

| Semester 1 | Semester 2 |
|---:|---:|
| 0.7749 kg/kWh | 0.7749 kg/kWh |

---

# IV. Energize Investment

**Total Bobot Parent:** 8.00

## IV.1 Disburse Investasi dan PRK Investasi Terkontrak

| Field | Nilai |
|---|---|
| Kode | IV.1 |
| Sub Indikator | Disburse Investasi dan PRK Investasi Terkontrak |
| Polaritas | UP / semakin tinggi semakin baik |
| Satuan | % |
| Bobot | 8.00 |
| Formula Type | AVERAGE_COMPONENT |
| Formula Text | Rerata pencapaian disburse investasi dan PRK investasi terkontrak |

### Maturity Level / Komponen Penyusun

| Kode | Komponen | Turunan | Proporsi |
|---|---|---|---:|
| a | Disburse Investasi | - | - |
| a1 | Disburse Investasi UP Tenayan Non Tembilahan | Anak dari a | 70% |
| a2 | Disburse Investasi PLTU Tembilahan | Anak dari a | 30% |
| b | PRK Investasi Terkontrak | - | - |
| b1 | PRK Investasi Terkontrak UP Tenayan Non Tembilahan | Anak dari b | 70% |
| b2 | PRK Investasi Terkontrak PLTU Tembilahan | Anak dari b | 30% |

### Target

| Semester 1 | Semester 2 |
|---:|---:|
| 100.00% | 100.00% |

---

# V. Unleash Talent

**Total Bobot Parent:** 15.00

## V.1 Pengelolaan Human Capital, Inovasi dan Safety Culture

| Field | Nilai |
|---|---|
| Kode | V.1 |
| Sub Indikator | Pengelolaan Human Capital, Inovasi dan Safety Culture |
| Polaritas | UP / semakin tinggi semakin baik |
| Satuan | % |
| Bobot | 15.00 |
| Formula Type | AVERAGE_COMPONENT |
| Formula Text | Rerata pencapaian komponen human capital, inovasi, dan safety culture |

### Maturity Level / Komponen Penyusun

| Kode | Komponen |
|---|---|
| a | HCR / Human Capital Readiness |
| b | OCR / Organization Capital Readiness |
| c | Pengelolaan SPKI PLN NP |
| d | Penguatan Budaya |
| e | Diseminasi Karya Inovasi |
| f | Biaya Kesehatan |
| g | Lost Time Injury Frequency Rate |
| h | Kontribusi Keterlibatan pada Project Korporat |

### Target

| Komponen | Semester 1 | Semester 2 |
|---|---|---|
| a. HCR / Human Capital Readiness | 100% | 100% |
| b. OCR / Organization Capital Readiness | 100% | 100% |
| c. Pengelolaan SPKI PLN NP | 100% | 100% |
| d. Penguatan Budaya | 100% | 100% |
| e. Diseminasi Karya Inovasi | - | 1 judul |
| f. Biaya Kesehatan | 100% | 100% |
| g. Lost Time Injury Frequency Rate | 0.106 indeks | 0.106 indeks |
| h. Kontribusi Keterlibatan pada Project Korporat | 100% | 100% |

---

# VI. Compliance / Nilai Pengurang

**Tipe:** Penalti / nilai pengurang  
**Maksimal pengurang:** -10  
**Catatan:** Compliance tidak masuk ke total bobot 100. Nilainya mengurangi total skor akhir.

## VI.1 Compliance

| Field | Nilai |
|---|---|
| Kode | VI.1 |
| Sub Indikator | Compliance / GCG, Kepatuhan K3L, Audit, Reporting, PACA, Critical Event, NAC |
| Polaritas | DOWN / semakin kecil pengurang semakin baik |
| Satuan | Nilai Pengurang |
| Bobot | 0 |
| Max Penalty | -10 |
| Formula Type | PENALTY_SUM |

### Komponen Pengurang

| Kode | Komponen |
|---|---|
| a | Komitmen terhadap Kepatuhan, Ketepatan Laporan, dan Validitas Data |
| b | Penyelesaian Temuan Audit / rekomendasi jatuh tempo yang harus selesai ditindaklanjuti |
| c | Penyelesaian Rekomendasi Tindak Lanjut OFI |
| d | SLA Penyelesaian Tiket dan Awareness terkait Keamanan Siber |
| e | Kepatuhan pada HSSE dan Regulasi |
| f | Planning Accuracy Compliance Adjustment / PACA |
| g | Critical Event |
| h | ICOFR |
| i | Pengendalian Nilai NAC / Non Allowable Cost sesuai RKAP 2026 |

---

# 4. Rekap Total Bobot

| Parent | Bobot |
|---|---:|
| I. Economic & Social Value | 46.00 |
| II. Model Business Innovation | 25.00 |
| III. Technology Leadership | 6.00 |
| IV. Energize Investment | 8.00 |
| V. Unleash Talent | 15.00 |
| **Total Bobot I-V** | **100.00** |
| VI. Compliance | **Max -10, bukan bobot penambah** |

Validasi yang wajib dibuat di aplikasi:

```text
sum(parent.weight where is_penalty = false) harus sama dengan 100
sum(sub_indicator.weight dalam satu parent) harus sama dengan parent.weight
compliance tidak boleh dihitung sebagai bobot positif
```

---

# 5. Konsep Polaritas

Aplikasi harus menyimpan polaritas pada setiap sub indikator.

| Polaritas | Arti | Rumus Umum Pencapaian |
|---|---|---|
| UP | Semakin tinggi realisasi semakin baik | actual / target x 100 |
| DOWN | Semakin rendah realisasi semakin baik | target / actual x 100 |

## Indikator Polaritas UP

| Kode | Indikator |
|---|---|
| I.1 | Pengendalian Komponen BPP Unit |
| I.2 | Optimalisasi Kesiapan Pasokan Pembangkit |
| I.3 | EAF |
| I.5 | Pengelolaan SDGs |
| II.1 | Maturity Level Manajemen Aset Pembangkit |
| IV.1 | Disburse Investasi dan PRK Investasi Terkontrak |
| V.1 | Pengelolaan Human Capital, Inovasi dan Safety Culture |

## Indikator Polaritas DOWN

| Kode | Indikator |
|---|---|
| I.4 | EFOR |
| III.1 | SFC Batubara |
| VI.1 | Compliance |

---

# 6. Periode Target dan Monitoring

Target pada dokumen dibagi menjadi Semester 1 dan Semester 2. Namun aplikasi harus mendukung monitoring setiap triwulan karena pelaporan dilakukan berkala.

| Periode Input | Target Acuan |
|---|---|
| Triwulan 1 | Target Semester 1 |
| Triwulan 2 | Target Semester 1 |
| Triwulan 3 | Target Semester 2 |
| Triwulan 4 | Target Semester 2 |
| Semester 1 | Agregasi Triwulan 1 dan Triwulan 2 |
| Semester 2 | Agregasi Triwulan 3 dan Triwulan 4 |
| Tahunan | Agregasi Semester 1 dan Semester 2 |

Catatan implementasi:

```text
Aplikasi harus menyimpan target per semester, tetapi realisasi bisa diinput per triwulan.
Untuk indikator tertentu, realisasi semester/tahunan harus bisa dihitung dari data triwulan sesuai metode masing-masing kertas kerja.
```

---

# 7. Rekomendasi Struktur Database

## 7.1 Table: performance_contracts

```sql
id
year
unit_name
document_code
document_title
status
created_at
updated_at
```

Contoh:

```json
{
  "year": 2026,
  "unit_name": "Unit Pembangkitan Tenayan",
  "document_title": "Kontrak Kinerja PT PLN Nusantara Power Unit Pembangkitan Tenayan Tahun 2026",
  "status": "active"
}
```

## 7.2 Table: indicator_groups

Untuk parent indicator.

```sql
id
contract_id
code
name
weight
order_index
is_penalty
created_at
updated_at
```

Contoh:

```json
{
  "code": "I",
  "name": "Economic & Social Value",
  "weight": 46.00,
  "is_penalty": false
}
```

```json
{
  "code": "VI",
  "name": "Compliance",
  "weight": 0,
  "is_penalty": true
}
```

## 7.3 Table: indicators

Untuk sub indikator kinerja.

```sql
id
group_id
code
name
polarity
unit
weight
formula_type
formula_text
order_index
is_penalty
max_penalty
created_at
updated_at
```

Contoh:

```json
{
  "group_code": "I",
  "code": "I.3",
  "name": "EAF / Equivalent Availability Factor",
  "polarity": "UP",
  "unit": "%",
  "weight": 6.00,
  "formula_type": "CUSTOM"
}
```

## 7.4 Table: maturity_components

Untuk breakdown formula, maturity level, atau komponen penyusun.

```sql
id
indicator_id
parent_component_id
code
name
description
proportion
unit
calculation_type
workpaper_template_id
order_index
created_at
updated_at
```

Contoh:

```json
{
  "indicator_code": "I.1",
  "code": "a1",
  "name": "Biaya Pemeliharaan UP Tenayan Non Tembilahan",
  "parent_component_code": "a",
  "proportion": 70
}
```

## 7.5 Table: indicator_targets

Untuk target per semester atau triwulan.

```sql
id
indicator_id
component_id
period_type
period_name
target_value
target_text
unit
year
created_at
updated_at
```

Contoh angka:

```json
{
  "indicator_code": "I.3",
  "period_type": "SEMESTER",
  "period_name": "Semester 1",
  "target_value": 77.00,
  "unit": "%"
}
```

Contoh teks:

```json
{
  "indicator_code": "I.5",
  "component_code": "b",
  "period_type": "SEMESTER",
  "period_name": "Semester 2",
  "target_text": "Beyond Compliance"
}
```

## 7.6 Table: actual_realizations

Untuk input realisasi per triwulan/semester.

```sql
id
indicator_id
component_id
period_type
period_name
actual_value
actual_text
evidence_file_url
notes
input_by
verified_by
verification_status
created_at
updated_at
```

## 7.7 Table: workpaper_templates

Karena setiap maturity level dapat memiliki kertas kerja berbeda.

```sql
id
code
name
description
calculation_method
template_file_url
created_at
updated_at
```

## 7.8 Table: workpaper_results

Untuk hasil hitung dari kertas kerja.

```sql
id
workpaper_template_id
indicator_id
component_id
period_name
raw_input_json
calculated_value
calculated_score
notes
created_at
updated_at
```

---

# 8. Aturan Perhitungan Nilai

## 8.1 Rumus Umum Pencapaian

Untuk indikator polaritas UP:

```text
achievement = actual / target x 100
```

Untuk indikator polaritas DOWN:

```text
achievement = target / actual x 100
```

Namun rumus umum ini tidak boleh hardcoded untuk semua indikator, karena beberapa indikator memiliki formula khusus seperti EAF, EFOR, SFC, maturity level, atau target kualitatif.

## 8.2 Nilai Tertimbang Sub Indikator

```text
weighted_score = achievement_score x indicator_weight / 100
```

Contoh:

```text
Achievement EAF = 98%
Bobot EAF = 6
Weighted score = 98 x 6 / 100 = 5.88
```

## 8.3 Nilai Parent Indicator

```text
parent_score = sum(weighted_score seluruh sub indikator dalam parent)
```

Contoh:

```text
Economic & Social Value = Score I.1 + Score I.2 + Score I.3 + Score I.4 + Score I.5
```

## 8.4 Nilai Akhir Sebelum Compliance

```text
total_score_before_penalty =
Score Parent I + Score Parent II + Score Parent III + Score Parent IV + Score Parent V
```

Maksimal teoritis adalah 100.

## 8.5 Nilai Akhir Setelah Compliance

```text
final_score = total_score_before_penalty + compliance_penalty
```

Contoh:

```text
total_score_before_penalty = 97.25
compliance_penalty = -3.00
final_score = 94.25
```

---

# 9. JSON Master Data untuk Seed Database

```json
{
  "contract": {
    "year": 2026,
    "unit": "Unit Pembangkitan Tenayan",
    "title": "Kontrak Kinerja PT PLN Nusantara Power Unit Pembangkitan Tenayan Tahun 2026",
    "total_weight": 100
  },
  "indicator_groups": [
    {
      "code": "I",
      "name": "Economic & Social Value",
      "weight": 46,
      "is_penalty": false,
      "indicators": [
        {
          "code": "I.1",
          "name": "Pengendalian Komponen BPP Unit",
          "polarity": "UP",
          "unit": "%",
          "weight": 18,
          "formula_type": "AVERAGE_COMPONENT",
          "formula_text": "Rerata pencapaian komponen biaya dan fisik",
          "components": [
            {
              "code": "a",
              "name": "Biaya Pemeliharaan",
              "children": [
                { "code": "a1", "name": "Biaya Pemeliharaan UP Tenayan Non Tembilahan", "proportion": 70 },
                { "code": "a2", "name": "Biaya Pemeliharaan PLTU Tembilahan", "proportion": 30 }
              ]
            },
            {
              "code": "b",
              "name": "Fisik Pemeliharaan",
              "children": [
                { "code": "b1", "name": "Fisik Pemeliharaan UP Tenayan Non Tembilahan", "proportion": 70 },
                { "code": "b2", "name": "Fisik Pemeliharaan PLTU Tembilahan", "proportion": 30 }
              ]
            },
            { "code": "c", "name": "Biaya Administrasi" },
            { "code": "d", "name": "Biaya Kimia dan Pelumas" },
            { "code": "e", "name": "Penghapusan ATTB" }
          ],
          "targets": {
            "semester_1": { "a": "100%", "b": "100%", "c": "98%", "d": "100%", "e": "100%" },
            "semester_2": { "a": "100%", "b": "100%", "c": "98%", "d": "100%", "e": "100%" }
          }
        },
        {
          "code": "I.2",
          "name": "Optimalisasi Kesiapan Pasokan Pembangkit",
          "polarity": "UP",
          "unit": "%",
          "weight": 6,
          "formula_type": "CUSTOM",
          "formula_text": "Sigma(Daya Mampu Pasok / Daya Mampu Netto x rata-rata tertimbang DMN x 100%)",
          "targets": { "semester_1": 83.77, "semester_2": 83.77 }
        },
        {
          "code": "I.3",
          "name": "EAF / Equivalent Availability Factor",
          "polarity": "UP",
          "unit": "%",
          "weight": 6,
          "formula_type": "CUSTOM",
          "formula_text": "Sigma(AH - EPDH - EMDH - EFDH) x DMN x 100% / Sigma(PH x DMN)",
          "targets": { "semester_1": 77.00, "semester_2": 80.27 }
        },
        {
          "code": "I.4",
          "name": "EFOR / Equivalent Forced Outage Rate",
          "polarity": "DOWN",
          "unit": "%",
          "weight": 6,
          "formula_type": "CUSTOM",
          "formula_text": "Sigma[(FOH + EFDH) x DMN] / Sigma[(FOH + SH + EFDHRS) x DMN] x 100%",
          "targets": { "semester_1": 3.02, "semester_2": 3.44 }
        },
        {
          "code": "I.5",
          "name": "Pengelolaan Sustainable Development Goals / SDGs",
          "polarity": "UP",
          "unit": "%",
          "weight": 10,
          "formula_type": "AVERAGE_COMPONENT",
          "components": [
            { "code": "a", "name": "Pengelolaan Komunikasi dan TJSL" },
            { "code": "b", "name": "Tingkat Proper Unit" },
            { "code": "c", "name": "ERM / Enterprise Risk Management" },
            { "code": "d", "name": "Intensitas Emisi" },
            { "code": "e", "name": "Kepuasan Pelanggan dan Tindak Lanjut Keluhan Saran Pelanggan" },
            { "code": "f", "name": "Umur Persediaan Batubara" },
            { "code": "g", "name": "Implementasi Digitalisasi Pembayaran" }
          ],
          "targets": {
            "semester_1": { "a": "100%", "b": "-", "c": "100%", "d": "100%", "e": "100%", "f": "100%", "g": "75%" },
            "semester_2": { "a": "100%", "b": "Beyond Compliance", "c": "100%", "d": "100%", "e": "Sangat Memuaskan", "f": "100%", "g": "95%" }
          }
        }
      ]
    },
    {
      "code": "II",
      "name": "Model Business Innovation",
      "weight": 25,
      "is_penalty": false,
      "indicators": [
        {
          "code": "II.1",
          "name": "Maturity Level Manajemen Aset Pembangkit",
          "polarity": "UP",
          "unit": "Level",
          "weight": 25,
          "formula_type": "MATURITY_AVERAGE",
          "components": [
            { "code": "a", "name": "Outage Management" },
            { "code": "b", "name": "WPC / Work Planning & Control Management" },
            { "code": "c", "name": "Operation Management" },
            { "code": "d", "name": "Reliability Management" },
            { "code": "e", "name": "Efficiency Management" },
            { "code": "f", "name": "LCCM / Life Cycle Cost Management" },
            { "code": "g", "name": "Pengelolaan Energi Primer" },
            { "code": "h", "name": "Supply Chain Management" },
            { "code": "i", "name": "DPP / Digital Power Plant Maturity Level" },
            { "code": "j", "name": "Pengelolaan Keuangan" },
            { "code": "k", "name": "Manajemen Lingkungan" },
            { "code": "l", "name": "Manajemen K3" },
            { "code": "m", "name": "Manajemen Keamanan" },
            { "code": "n", "name": "Manajemen Anti Penyuapan" }
          ],
          "targets": { "semester_1": 3.27, "semester_2": 3.34 }
        }
      ]
    },
    {
      "code": "III",
      "name": "Technology Leadership",
      "weight": 6,
      "is_penalty": false,
      "indicators": [
        {
          "code": "III.1",
          "name": "SFC / Specific Fuel Consumption Batubara",
          "polarity": "DOWN",
          "unit": "kg/kWh",
          "weight": 6,
          "formula_type": "CUSTOM",
          "formula_text": "Sigma Volume Pemakaian Bahan Bakar / Sigma kWh Produksi Bruto",
          "targets": { "semester_1": 0.7749, "semester_2": 0.7749 }
        }
      ]
    },
    {
      "code": "IV",
      "name": "Energize Investment",
      "weight": 8,
      "is_penalty": false,
      "indicators": [
        {
          "code": "IV.1",
          "name": "Disburse Investasi dan PRK Investasi Terkontrak",
          "polarity": "UP",
          "unit": "%",
          "weight": 8,
          "formula_type": "AVERAGE_COMPONENT",
          "components": [
            {
              "code": "a",
              "name": "Disburse Investasi",
              "children": [
                { "code": "a1", "name": "Disburse Investasi UP Tenayan Non Tembilahan", "proportion": 70 },
                { "code": "a2", "name": "Disburse Investasi PLTU Tembilahan", "proportion": 30 }
              ]
            },
            {
              "code": "b",
              "name": "PRK Investasi Terkontrak",
              "children": [
                { "code": "b1", "name": "PRK Investasi Terkontrak UP Tenayan Non Tembilahan", "proportion": 70 },
                { "code": "b2", "name": "PRK Investasi Terkontrak PLTU Tembilahan", "proportion": 30 }
              ]
            }
          ],
          "targets": { "semester_1": 100, "semester_2": 100 }
        }
      ]
    },
    {
      "code": "V",
      "name": "Unleash Talent",
      "weight": 15,
      "is_penalty": false,
      "indicators": [
        {
          "code": "V.1",
          "name": "Pengelolaan Human Capital, Inovasi dan Safety Culture",
          "polarity": "UP",
          "unit": "%",
          "weight": 15,
          "formula_type": "AVERAGE_COMPONENT",
          "components": [
            { "code": "a", "name": "HCR / Human Capital Readiness" },
            { "code": "b", "name": "OCR / Organization Capital Readiness" },
            { "code": "c", "name": "Pengelolaan SPKI PLN NP" },
            { "code": "d", "name": "Penguatan Budaya" },
            { "code": "e", "name": "Diseminasi Karya Inovasi" },
            { "code": "f", "name": "Biaya Kesehatan" },
            { "code": "g", "name": "Lost Time Injury Frequency Rate" },
            { "code": "h", "name": "Kontribusi Keterlibatan pada Project Korporat" }
          ],
          "targets": {
            "semester_1": { "a": "100%", "b": "100%", "c": "100%", "d": "100%", "e": "-", "f": "100%", "g": "0.106 indeks", "h": "100%" },
            "semester_2": { "a": "100%", "b": "100%", "c": "100%", "d": "100%", "e": "1 judul", "f": "100%", "g": "0.106 indeks", "h": "100%" }
          }
        }
      ]
    },
    {
      "code": "VI",
      "name": "Compliance",
      "weight": 0,
      "is_penalty": true,
      "max_penalty": -10,
      "indicators": [
        {
          "code": "VI.1",
          "name": "Compliance / GCG, Kepatuhan K3L, Audit, Reporting, PACA, Critical Event, NAC",
          "polarity": "DOWN",
          "unit": "Nilai Pengurang",
          "weight": 0,
          "max_penalty": -10,
          "formula_type": "PENALTY_SUM",
          "components": [
            { "code": "a", "name": "Komitmen terhadap Kepatuhan, Ketepatan Laporan dan Validitas Data" },
            { "code": "b", "name": "Penyelesaian Temuan Audit" },
            { "code": "c", "name": "Penyelesaian Rekomendasi Tindak Lanjut OFI" },
            { "code": "d", "name": "SLA Penyelesaian Tiket dan Awareness terkait Keamanan Siber" },
            { "code": "e", "name": "Kepatuhan pada HSSE dan Regulasi" },
            { "code": "f", "name": "Planning Accuracy Compliance Adjustment / PACA" },
            { "code": "g", "name": "Critical Event" },
            { "code": "h", "name": "ICOFR" },
            { "code": "i", "name": "Pengendalian Nilai NAC / Non Allowable Cost sesuai RKAP 2026" }
          ]
        }
      ]
    }
  ]
}
```

---

# 10. Instruksi Teknis untuk Codex

Gunakan aturan berikut saat membangun aplikasi:

```text
1. Buat master data kontrak kinerja berbasis tahun dan unit.

2. Setiap kontrak memiliki beberapa parent indicator.

3. Setiap parent indicator memiliki sub indicator.

4. Setiap sub indicator dapat memiliki:
   - formula langsung,
   - maturity components,
   - child components,
   - workpaper berbeda,
   - target semester,
   - realisasi triwulan.

5. Bobot diberikan pada sub indicator, lalu dijumlahkan ke parent.

6. Total bobot parent I sampai V harus selalu 100.

7. Parent VI Compliance tidak masuk total bobot 100.
   Compliance adalah nilai pengurang maksimal -10.

8. Aplikasi harus mendukung target semester, tetapi realisasi diinput per triwulan.

9. Triwulan 1 dan 2 menggunakan target Semester 1.
   Triwulan 3 dan 4 menggunakan target Semester 2.

10. Setiap maturity level harus bisa dihubungkan dengan kertas kerja berbeda.

11. Target dapat berupa angka atau teks.
    Contoh angka: 77.00, 0.7749, 3.27.
    Contoh teks: Beyond Compliance, Sangat Memuaskan, 1 judul, 100% sesuai ketentuan.

12. Sistem scoring harus fleksibel karena tidak semua indikator dapat dihitung dengan rumus actual/target.
```

---

# 11. Output Dashboard yang Disarankan

Dashboard utama aplikasi sebaiknya menampilkan:

```text
1. Nilai total Kontrak Kinerja tahun berjalan
2. Nilai sebelum Compliance
3. Nilai pengurang Compliance
4. Nilai akhir setelah Compliance
5. Progress per parent indicator
6. Progress per sub indikator
7. Status pencapaian
8. Evidence / dokumen pendukung per maturity level
9. Riwayat input per triwulan
10. Export laporan untuk Kantor Pusat
```

## Status Pencapaian yang Disarankan

| Status | Arti |
|---|---|
| Achieved | Realisasi memenuhi atau melampaui target |
| On Track | Realisasi masih sesuai jalur pencapaian |
| At Risk | Realisasi berisiko tidak memenuhi target |
| Not Achieved | Realisasi tidak memenuhi target |
| Not Yet Reported | Belum ada input realisasi |

---

# 12. Catatan Penting untuk Developer

Pada dokumen terdapat catatan bahwa perhitungan Nilai Kinerja Organisasi mengikuti breakdown KM dan/atau penetapan revisi RKAP termutakhir. Artinya, aplikasi tidak boleh mengunci rumus secara hardcoded sepenuhnya.

Aplikasi harus memiliki fitur admin untuk:

```text
1. Mengubah target
2. Mengubah bobot
3. Mengubah formula
4. Mengubah proporsi
5. Mengubah template kertas kerja
6. Mengubah mapping maturity level
7. Mengubah aturan scoring jika ada revisi RKAP/KM
```

Dengan demikian, struktur terbaik adalah configurable KPI engine, bukan kalkulator statis.

---

# 13. Ringkasan untuk Codex

Bangun aplikasi sebagai sistem KPI hierarkis dengan karakteristik berikut:

```text
Contract -> Parent Indicator -> Sub Indicator -> Maturity Component -> Workpaper Result -> Score
```

Aturan paling penting:

```text
- Total bobot indikator I-V = 100.
- Compliance adalah pengurang, bukan bobot positif.
- Target disimpan per semester.
- Realisasi diinput per triwulan.
- Maturity level dapat memiliki formula dan kertas kerja sendiri.
- Formula harus configurable.
- Target bisa numeric atau textual.
- Dashboard harus menampilkan skor parent, skor sub indikator, skor akhir, dan penalti compliance.
```
