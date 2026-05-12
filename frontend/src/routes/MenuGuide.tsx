import { Link } from "react-router-dom";
import { SkBadge, SkButton, SkPanel } from "@/components/skeuomorphic";

type MenuItem = {
  name: string;
  route: string;
  roles: string;
  purpose: string;
  whenToUse: string;
};

type StreamNote = {
  group: string;
  unit: string;
  calculation: string;
  example: string;
};

const menus: MenuItem[] = [
  {
    name: "Dasbor",
    route: "/dashboard",
    roles: "Semua role",
    purpose: "Ringkasan NKO, status pilar, trend, heatmap maturity, dan perhatian utama.",
    whenToUse: "Dibuka pertama kali untuk melihat kondisi semester atau triwulan secara cepat.",
  },
  {
    name: "Assessment",
    route: "/assessment",
    roles: "PIC, Asesor, Super Admin",
    purpose: "Tempat PIC mengisi self-assessment dan asesor melakukan review, override, atau request revisi.",
    whenToUse: "Dipakai saat periode sudah masuk tahap self-assessment atau asesmen.",
  },
  {
    name: "Rekomendasi",
    route: "/recommendations",
    roles: "PIC, Asesor, Manajemen",
    purpose: "Tracker tindak lanjut hasil asesmen: open, in progress, pending review, closed, atau carried over.",
    whenToUse: "Dipakai setelah temuan atau gap muncul dari assessment dan harus ditindaklanjuti.",
  },
  {
    name: "Periode",
    route: "/periode",
    roles: "Super Admin",
    purpose: "Membuat dan mengatur lifecycle periode Konkin, termasuk pembentukan assessment session.",
    whenToUse: "Dipakai sebelum assessment dimulai, saat berpindah tahap, dan saat periode akan ditutup.",
  },
  {
    name: "Compliance",
    route: "/compliance",
    roles: "Super Admin, Admin Unit",
    purpose: "Mencatat laporan rutin dan komponen compliance yang menjadi pengurang NKO.",
    whenToUse: "Dipakai oleh fungsi compliance/CPF untuk memastikan keterlambatan dan pengurang tercatat.",
  },
  {
    name: "Audit",
    route: "/audit-logs",
    roles: "Super Admin",
    purpose: "Jejak perubahan mutating action: siapa mengubah apa, kapan, nilai sebelum, dan nilai sesudah.",
    whenToUse: "Dipakai saat investigasi, rekonsiliasi, atau pembuktian proses asesmen.",
  },
  {
    name: "Master Data",
    route: "/master/konkin-template/2026",
    roles: "Super Admin, Admin Unit",
    purpose: "Struktur Konkin 2026: perspektif, indikator, bidang, dan blueprint maturity level stream.",
    whenToUse: "Dipakai saat setup awal, koreksi blueprint, atau validasi rumus/satuan tiap indikator.",
  },
  {
    name: "Notifikasi",
    route: "/notifications",
    roles: "Semua role",
    purpose: "Daftar pemberitahuan deadline, review pending, rekomendasi baru, dan event workflow lain.",
    whenToUse: "Dipakai untuk mengecek pekerjaan yang perlu segera direspons.",
  },
];

const roles = [
  ["super_admin", "Mengatur periode, master data, audit, compliance, dan seluruh workflow."],
  ["admin_unit", "Membantu administrasi unit, master data, compliance, dan monitoring."],
  ["pic_bidang", "Mengisi self-assessment sesuai bidang dan menindaklanjuti rekomendasi."],
  ["asesor", "Mereview assessment, memberi override dengan justifikasi, dan memverifikasi rekomendasi."],
  ["manajer_unit", "Membaca dashboard, NKO, trend, dan output laporan untuk keputusan manajemen."],
  ["viewer", "Membaca informasi tanpa melakukan perubahan data."],
];

const streamNotes: StreamNote[] = [
  {
    group: "KPI kuantitatif",
    unit: "%, rupiah, jam, hari, indeks, atau skor",
    calculation: "Nilai dihitung dari realisasi dibanding target dengan polaritas positif, negatif, atau range-based.",
    example: "EAF makin tinggi makin baik; EFOR dan keterlambatan laporan makin rendah makin baik.",
  },
  {
    group: "Maturity Level",
    unit: "Level 1 sampai 5 atau skor sub-area",
    calculation: "Nilai berasal dari rubrik bertingkat per sub-area, lalu diagregasi ke area, stream, dan indikator.",
    example: "Outage, SMAP, Reliability, Efficiency, WPC, Operation, Energi Primer, LCCM, SCM, HCR, dan OCR.",
  },
  {
    group: "Sub-indikator berbobot",
    unit: "% realisasi atau skor komponen",
    calculation: "Beberapa indikator terdiri dari sub-komponen dengan bobot khusus sebelum masuk NKO.",
    example: "Biaya/Fisik Pemeliharaan 70/30, HCR area, OCR OWM 55/45, dan Pilar IV investasi.",
  },
  {
    group: "Compliance pengurang",
    unit: "Poin pengurang NKO",
    calculation: "Nilai dikurangi dari total NKO dan dapat memiliki cap agar tidak melewati batas pengurang.",
    example: "Laporan rutin terlambat 2 hari dengan pengurang 0,039 per hari menghasilkan -0,078.",
  },
];

