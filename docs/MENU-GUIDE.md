# Panduan Menu PULSE

Dokumen ini menjelaskan menu yang ada di aplikasi PULSE, fungsi tiap halaman, siapa yang biasanya memakai menu tersebut, dan bagaimana menu saling terhubung dalam alur Konkin.

## Ringkasan Peran

| Role | Fokus akses |
|------|-------------|
| `super_admin` | Akses penuh: periode, assessment, rekomendasi, compliance, audit, master data, dashboard, AI. |
| `admin_unit` | Kelola master data Konkin dan compliance. |
| `pic_bidang` | Isi self-assessment bidangnya, submit nilai, melihat rekomendasi dan notifikasi. |
| `asesor` | Review submission, approve/override/request revision, membuat rekomendasi. |
| `manajer_unit` | Melihat dashboard eksekutif dan perkembangan kinerja. |
| `viewer` | Akses baca untuk dashboard dan informasi non-mutasi. |

## Menu Utama

| Menu | Fungsi utama | Akses umum |
|------|--------------|------------|
| Dasbor | Melihat NKO, kontribusi pilar, trend, heatmap maturity, simulator skenario, dan drilldown indikator. | Semua user login, dengan data eksekutif untuk `super_admin`, `manajer_unit`, `viewer`. |
| Assessment | PIC mengisi realisasi/target/maturity, submit self-assessment; asesor melakukan review. | `super_admin`, `pic_bidang`, `asesor`. |
| Rekomendasi | Tracking tindak lanjut rekomendasi sampai selesai atau carry-over. | Semua user login, aksi tergantung role. |
| Periode | Membuat periode Konkin dan menggerakkan lifecycle periode. | `super_admin`. |
| Compliance | Input laporan rutin dan komponen pengurang compliance yang memengaruhi NKO. | `super_admin`, `admin_unit`. |
| Audit | Melihat jejak perubahan sistem: siapa melakukan apa, kapan, dan before/after data. | `super_admin`. |
| Master Data | Mengelola struktur Konkin 2026, bidang, dan rubric maturity level. | `super_admin`, `admin_unit`. |
| Notifikasi | Melihat pemberitahuan assignment, review, dan pekerjaan yang perlu ditindaklanjuti. | Semua user login. |

## Dasbor

Dasbor adalah halaman ringkasan kinerja. Tujuannya memberi gambaran cepat tentang NKO dan komponen yang membuat nilai naik atau turun.

Yang ditampilkan:

- NKO final dan gross Pilar I-V.
- Pengurang compliance.
- Forecast dan trend NKO.
- Panel kontribusi per pilar.
- Heatmap maturity untuk stream maturity level.
- Formula ledger per stream, termasuk metode kuantitatif, maturity, dan compliance.
- Drilldown indikator/stream untuk melihat realisasi, target, nilai, kontribusi, serta detail bidang.
- Scenario simulator untuk simulasi dummy dampak perubahan EAF, EFOR, Outage maturity, dan SMAP.

Catatan data:

- Jika data live belum lengkap, dashboard dapat memakai fallback/demo snapshot agar tampilan tetap bisa diuji.
- Pada periode dummy final UAT, NKO bisa terlihat rendah karena hanya sebagian kecil session yang sudah approved.
- NKO produksi baru representatif setelah periode, session assessment, review asesor, dan compliance terisi lengkap.

## Assessment

Assessment adalah workspace utama PIC dan asesor.

Untuk PIC:

- Mengisi `target`, `realisasi`, `catatan_pic`, dan `link_eviden`.
- Mengisi rubric maturity level L0-L4 untuk stream yang berbasis maturity.
- Menandai sub-area `tidak dinilai` jika memang tidak berlaku, dengan alasan yang cukup.
- Menyimpan draft dan submit ke asesor.
- Menggunakan AI untuk draft justifikasi, inline help indikator, comparative analysis, dan bantuan membaca anomali.

Untuk asesor:

- Melihat session yang sudah `submitted`.
- Approve nilai jika sesuai.
- Override nilai final dengan catatan wajib.
- Request revision jika perlu diperbaiki PIC.
- Membuat rekomendasi inline, termasuk action item dan deadline.
- Menggunakan AI untuk draft rekomendasi SMART dan anomaly check.

Status penting:

- `draft`: masih bisa diedit PIC.
- `revision_requested`: dikembalikan asesor, bisa diedit ulang PIC.
- `submitted`: menunggu review asesor.
- `approved`: disetujui asesor.
- `overridden`: asesor menetapkan nilai final berbeda.

## Rekomendasi

Menu Rekomendasi dipakai untuk mengawal tindak lanjut setelah assessment atau review menemukan gap.

Yang bisa dilakukan:

- Melihat daftar rekomendasi beserta severity: `low`, `medium`, `high`, `critical`.
- Mengubah progress rekomendasi dalam persentase.
- Mengisi catatan progress.
- Melihat action items dan deadline.
- Mark completed saat PIC merasa tindak lanjut selesai.
- Verify close oleh asesor saat rekomendasi sudah layak ditutup.

Status rekomendasi:

- `open`: rekomendasi baru.
- `in_progress`: sedang dikerjakan.
- `pending_review`: menunggu verifikasi asesor.
- `closed`: selesai dan ditutup.
- `carried_over`: dibawa ke periode berikutnya.

