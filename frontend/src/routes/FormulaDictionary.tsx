import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { SkBadge, SkButton, SkInput, SkPanel } from "@/components/skeuomorphic";
import { dashboardModel } from "@/lib/dashboard-fixtures";

type FormulaFamily = {
  name: string;
  tone: "neutral" | "info" | "success" | "warning" | "danger";
  formula: string;
  usedFor: string;
  warning: string;
};

type DictionaryRow = {
  code: string;
  name: string;
  pillar: string;
  family: string;
  unit: string;
  polarity: string;
  weight: string;
  formula: string;
  aggregation: string;
  notes: string;
};

const families: FormulaFamily[] = [
  {
    name: "Kuantitatif Positif",
    tone: "success",
    formula: "Pencapaian = realisasi / target x 100",
    usedFor: "Indikator yang makin tinggi makin baik.",
    warning: "Jangan dipakai untuk indikator berbasis penurunan risiko atau biaya.",
  },
  {
    name: "Kuantitatif Negatif",
    tone: "warning",
    formula: "Pencapaian = (2 - realisasi / target) x 100",
    usedFor: "Indikator yang makin rendah makin baik.",
    warning: "Jika realisasi turun, skor justru membaik. Ini berbeda dari EAF.",
  },
  {
    name: "Range-Based",
    tone: "info",
    formula: "Skor terbaik saat realisasi berada dekat rentang/target ideal.",
    usedFor: "Indikator yang tidak selalu makin tinggi atau makin rendah.",
    warning: "Butuh batas bawah/atas atau target ideal yang jelas di master data.",
  },
  {
    name: "Maturity Average",
    tone: "neutral",
    formula: "Rata-rata sub-area ke area ke stream.",
    usedFor: "Stream maturity level dengan rubrik level 0 sampai 4.",
    warning: "Sub-area tidak dinilai perlu dinormalisasi, bukan dihitung sebagai nol.",
  },
  {
    name: "Weighted Maturity",
    tone: "info",
    formula: "Jumlah nilai sub-area x bobot sub-area.",
    usedFor: "HCR/OCR atau stream yang punya bobot internal khusus.",
    warning: "Bobot internal berbeda dari bobot indikator terhadap pilar.",
  },
  {
    name: "Compliance Pengurang",
    tone: "danger",
    formula: "Pengurang = nilai pelanggaran x faktor, lalu diterapkan cap.",
    usedFor: "Laporan rutin terlambat dan komponen compliance lain.",
    warning: "Nilai ini mengurangi NKO final, bukan menambah kontribusi pilar.",
  },
];

const baseRows: DictionaryRow[] = dashboardModel.streams.map((stream) => ({
  code: stream.code,
  name: stream.name,
  pillar: stream.pillar,
  family:
    stream.polarity === "negatif"
      ? "Kuantitatif Negatif"
      : stream.kind === "maturity"
        ? "Maturity Average"
        : stream.kind === "compliance"
          ? "Compliance Pengurang"
          : "Kuantitatif Positif",
  unit: stream.unit,
  polarity: stream.polarity,
  weight: String(stream.weight),
  formula: stream.formula,
  aggregation: stream.kind === "maturity" ? "Sub-area ke area ke stream" : "Indikator langsung ke pilar",
  notes: stream.note,
}));

