import "./ComplianceTracker.css";

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { SkBadge, SkButton, SkInput, SkLed, SkPanel, SkSelect } from "@/components/skeuomorphic";
import {
  asNumber,
  useComplianceComponents,
  useComplianceDefinitions,
  useComplianceSubmissions,
  useComplianceSummary,
  useUpsertComplianceComponent,
  useUpsertComplianceSubmission,
} from "@/lib/compliance-api";
import { usePeriodeList } from "@/lib/phase2-api";

const monthNames = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

function formatNumber(value: string | number | null | undefined, digits = 4) {
  return asNumber(value).toLocaleString("id-ID", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function isoDate(year: number, month: number, day: number) {
  const safeDay = Math.max(1, Math.min(28, day));
  return `${year}-${String(month).padStart(2, "0")}-${String(safeDay).padStart(2, "0")}`;
}

export default function ComplianceTracker() {
  const periodeQuery = usePeriodeList();
  const activePeriode = periodeQuery.data?.data[0];
  const definitions = useComplianceDefinitions();
  const components = useComplianceComponents();
  const submissions = useComplianceSubmissions(activePeriode?.id);
  const summary = useComplianceSummary(activePeriode?.id);
  const upsertSubmission = useUpsertComplianceSubmission();
  const upsertComponent = useUpsertComplianceComponent();
  const firstDefinition = definitions.data?.data[0];
  const firstComponent = components.data?.data[0];
  const [reportForm, setReportForm] = useState({
    definisiId: "",
    bulan: 5,
    tanggalJatuhTempo: "2026-05-10",
    tanggalSubmit: "2026-05-12",
    isValid: "true",
    catatan: "Dummy Phase 4: telat 2 hari",
  });
  const [componentForm, setComponentForm] = useState({
    komponenId: "",
    nilai: "1",
    pengurang: "0.0000",
    catatan: "Dummy Phase 4",
  });
  const [status, setStatus] = useState("");

  const selectedDefinitionId = reportForm.definisiId || firstDefinition?.id || "";
  const selectedComponentId = componentForm.komponenId || firstComponent?.id || "";
  const selectedDefinition = definitions.data?.data.find((item) => item.id === selectedDefinitionId);

  const monthDueDate = useMemo(() => {
    if (!activePeriode || !selectedDefinition) return reportForm.tanggalJatuhTempo;
    return isoDate(activePeriode.tahun, reportForm.bulan, selectedDefinition.default_due_day);
  }, [activePeriode, reportForm.bulan, reportForm.tanggalJatuhTempo, selectedDefinition]);

  const handleSaveReport = async () => {
    if (!activePeriode || !selectedDefinitionId) return;
    setStatus("Menyimpan laporan compliance...");
    await upsertSubmission.mutateAsync({
      periode_id: activePeriode.id,
      definisi_id: selectedDefinitionId,
      bulan: reportForm.bulan,
      tanggal_jatuh_tempo: reportForm.tanggalJatuhTempo || monthDueDate,
      tanggal_submit: reportForm.tanggalSubmit || null,
      is_valid: reportForm.isValid === "true",
      catatan: reportForm.catatan || null,
    });
    setStatus("Laporan tersimpan, NKO sudah direcompute.");
  };

  const handleSaveComponent = async () => {
    if (!activePeriode || !selectedComponentId) return;
    setStatus("Menyimpan komponen compliance...");
    await upsertComponent.mutateAsync({
      periode_id: activePeriode.id,
      komponen_id: selectedComponentId,
      nilai: asNumber(componentForm.nilai, 0),
      pengurang: asNumber(componentForm.pengurang, 0),
      payload: { source: "frontend_dummy" },
      catatan: componentForm.catatan || null,
    });
    setStatus("Komponen tersimpan, NKO sudah direcompute.");
  };

  const rows = summary.data?.rows ?? [];
  const submissionRows = submissions.data?.data ?? [];

  return (
    <main className="compliance-page">
      <section className="compliance-hero">
        <div className="compliance-hero-copy">
          <div className="compliance-kicker">
            <SkLed state="on" label="compliance live" />
            <span>Phase 4 Compliance Tracker</span>
          </div>
          <h1>Compliance Control Desk</h1>
          <p>
            Tracker ini memakai blueprint Phase 4: 9 laporan rutin punya faktor pengurang keterlambatan sendiri,
            komponen PACA/ICOFR/NAC/Critical Event dicatat terpisah, dan total pengurang langsung masuk ke snapshot NKO.
          </p>
          <div>
            <Link to="/dashboard/executive">
              <SkButton variant="secondary">Buka Dashboard NKO</SkButton>
            </Link>
          </div>
        </div>

        <SkPanel className="compliance-period-panel" title="PERIODE AKTIF">
          <span>{activePeriode ? `${activePeriode.tahun} TW${activePeriode.triwulan}` : "Belum ada periode"}</span>
          <strong>{activePeriode?.nama ?? "Tidak tersedia"}</strong>
          <small>Status: {activePeriode?.status ?? "-"}</small>
        </SkPanel>
      </section>

      <section className="compliance-metrics" aria-label="Compliance summary">
        <SkPanel className="compliance-metric">
          <span>Total Pengurang</span>
          <strong>-{formatNumber(summary.data?.total_pengurang)}</strong>
          <small>Cap {formatNumber(summary.data?.cap)}</small>
        </SkPanel>
        <SkPanel className="compliance-metric">
          <span>Laporan Telat</span>
          <strong>{summary.data?.late_report_count ?? 0}</strong>
          <small>{summary.data?.report_count ?? 0} laporan tercatat</small>
        </SkPanel>
        <SkPanel className="compliance-metric">
          <span>Laporan Invalid</span>
          <strong>{summary.data?.invalid_report_count ?? 0}</strong>
          <small>Faktor invaliditas aktif</small>
        </SkPanel>
        <SkPanel className="compliance-metric">
          <span>Pengurang Laporan</span>
          <strong>-{formatNumber(summary.data?.laporan_pengurang)}</strong>
          <small>0.039 per hari/default</small>
        </SkPanel>
        <SkPanel className="compliance-metric">
          <span>Pengurang Komponen</span>
          <strong>-{formatNumber(summary.data?.komponen_pengurang)}</strong>
          <small>{summary.data?.component_count ?? 0} komponen</small>
        </SkPanel>
      </section>

      <section className="compliance-workbench">
        <SkPanel title="Input Laporan Rutin">
          <div className="compliance-form">
            <div className="compliance-field-grid">
              <div className="compliance-field">
                <label>Laporan</label>
                <SkSelect
                  value={selectedDefinitionId}
                  onChange={(event) => setReportForm((current) => ({ ...current, definisiId: event.currentTarget.value }))}
                  label="Pilih laporan rutin"
                >
                  {(definitions.data?.data ?? []).map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.kode} - {item.nama}
                    </option>
                  ))}
                </SkSelect>
              </div>
              <div className="compliance-field">
                <label>Bulan</label>
                <SkSelect
                  value={reportForm.bulan}
                  onChange={(event) => {
                    const bulan = Number(event.currentTarget.value);
                    setReportForm((current) => ({ ...current, bulan }));
                  }}
                  label="Bulan laporan"
                >
                  {monthNames.map((month, index) => (
                    <option key={month} value={index + 1}>
                      {month}
                    </option>
                  ))}
                </SkSelect>
              </div>
              <div className="compliance-field">
                <label>Jatuh Tempo</label>
                <SkInput
                  type="date"
                  value={reportForm.tanggalJatuhTempo || monthDueDate}
                  label="Tanggal jatuh tempo"
                  onChange={(event) => setReportForm((current) => ({ ...current, tanggalJatuhTempo: event.currentTarget.value }))}
                />
              </div>
              <div className="compliance-field">
                <label>Tanggal Submit</label>
                <SkInput
                  type="date"
                  value={reportForm.tanggalSubmit}
                  label="Tanggal submit"
                  onChange={(event) => setReportForm((current) => ({ ...current, tanggalSubmit: event.currentTarget.value }))}
                />
              </div>
              <div className="compliance-field">
                <label>Validitas</label>
                <SkSelect
                  value={reportForm.isValid}
                  label="Validitas laporan"
                  onChange={(event) => setReportForm((current) => ({ ...current, isValid: event.currentTarget.value }))}
                >
                  <option value="true">Valid</option>
                  <option value="false">Invalid</option>
                </SkSelect>
              </div>
              <div className="compliance-field">
                <label>Catatan</label>
                <SkInput
                  value={reportForm.catatan}
                  label="Catatan laporan"
                  onChange={(event) => setReportForm((current) => ({ ...current, catatan: event.currentTarget.value }))}
                />
              </div>
            </div>
            <p className="compliance-help">
              Contoh dummy: Pengusahaan Mei submit 12 Mei dengan jatuh tempo 10 Mei menghasilkan pengurang 2 x 0.039 = 0.0780.
            </p>
            <SkButton onClick={handleSaveReport} disabled={!activePeriode || upsertSubmission.isPending}>
              Simpan Laporan
            </SkButton>
          </div>
        </SkPanel>

        <SkPanel title="Input Komponen Compliance">
          <div className="compliance-form">
            <div className="compliance-field-grid">
              <div className="compliance-field">
                <label>Komponen</label>
                <SkSelect
                  value={selectedComponentId}
                  label="Pilih komponen compliance"
                  onChange={(event) => setComponentForm((current) => ({ ...current, komponenId: event.currentTarget.value }))}
                >
                  {(components.data?.data ?? []).map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.kode} - {item.nama}
                    </option>
                  ))}
                </SkSelect>
              </div>
              <div className="compliance-field">
                <label>Nilai</label>
                <SkInput
                  type="number"
                  step="0.0001"
                  value={componentForm.nilai}
                  label="Nilai komponen"
                  onChange={(event) => setComponentForm((current) => ({ ...current, nilai: event.currentTarget.value }))}
                />
              </div>
              <div className="compliance-field">
                <label>Pengurang</label>
                <SkInput
                  type="number"
                  min="0"
                  step="0.0001"
                  value={componentForm.pengurang}
                  label="Pengurang komponen"
                  onChange={(event) => setComponentForm((current) => ({ ...current, pengurang: event.currentTarget.value }))}
                />
              </div>
              <div className="compliance-field">
                <label>Catatan</label>
                <SkInput
                  value={componentForm.catatan}
                  label="Catatan komponen"
                  onChange={(event) => setComponentForm((current) => ({ ...current, catatan: event.currentTarget.value }))}
                />
              </div>
            </div>
            <p className="compliance-help">
              Komponen non-laporan disimpan per periode dan cap mengikuti konfigurasi komponen backend.
            </p>
            <SkButton onClick={handleSaveComponent} disabled={!activePeriode || upsertComponent.isPending}>
              Simpan Komponen
            </SkButton>
          </div>
        </SkPanel>
      </section>

      <div className="compliance-status">{status || (summary.isFetching ? "Memuat compliance summary..." : "")}</div>

      <section className="compliance-tables">
        <SkPanel title="Detail Pengurang">
          <div className="compliance-table-wrap">
            <table className="compliance-table">
              <thead>
                <tr>
                  <th>Jenis</th>
                  <th>Kode</th>
                  <th>Periode</th>
                  <th>Status</th>
                  <th>Pengurang</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={`${row.type}-${row.kode}-${index}`}>
                    <td><SkBadge tone={row.type === "laporan" ? "info" : "warning"}>{row.type}</SkBadge></td>
                    <td><strong>{row.kode}</strong><br />{row.nama}</td>
                    <td>{row.bulan ? monthNames[row.bulan - 1] : "-"}</td>
                    <td>
                      {row.type === "laporan"
                        ? `${row.keterlambatan_hari ?? 0} hari, ${row.is_valid ? "valid" : "invalid"}`
                        : `nilai ${formatNumber(row.nilai, 2)}`}
                    </td>
                    <td className="compliance-amount">-{formatNumber(row.pengurang)}</td>
                  </tr>
                ))}
                {!rows.length && (
                  <tr>
                    <td colSpan={5}>Belum ada record compliance untuk periode ini.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </SkPanel>

        <SkPanel title="Laporan Tersimpan">
          <div className="compliance-table-wrap">
            <table className="compliance-table">
              <thead>
                <tr>
                  <th>Bulan</th>
                  <th>Definisi</th>
                  <th>Jatuh Tempo</th>
                  <th>Submit</th>
                  <th>Telat</th>
                </tr>
              </thead>
              <tbody>
                {submissionRows.map((row) => {
                  const def = definitions.data?.data.find((item) => item.id === row.definisi_id);
                  return (
                    <tr key={row.id}>
                      <td>{monthNames[row.bulan - 1]}</td>
                      <td><strong>{def?.kode ?? row.definisi_id.slice(0, 8)}</strong><br />{def?.nama ?? "-"}</td>
                      <td>{row.tanggal_jatuh_tempo}</td>
                      <td>{row.tanggal_submit ?? "-"}</td>
                      <td>{row.keterlambatan_hari} hari</td>
                    </tr>
                  );
                })}
                {!submissionRows.length && (
                  <tr>
                    <td colSpan={5}>Belum ada laporan tersimpan.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </SkPanel>
      </section>
    </main>
  );
}