## Periode

Menu Periode mengatur siklus kerja Konkin. PULSE membuat session assessment berdasarkan periode dan mapping indikator ke bidang.

Lifecycle periode:

| Status | Makna |
|--------|-------|
| `draft` | Periode dibuat, belum aktif. |
| `aktif` | Periode dibuka. |
| `self_assessment` | Sistem membuat session assessment dan PIC mulai mengisi. |
| `asesmen` | Fase review asesor. |
| `finalisasi` | Persiapan penutupan periode. |
| `closed` | Periode ditutup; rekomendasi yang belum selesai dapat carry-over. |

Tombol transisi:

- `Buka Periode`: `draft` ke `aktif`.
- `Mulai Self-Assessment`: `aktif` ke `self_assessment`, sekaligus membuat session.
- `Tutup Self-Assessment`: masuk fase `asesmen`.
- `Finalisasi`: masuk fase finalisasi.
- `Tutup Periode`: menutup periode.
- Reopen hanya untuk rollback tertentu dan membutuhkan alasan yang cukup.

## Compliance

Menu Compliance mengelola pengurang NKO dari kepatuhan laporan dan komponen compliance lain.

Bagian utama:

- Input laporan rutin.
- Input komponen compliance.
- Ringkasan total pengurang.
- Detail keterlambatan dan invaliditas laporan.
- Rekap laporan tersimpan.

Contoh logika:

- Laporan terlambat dapat menghasilkan pengurang berdasarkan jumlah hari terlambat.
- Laporan invalid dapat menambah risiko pengurang sesuai konfigurasi.
- Komponen seperti PACA, ICOFR, NAC, atau Critical Event dicatat per periode.
- Total pengurang compliance masuk ke snapshot NKO.

Catatan:

- Compliance adalah komponen pengurang, bukan penambah.
- Nilai compliance memengaruhi dashboard setelah disimpan dan NKO direcompute.

## Audit

Audit menampilkan jejak aktivitas sistem. Ini penting untuk transparansi dan pemeriksaan internal.

Yang ditampilkan:

- Waktu kejadian.
- Action atau endpoint yang dipanggil.
- Entity terkait.
- User yang melakukan perubahan.
- IP address.
- Data sebelum dan sesudah perubahan.

Gunakan Audit untuk:

- Menelusuri siapa mengubah periode, assessment, compliance, rekomendasi, atau master data.
- Membuktikan perubahan saat ada perbedaan nilai.
- Membantu troubleshooting ketika ada data yang tidak sesuai.

## Master Data

Master Data berisi fondasi Konkin yang dipakai oleh assessment dan dashboard.

Submenu:

| Submenu | Fungsi |
|---------|--------|
| Template Konkin 2026 | Melihat struktur perspektif/pilar, bobot, dan penanda pengurang/penambah. |
| Master Bidang | Melihat daftar bidang dan struktur parent/sub bidang. |
| Maturity Level Stream | Melihat rubric maturity level berbasis JSONB: area, sub-area, dan kriteria L0-L4. |

Catatan penting:

- Master Data adalah sumber struktur assessment.
- Perubahan master data dapat memengaruhi session assessment dan perhitungan NKO.
- Stream maturity berbeda-beda per indikator, sehingga satuan dan perhitungan tidak selalu sama.

## Notifikasi

Notifikasi membantu user melihat pekerjaan yang perlu ditindaklanjuti.

Contoh notifikasi:

- Assessment perlu diisi.
- Submission menunggu review.
- Rekomendasi ditugaskan.
- Status pekerjaan berubah.

Fitur:

- Melihat daftar notifikasi.
- Melihat jumlah yang belum dibaca di header.
- Menandai semua notifikasi sebagai dibaca.

## Alur Kerja Disarankan

1. `super_admin` membuat periode di menu Periode.
2. `super_admin` membuka periode sampai status `self_assessment`.
3. PIC mengisi Assessment dan submit.
4. Asesor melakukan review, approve/override/request revision.
5. Jika ada gap, asesor atau sistem membuat Rekomendasi.
6. PIC mengupdate progress Rekomendasi.
7. Admin atau PIC compliance mengisi data Compliance.
8. Manajer melihat Dasbor untuk membaca NKO, gap, trend, dan prioritas.
9. `super_admin` mengecek Audit jika ada perubahan yang perlu ditelusuri.
10. Periode difinalisasi dan ditutup setelah data dinyatakan siap.

## Data Dummy vs Data Final

Saat fase development dan UAT, beberapa data masih dummy atau placeholder. Ini sengaja dipakai agar dashboard, alur assessment, export, AI, dan compliance dapat diuji end-to-end sebelum semua angka final tersedia.

Yang perlu dipahami:

- Dummy data boleh dipakai untuk demo dan validasi alur.
- Data final produksi harus berasal dari input resmi PIC, review asesor, dan compliance aktual.
- Stream berbeda dapat memiliki formula, satuan, bobot, dan cara agregasi yang berbeda.
- Jangan membandingkan semua stream dengan satu ukuran yang sama; baca formula dan satuannya di Dashboard atau Master Data.