const workflow = [
  "Super Admin membuat periode dan membuka tahap assessment.",
  "Sistem membuat assessment session berdasarkan indikator, bidang, dan blueprint Konkin 2026.",
  "PIC mengisi KPI atau maturity level sesuai jenis stream dan satuannya.",
  "Asesor mereview, approve, override, atau mengembalikan submission untuk revisi.",
  "Rekomendasi dibuat untuk gap yang perlu tindakan lanjutan.",
  "Compliance dicatat sebagai komponen pengurang NKO.",
  "Dashboard menghitung NKO dan menampilkan pilar, trend, heatmap, serta drill-down.",
  "Laporan/export dipakai untuk arsip dan komunikasi resmi.",
];

const panelStyle = {
  padding: "1rem",
} as const;

const sectionTitleStyle = {
  margin: "0 0 0.35rem",
  color: "var(--sk-text-hi)",
  fontSize: "1rem",
} as const;

export default function MenuGuide() {
  return (
    <main
      style={{
        padding: "1.25rem",
        display: "grid",
        gap: "1rem",
        maxWidth: "1280px",
        width: "100%",
        margin: "0 auto",
      }}
    >
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "1rem",
          alignItems: "stretch",
        }}
      >
        <SkPanel title="Panduan Operasi PULSE" style={panelStyle}>
          <p style={{ margin: "0 0 1rem", color: "var(--sk-text-med)", lineHeight: 1.65 }}>
            Halaman ini merangkum fungsi menu, role, alur kerja, dan cara membaca jenis stream
            Konkin. Data pada fase dev masih dapat berisi dummy, tetapi struktur rumus, satuan,
            bobot, dan agregasinya mengikuti blueprint yang sudah dipetakan.
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <SkBadge tone="info">Konkin 2026</SkBadge>
            <SkBadge tone="success">NKO Real-Time</SkBadge>
            <SkBadge tone="warning">Stream Berbeda Rumus</SkBadge>
            <SkBadge tone="neutral">Data Dummy Dev</SkBadge>
          </div>
        </SkPanel>

        <SkPanel title="Urutan Cepat" style={panelStyle}>
          <ol style={{ margin: 0, paddingLeft: "1.25rem", color: "var(--sk-text-med)", lineHeight: 1.7 }}>
            <li>Periode</li>
            <li>Assessment</li>
            <li>Review Asesor</li>
            <li>Rekomendasi</li>
            <li>Compliance</li>
            <li>Dasbor dan Laporan</li>
          </ol>
        </SkPanel>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "1rem",
        }}
      >
        {menus.map((menu) => (
          <SkPanel key={menu.name} title={menu.name} style={{ ...panelStyle, display: "grid", gap: "0.75rem" }}>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <SkBadge tone="info">{menu.roles}</SkBadge>
              <SkBadge tone="neutral">{menu.route}</SkBadge>
            </div>
            <div>
              <h3 style={sectionTitleStyle}>Fungsi</h3>
              <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.6 }}>{menu.purpose}</p>
            </div>
            <div>
              <h3 style={sectionTitleStyle}>Kapan Dibuka</h3>
              <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.6 }}>{menu.whenToUse}</p>
            </div>
            <Link to={menu.route} style={{ textDecoration: "none", marginTop: "auto" }}>
              <SkButton variant="secondary" type="button">
                Buka {menu.name}
              </SkButton>
            </Link>
          </SkPanel>
        ))}
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "1rem",
        }}
      >
        <SkPanel title="Role dan Tanggung Jawab" style={panelStyle}>
          <div style={{ display: "grid", gap: "0.75rem" }}>
            {roles.map(([role, description]) => (
              <div key={role} style={{ display: "grid", gap: "0.25rem" }}>
                <SkBadge tone="info">{role}</SkBadge>
                <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.55 }}>{description}</p>
              </div>
            ))}
          </div>
        </SkPanel>

        <SkPanel title="Alur End-to-End Konkin" style={panelStyle}>
          <ol style={{ margin: 0, paddingLeft: "1.25rem", color: "var(--sk-text-med)", lineHeight: 1.7 }}>
            {workflow.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </SkPanel>
      </section>

      <SkPanel title="Mengapa Tiap Stream Berbeda" style={panelStyle}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "1rem",
          }}
        >
          {streamNotes.map((note) => (
            <div
              key={note.group}
              style={{
                display: "grid",
                gap: "0.55rem",
                padding: "0.85rem",
                border: "1px solid var(--sk-bevel-dark)",
                borderRadius: "8px",
                background: "var(--sk-surface-1)",
              }}
            >
              <SkBadge tone="warning">{note.group}</SkBadge>
              <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.55 }}>
                <strong>Satuan:</strong> {note.unit}
              </p>
              <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.55 }}>
                <strong>Perhitungan:</strong> {note.calculation}
              </p>
              <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.55 }}>
                <strong>Contoh:</strong> {note.example}
              </p>
            </div>
          ))}
        </div>
      </SkPanel>

      <SkPanel title="Catatan Data Dummy" style={panelStyle}>
        <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.65 }}>
          Pada fase pengembangan, beberapa angka dashboard, trend, dan contoh periode masih dapat
          memakai data dummy agar UI dan alur kerja bisa diuji. Yang harus dijaga tetap benar adalah
          struktur master data, jenis stream, satuan, bobot, polaritas, lifecycle review, audit log,
          dan jalur perhitungan NKO.
        </p>
      </SkPanel>
    </main>
  );
}