const extraRows: DictionaryRow[] = [
  {
    code: "BPP-HAR",
    name: "Biaya Pemeliharaan",
    pillar: "I",
    family: "Kuantitatif Negatif",
    unit: "Rupiah atau %",
    polarity: "negatif",
    weight: "70/30 bersama fisik",
    formula: "Realisasi biaya dibanding target biaya dengan arah negatif.",
    aggregation: "Komponen biaya dan fisik dinormalisasi sebelum masuk indikator BPP.",
    notes: "Biaya lebih rendah dari target meningkatkan skor, selama fisik tetap terkendali.",
  },
  {
    code: "SDGS-KP",
    name: "Kepuasan Pelanggan",
    pillar: "I",
    family: "Range-Based",
    unit: "Indeks",
    polarity: "range",
    weight: "Sub-komponen SDGs",
    formula: "Skor mengikuti kedekatan terhadap target ideal/rentang yang ditetapkan.",
    aggregation: "Tujuh sub-komponen SDGs dirata-rata atau dibobot sesuai master.",
    notes: "Tidak otomatis sama dengan indikator positif; rentang ideal harus dibaca dari blueprint.",
  },
  {
    code: "RELIABILITY",
    name: "Reliability Management",
    pillar: "II",
    family: "Maturity Average",
    unit: "Level 0-4",
    polarity: "rubric",
    weight: "Pilar II",
    formula: "Rata-rata rubrik reliability improvement dan defect elimination.",
    aggregation: "Sub-area ke area ke stream, lalu ke Pilar II.",
    notes: "Bandingkan antar periode di dalam konteks Reliability, bukan langsung dengan KPI persen.",
  },
  {
    code: "EFFICIENCY",
    name: "Efficiency Management",
    pillar: "II",
    family: "Maturity Average",
    unit: "Level 0-4",
    polarity: "rubric",
    weight: "Pilar II",
    formula: "Rata-rata maturity heat-rate monitoring dan losses reduction.",
    aggregation: "Sub-area ke area ke stream, lalu ke Pilar II.",
    notes: "Nilai 3,2 berarti maturity proses, bukan 3,2 persen.",
  },
  {
    code: "WPC",
    name: "Work Planning Control",
    pillar: "II",
    family: "Maturity Average",
    unit: "Level 0-4",
    polarity: "rubric",
    weight: "Pilar II",
    formula: "Rata-rata work identification, prioritization, dan integrated schedule.",
    aggregation: "Sub-area ke area ke stream, lalu ke Pilar II.",
    notes: "Perlu catatan asesmen untuk menjelaskan gap antar sub-area.",
  },
  {
    code: "HCR",
    name: "Human Capital Readiness",
    pillar: "V",
    family: "Weighted Maturity",
    unit: "Level 0-4",
    polarity: "rubric",
    weight: "Pilar V",
    formula: "Rata-rata atau bobot area workforce, talent, performance, reward, IR, dan HC operations.",
    aggregation: "Area HCR ke Pilar V.",
    notes: "HCR dibaca sebagai kesiapan organisasi, bukan KPI operasional harian.",
  },
  {
    code: "OCR",
    name: "Organization Capital Readiness",
    pillar: "V",
    family: "Weighted Maturity",
    unit: "Level 0-4",
    polarity: "rubric",
    weight: "OWM 55/45 pada sub-area khusus",
    formula: "Weighted average saat metadata bobot tersedia, fallback ke maturity average.",
    aggregation: "Sub-area OCR ke area OCR ke Pilar V.",
    notes: "OWM punya bobot khusus sehingga tidak boleh dirata-rata polos jika metadata bobot ada.",
  },
  {
    code: "LAP-RUTIN",
    name: "Laporan Rutin Compliance",
    pillar: "VI",
    family: "Compliance Pengurang",
    unit: "Poin NKO",
    polarity: "pengurang",
    weight: "Cap pengurang",
    formula: "Hari terlambat x faktor pengurang per laporan.",
    aggregation: "Total pengurang compliance dikurangkan dari gross Pilar I-V.",
    notes: "Contoh lokal: 2 hari x 0,039 menghasilkan -0,078.",
  },
];

const rows = [...baseRows, ...extraRows];

function toneForFamily(family: string): FormulaFamily["tone"] {
  return families.find((item) => item.name === family)?.tone ?? "neutral";
}

const panelStyle = { padding: "1rem" } as const;

