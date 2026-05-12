import { Link } from "react-router-dom";
import { SkBadge, SkButton, SkPanel } from "@/components/skeuomorphic";

type Step = {
  no: string;
  title: string;
  owner: string;
  route: string;
  input: string;
  action: string;
  output: string;
  checks: string[];
};

type StatusGroup = {
  name: string;
  tone: "neutral" | "info" | "success" | "warning" | "danger";
  statuses: string[];
  explanation: string;
};

const steps: Step[] = [
  {
    no: "01",
    title: "Setup periode",
    owner: "super_admin",
    route: "/periode",
    input: "Tahun, semester/triwulan, tanggal mulai, dan deadline.",
    action: "Buat periode lalu transisikan sesuai fase kerja.",
    output: "Periode aktif dan assessment session siap dibuat.",
    checks: ["Nama periode benar", "Status tidak loncat tahap", "Tanggal deadline masuk akal"],
  },
  {
    no: "02",
    title: "Generate session",
    owner: "super_admin",
    route: "/periode",
    input: "Template Konkin 2026, bidang, indikator, dan mapping applicability.",
    action: "Pastikan session tersedia untuk PIC/bidang yang relevan.",
    output: "Daftar assessment session muncul di menu Assessment.",
    checks: ["Jumlah session wajar", "Bidang PIC sesuai", "Stream baru ikut muncul"],
  },
  {
    no: "03",
    title: "Self-assessment PIC",
    owner: "pic_bidang",
    route: "/assessment",
    input: "Realisasi KPI, level maturity, catatan, dan link eviden bila ada.",
    action: "Isi form sesuai jenis stream, simpan, lalu submit.",
    output: "Submission berstatus submitted dan menunggu asesor.",
    checks: ["Satuan tidak tertukar", "Polaritas benar", "Catatan menjelaskan gap"],
  },
  {
    no: "04",
    title: "Review asesor",
    owner: "asesor",
    route: "/assessment",
    input: "Submission PIC, target, realisasi, rubrik, dan catatan.",
    action: "Approve, override dengan justifikasi, atau request revision.",
    output: "Nilai final tersimpan dan NKO dapat dihitung ulang.",
    checks: ["Override punya alasan", "Nilai final wajar", "Gap dibuat rekomendasi"],
  },
  {
    no: "05",
    title: "Tindak lanjut rekomendasi",
    owner: "pic_bidang + asesor",
    route: "/recommendations",
    input: "Action item, PIC owner, target outcome, deadline, dan progress.",
    action: "PIC update progress; asesor verify-close saat selesai.",
    output: "Rekomendasi closed atau carried over ke periode berikutnya.",
    checks: ["Owner jelas", "Progress terukur", "Closed punya bukti/catatan"],
  },
  {
    no: "06",
    title: "Compliance pengurang",
    owner: "admin_unit",
    route: "/compliance",
    input: "Status laporan rutin, keterlambatan, dan komponen compliance lain.",
    action: "Catat realisasi compliance agar pengurang masuk ke NKO.",
    output: "Deduction tampil di dashboard dan summary compliance.",
    checks: ["Tanggal laporan benar", "Faktor pengurang sesuai", "Cap pengurang diperhatikan"],
  },
  {
    no: "07",
    title: "Dashboard dan laporan",
    owner: "manajer_unit",
    route: "/dashboard",
    input: "Nilai final, compliance, rekomendasi, dan snapshot periode.",
    action: "Pantau NKO, drilldown pilar/stream, lalu export laporan.",
    output: "Bahan rapat/manajemen dan arsip laporan resmi.",
    checks: ["NKO gross vs final jelas", "Stream merah ditindaklanjuti", "Export berhasil"],
  },
];

const statusGroups: StatusGroup[] = [
  {
    name: "Periode",
    tone: "info",
    statuses: ["draft", "aktif", "self_assessment", "asesmen", "finalisasi", "closed"],
    explanation: "Mengatur fase besar pekerjaan. Jangan close sebelum rekomendasi dan compliance dicek.",
  },
  {
    name: "Assessment",
    tone: "warning",
    statuses: ["draft", "submitted", "approved", "returned", "overridden"],
    explanation: "Menunjukkan posisi form PIC dan keputusan asesor terhadap nilai final.",
  },
  {
    name: "Rekomendasi",
    tone: "success",
    statuses: ["open", "in_progress", "pending_review", "closed", "carried_over"],
    explanation: "Mengawal tindak lanjut gap sampai selesai atau dibawa ke periode berikutnya.",
  },
  {
    name: "Compliance",
    tone: "danger",
    statuses: ["on_time", "late", "not_submitted", "deducted"],
    explanation: "Mempengaruhi NKO final sebagai pengurang, bukan sebagai nilai penambah pilar.",
  },
];