export default function FormulaDictionary() {
  const [query, setQuery] = useState("");
  const [family, setFamily] = useState("Semua");

  const filteredRows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return rows.filter((row) => {
      const familyMatch = family === "Semua" || row.family === family;
      const textMatch =
        !needle ||
        [row.code, row.name, row.pillar, row.family, row.unit, row.polarity, row.formula, row.notes]
          .join(" ")
          .toLowerCase()
          .includes(needle);
      return familyMatch && textMatch;
    });
  }, [family, query]);

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
        <SkPanel title="Kamus Formula & Stream" style={panelStyle}>
          <p style={{ margin: "0 0 1rem", color: "var(--sk-text-med)", lineHeight: 1.65 }}>
            Referensi ini membantu membaca perbedaan rumus, satuan, polaritas, bobot, dan
            agregasi antar stream. Halaman ini bersifat panduan operator; kalkulasi resmi tetap
            berasal dari NKO engine dan master data.
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <SkBadge tone="success">KPI Positif</SkBadge>
            <SkBadge tone="warning">KPI Negatif</SkBadge>
            <SkBadge tone="info">Range</SkBadge>
            <SkBadge tone="neutral">Maturity</SkBadge>
            <SkBadge tone="danger">Pengurang</SkBadge>
          </div>
        </SkPanel>

        <SkPanel title="Cara Membaca" style={panelStyle}>
          <ol style={{ margin: 0, paddingLeft: "1.25rem", color: "var(--sk-text-med)", lineHeight: 1.7 }}>
            <li>Cek family formula terlebih dahulu.</li>
            <li>Cek satuan, karena persen berbeda dari level maturity.</li>
            <li>Cek polaritas: positif, negatif, range, rubric, atau pengurang.</li>
            <li>Cek bobot indikator dan bobot internal bila ada.</li>
            <li>Baca catatan sebelum membandingkan antar stream.</li>
          </ol>
        </SkPanel>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "1rem",
        }}
      >
        {families.map((item) => (
          <SkPanel key={item.name} title={item.name} style={panelStyle}>
            <div style={{ display: "grid", gap: "0.55rem" }}>
              <SkBadge tone={item.tone}>{item.name}</SkBadge>
              <p style={{ margin: 0, color: "var(--sk-text-hi)", lineHeight: 1.55 }}>{item.formula}</p>
              <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.55 }}>{item.usedFor}</p>
              <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.55 }}>
                <strong>Catatan:</strong> {item.warning}
              </p>
            </div>
          </SkPanel>
        ))}
      </section>

      <SkPanel title="Filter Referensi" style={panelStyle}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(220px, 1fr) minmax(220px, 320px)",
            gap: "0.75rem",
          }}
        >
          <SkInput
            label="Cari stream atau formula"
            placeholder="Cari EAF, HCR, negatif, level, compliance..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <select
            aria-label="Filter family formula"
            value={family}
            onChange={(event) => setFamily(event.target.value)}
            style={{
              background: "var(--sk-surface-2)",
              color: "var(--sk-text-hi)",
              border: "1px solid rgba(96, 112, 134, 0.28)",
              borderRadius: 6,
              padding: "0.5rem 0.75rem",
              fontFamily: "var(--sk-font-mono)",
              boxShadow:
                "inset 0 2px 5px rgba(74, 92, 112, 0.12), inset 0 -1px 0 rgba(255,255,255,0.75)",
            }}
          >
            <option>Semua</option>
            {families.map((item) => (
              <option key={item.name}>{item.name}</option>
            ))}
          </select>
        </div>
      </SkPanel>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "1rem",
        }}
      >
        {filteredRows.map((row) => (
          <SkPanel key={`${row.code}-${row.family}`} title={`${row.code} - ${row.name}`} style={panelStyle}>
            <div style={{ display: "grid", gap: "0.65rem" }}>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                <SkBadge tone={toneForFamily(row.family)}>{row.family}</SkBadge>
                <SkBadge tone="neutral">Pilar {row.pillar}</SkBadge>
                <SkBadge tone="info">{row.unit}</SkBadge>
              </div>
              <dl
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto 1fr",
                  gap: "0.35rem 0.75rem",
                  margin: 0,
                  color: "var(--sk-text-med)",
                  lineHeight: 1.5,
                }}
              >
                <dt>Polaritas</dt>
                <dd style={{ margin: 0 }}>{row.polarity}</dd>
                <dt>Bobot</dt>
                <dd style={{ margin: 0 }}>{row.weight}</dd>
                <dt>Formula</dt>
                <dd style={{ margin: 0 }}>{row.formula}</dd>
                <dt>Agregasi</dt>
                <dd style={{ margin: 0 }}>{row.aggregation}</dd>
              </dl>
              <p style={{ margin: 0, color: "var(--sk-text-med)", lineHeight: 1.6 }}>{row.notes}</p>
            </div>
          </SkPanel>
        ))}
      </section>

      {filteredRows.length === 0 && (
        <SkPanel title="Tidak Ada Hasil" style={panelStyle}>
          <p style={{ margin: 0, color: "var(--sk-text-med)" }}>
            Tidak ada stream yang cocok dengan filter saat ini.
          </p>
        </SkPanel>
      )}

      <SkPanel title="Hubungan dengan Master Data" style={panelStyle}>
        <p style={{ margin: "0 0 0.75rem", color: "var(--sk-text-med)", lineHeight: 1.65 }}>
          Untuk melihat struktur rubrik lengkap per stream, buka Master Data stream ML. Kamus ini
          membantu membaca konsepnya, sedangkan detail area dan sub-area tetap berada di master
          `ml_stream.structure`.
        </p>
        <Link to="/master/stream-ml" style={{ textDecoration: "none" }}>
          <SkButton variant="secondary" type="button">
            Buka Master Stream ML
          </SkButton>
        </Link>
      </SkPanel>
    </main>
  );
}