const handoffs = [
  ["Super Admin", "PIC", "Periode/session sudah siap, PIC mulai isi assessment."],
  ["PIC", "Asesor", "Submission dikirim, asesor menilai dan memberi keputusan."],
  ["Asesor", "PIC", "Rekomendasi dibuat, PIC mengeksekusi tindak lanjut."],
  ["Admin Unit", "Manajer Unit", "Compliance dan laporan rutin dikunci untuk pembacaan NKO final."],
  ["Semua role", "Audit", "Setiap perubahan penting tercatat agar bisa ditelusuri ulang."],
];

const dailyChecks = [
  "Cek Notifikasi untuk review pending atau rekomendasi baru.",
  "Cek Assessment yang masih draft/submitted sebelum deadline.",
  "Cek Rekomendasi open dan pending_review.",
  "Cek Compliance yang terlambat atau belum submit.",
  "Cek Dasbor untuk stream dengan kontribusi turun atau pengurang naik.",
];

const panelStyle = { padding: "1rem" } as const;

export default function WorkflowPlaybook() {
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
        }}
      >
        <SkPanel title="Playbook Alur Kerja" style={panelStyle}>
          <p style={{ margin: "0 0 1rem", color: "var(--sk-text-med)", lineHeight: 1.65 }}>
            Playbook ini menunjukkan urutan operasional PULSE dari setup periode sampai dashboard
            dan laporan. Gunakan halaman ini sebagai checklist saat mencoba data dummy atau saat
            menyiapkan operasional produksi.
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <SkBadge tone="info">Periode</SkBadge>
            <SkBadge tone="warning">Assessment</SkBadge>
            <SkBadge tone="success">Rekomendasi</SkBadge>
            <SkBadge tone="danger">Compliance</SkBadge>
          </div>
        </SkPanel>

        <SkPanel title="Checklist Harian" style={panelStyle}>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", color: "var(--sk-text-med)", lineHeight: 1.7 }}>
            {dailyChecks.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </SkPanel>
      </section>

      <section style={{ display: "grid", gap: "1rem" }}>
        {steps.map((step) => (
          <SkPanel key={step.no} title={`${step.no} - ${step.title}`} style={panelStyle}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                gap: "1rem",
                alignItems: "start",
              }}
            >
              <div style={{ display: "grid", gap: "0.5rem" }}>
                <SkBadge tone="info">{step.owner}</SkBadge>
                <SkBadge tone="neutral">{step.route}</SkBadge>
                <Link to={step.route} style={{ textDecoration: "none" }}>
                  <SkButton variant="secondary" type="button">
                    Buka Menu
                  </SkButton>
                </Link>
              </div>
              <dl
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto 1fr",
                  gap: "0.4rem 0.75rem",
                  margin: 0,
                  color: "var(--sk-text-med)",
                  lineHeight: 1.55,
                }}
              >
                <dt>Input</dt>
                <dd style={{ margin: 0 }}>{step.input}</dd>
                <dt>Aksi</dt>
                <dd style={{ margin: 0 }}>{step.action}</dd>
                <dt>Output</dt>
                <dd style={{ margin: 0 }}>{step.output}</dd>
              </dl>
              <div>
                <strong style={{ display: "block", marginBottom: "0.35rem", color: "var(--sk-text-hi)" }}>
                  Cek Sebelum Lanjut
                </strong>
                <ul style={{ margin: 0, paddingLeft: "1rem", color: "var(--sk-text-med)", lineHeight: 1.55 }}>
                  {step.checks.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
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
        {statusGroups.map((group) => (
          <SkPanel key={group.name} title={`Status ${group.name}`} style={panelStyle}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
              {group.statuses.map((status) => (
                <SkBadge key={status} tone={group.tone}>
                  {status}
                </SkBadge>
              ))}
            </div>
            <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.6 }}>{group.explanation}</p>
          </SkPanel>
        ))}
      </section>

      <SkPanel title="Handoff Antar Role" style={panelStyle}>
        <div style={{ display: "grid", gap: "0.75rem" }}>
          {handoffs.map(([from, to, note]) => (
            <div
              key={`${from}-${to}`}
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                gap: "0.75rem",
                alignItems: "center",
                color: "var(--sk-text-med)",
              }}
            >
              <SkBadge tone="info">{from}</SkBadge>
              <span aria-hidden="true">ke</span>
              <SkBadge tone="success">{to}</SkBadge>
              <span>{note}</span>
            </div>
          ))}
        </div>
      </SkPanel>

      <SkPanel title="Titik Kontrol Sebelum Finalisasi" style={panelStyle}>
        <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.65 }}>
          Sebelum periode masuk finalisasi atau closed, pastikan assessment penting sudah direview,
          rekomendasi prioritas tidak menggantung, compliance pengurang sudah masuk, dashboard NKO
          final sudah dipahami, dan export laporan berhasil dibuka. Untuk rumus dan satuan, buka
          <Link to="/formula-dictionary" style={{ color: "var(--sk-pln-blue)", marginLeft: "0.25rem" }}>
            Kamus Formula
          </Link>
          .
        </p>
      </SkPanel>
    </main>
  );
}
