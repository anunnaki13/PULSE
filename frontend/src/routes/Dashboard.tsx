import "./Dashboard.css";

import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuthStore } from "@/lib/auth-store";
import { SkBadge, SkButton, SkLed, SkPanel, SkSlider, SkToggle } from "@/components/skeuomorphic";
import { dashboardInput, dashboardModel } from "@/lib/dashboard-fixtures";
import { computeDashboard, type StreamKind } from "@/lib/dashboard-calculations";
import { dashboardResponseToModel, useDashboardExecutive } from "@/lib/dashboard-api";
import { usePeriodeList } from "@/lib/phase2-api";

type ComponentPoint = {
  label: string;
  value: string;
  state: "baik" | "waspada" | "kritis";
};

type BidangScore = {
  bidang: string;
  value: number;
};

const baseStreams = dashboardModel.streams;

const trend = [
  { quarter: "TW1", nko: 99.62 },
  { quarter: "TW2", nko: 101.44 },
  { quarter: "TW3", nko: 102.71 },
  { quarter: "TW4", nko: 103.36 },
  { quarter: "FCT", nko: 104.18 },
];

const heatmap = [
  { stream: "OUTAGE", values: [2.6, 3.0, 3.2, 3.42] },
  { stream: "SMAP", values: [2.9, 3.0, 3.05, 3.1] },
  { stream: "Reliability", values: [3.1, 3.12, 3.18, 3.24] },
  { stream: "Efficiency", values: [2.7, 2.95, 3.06, 3.2] },
  { stream: "WPC", values: [2.4, 2.55, 2.8, 3.04] },
  { stream: "Operation", values: [3.3, 3.26, 3.38, 3.46] },
];

const attention = [
  "SMAP belum mencapai target level 3.5; perlu review evidence WBS dan program preventif.",
  "Pilar IV turun 0.31 karena dummy PRK execution berada di bawah target semester.",
  "WPC masih level 3.04; masuk kandidat prioritas rekomendasi Phase 4.",
];

const componentPoints: Record<string, ComponentPoint[]> = {
  EAF: [
    { label: "Available Hours", value: "7.428 jam", state: "baik" },
    { label: "Equivalent Derated Hours", value: "184 jam", state: "waspada" },
    { label: "Planned Outage Hours", value: "336 jam", state: "baik" },
    { label: "Service Hours Basis", value: "8.760 jam", state: "baik" },
  ],
  EFOR: [
    { label: "Forced Outage Hours", value: "112 jam", state: "baik" },
    { label: "Equivalent Forced Derating", value: "38 jam", state: "baik" },
    { label: "Service Hours", value: "4.052 jam", state: "baik" },
    { label: "Target Rate", value: "4,20%", state: "baik" },
  ],
  OUTAGE: [
    { label: "P3 Planning", value: "3,62", state: "baik" },
    { label: "Pre-Outage Readiness", value: "3,31", state: "waspada" },
    { label: "Execution Control", value: "3,44", state: "baik" },
    { label: "Post-Outage Review", value: "3,21", state: "waspada" },
  ],
  SMAP: [
    { label: "Buku Manual Utama", value: "3,35", state: "baik" },
    { label: "Program Preventif", value: "3,04", state: "waspada" },
    { label: "Whistleblowing System", value: "2,82", state: "kritis" },
    { label: "Monitoring Gratifikasi", value: "3,18", state: "waspada" },
  ],
};

const bidangScores: Record<string, BidangScore[]> = {
  EAF: [
    { bidang: "OM-1", value: 104.2 },
    { bidang: "OM-2", value: 102.8 },
    { bidang: "OM-3", value: 105.4 },
    { bidang: "OM-4", value: 101.9 },
    { bidang: "OM-5", value: 103.6 },
    { bidang: "OM-RE", value: 106.1 },
  ],
  EFOR: [
    { bidang: "OM-1", value: 112.4 },
    { bidang: "OM-2", value: 108.8 },
    { bidang: "OM-3", value: 113.1 },
    { bidang: "OM-4", value: 110.5 },
    { bidang: "OM-5", value: 109.2 },
    { bidang: "OM-RE", value: 114.0 },
  ],
  OUTAGE: [
    { bidang: "OM-1", value: 3.44 },
    { bidang: "OM-2", value: 3.28 },
    { bidang: "OM-3", value: 3.57 },
    { bidang: "OM-4", value: 3.31 },
    { bidang: "OM-5", value: 3.39 },
    { bidang: "OM-RE", value: 3.54 },
  ],
  SMAP: [
    { bidang: "CPF", value: 3.18 },
    { bidang: "HSE", value: 3.07 },
    { bidang: "RISK", value: 3.14 },
    { bidang: "AUD", value: 3.28 },
    { bidang: "FIN", value: 2.94 },
    { bidang: "LOG", value: 3.01 },
  ],
};

const pipeline = [
  { label: "Open", value: 9, tone: "warning" as const },
  { label: "In Progress", value: 14, tone: "info" as const },
  { label: "Pending Review", value: 4, tone: "neutral" as const },
  { label: "Closed", value: 31, tone: "success" as const },
];

const operatingSignals = [
  { label: "Assessment Completion", value: "86%", caption: "30 dari 34 sesi pilot" },
  { label: "Submitted for Review", value: "12", caption: "menunggu asesor" },
  { label: "High Severity", value: "3", caption: "rekomendasi prioritas" },
  { label: "NKO Delta", value: "+1,92", caption: "terhadap TW sebelumnya" },
];

function formatScore(value: number) {
  return value.toLocaleString("id-ID", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function streamTone(kind: StreamKind) {
  if (kind === "quantitative") return "info";
  if (kind === "maturity") return "success";
  if (kind === "compliance") return "warning";
  return "neutral";
}

function levelClass(value: number) {
  if (value < 1) return "level-0";
  if (value < 2) return "level-1";
  if (value < 3) return "level-2";
  if (value < 3.5) return "level-3";
  return "level-4";
}

function NkoGauge({ value }: { value: number }) {
  const min = 80;
  const max = 110;
  const pct = Math.max(0, Math.min(1, (value - min) / (max - min)));
  const angle = -118 + pct * 236;

  return (
    <div className="nko-gauge" aria-label={`NKO ${formatScore(value)}`}>
      <svg viewBox="0 0 260 180" role="img" aria-labelledby="nko-gauge-title">
        <title id="nko-gauge-title">NKO gauge</title>
        <path className="gauge-rail" d="M34 132a98 98 0 0 1 192 0" />
        <path className="gauge-band band-alert" d="M34 132a98 98 0 0 1 44-82" />
        <path className="gauge-band band-watch" d="M78 50a98 98 0 0 1 88-8" />
        <path className="gauge-band band-good" d="M166 42a98 98 0 0 1 60 90" />
        <g transform={`rotate(${angle} 130 132)`}>
          <line className="gauge-needle" x1="130" y1="132" x2="130" y2="48" />
        </g>
        <circle className="gauge-hub" cx="130" cy="132" r="11" />
      </svg>
      <div className="nko-readout">
        <span>{formatScore(value)}</span>
        <small>NKO FINAL</small>
      </div>
    </div>
  );
}

function TrendChart() {
  const width = 560;
  const height = 190;
  const pad = 28;
  const values = trend.map((row) => row.nko);
  const min = Math.min(...values) - 1;
  const max = Math.max(...values) + 1;
  const points = trend
    .map((row, index) => {
      const x = pad + (index * (width - pad * 2)) / (trend.length - 1);
      const y = height - pad - ((row.nko - min) / (max - min)) * (height - pad * 2);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg className="trend-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Trend NKO">
      <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} />
      <line x1={pad} y1={pad} x2={pad} y2={height - pad} />
      <polyline points={points} />
      {trend.map((row, index) => {
        const x = pad + (index * (width - pad * 2)) / (trend.length - 1);
        const y = height - pad - ((row.nko - min) / (max - min)) * (height - pad * 2);
        return (
          <g key={row.quarter}>
            <circle cx={x} cy={y} r="4.5" />
            <text x={x} y={height - 8} textAnchor="middle">
              {row.quarter}
            </text>
            <text x={x} y={y - 10} textAnchor="middle">
              {formatScore(row.nko)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function Dashboard() {
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const [selectedCode, setSelectedCode] = useState(baseStreams[0].code);
  const [scenarioEnabled, setScenarioEnabled] = useState(false);
  const [scenario, setScenario] = useState({ eaf: 0, efor: 0, outage: 0, smap: 0 });
  const canReadExecutive =
    !!user && user.roles.some((role) => ["super_admin", "manajer_unit", "viewer"].includes(role));
  const periodeQuery = usePeriodeList();
  const activePeriode = periodeQuery.data?.data[0];
  const dashboardQuery = useDashboardExecutive(activePeriode?.id, canReadExecutive);
  const liveDashboard = useMemo(() => {
    if (!dashboardQuery.data) return null;
    return dashboardResponseToModel(dashboardQuery.data, activePeriode?.nama);
  }, [activePeriode?.nama, dashboardQuery.data]);
  const dashboard = useMemo(() => {
    if (!scenarioEnabled) return dashboardModel;

    return computeDashboard({
      ...dashboardInput,
      changedIndikator: "Scenario",
      streams: dashboardInput.streams.map((stream) => {
        if (stream.code === "EAF") return { ...stream, actualValue: stream.actualValue + scenario.eaf };
        if (stream.code === "EFOR") return { ...stream, actualValue: Math.max(0, stream.actualValue - scenario.efor) };
        if (stream.code === "OUTAGE") return { ...stream, actualValue: Math.min(4, stream.actualValue + scenario.outage) };
        if (stream.code === "SMAP") return { ...stream, actualValue: Math.min(4, stream.actualValue + scenario.smap) };
        return stream;
      }),
    });
  }, [scenario.eaf, scenario.efor, scenario.outage, scenario.smap, scenarioEnabled]);
  const baselineDashboard = liveDashboard ?? dashboardModel;
  const renderedDashboard = scenarioEnabled ? dashboard : baselineDashboard;
  const { streams, pillars, snapshot: nkoSnapshot } = renderedDashboard;
  const dataSource = scenarioEnabled ? "scenario" : liveDashboard?.source ?? "demo";
  const grossPillarTotal = pillars.reduce((total, pillar) => total + pillar.contribution, 0);
  const scenarioDelta = nkoSnapshot.nkoTotal - dashboardModel.snapshot.nkoTotal;
  const selectedStream = useMemo(
    () => streams.find((stream) => stream.code === selectedCode) ?? streams[0],
    [selectedCode],
  );
  const canOpenAssessment =
    !!user && user.roles.some((role) => ["super_admin", "pic_bidang", "asesor"].includes(role));

  useEffect(() => {
    if (!accessToken || !activePeriode?.id || !canReadExecutive) return;
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/dashboard?token=${accessToken}`);
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as { type?: string; periode_id?: string };
        if (payload.type === "nko_updated" && payload.periode_id === activePeriode.id) {
          queryClient.invalidateQueries({ queryKey: ["dashboard-executive", activePeriode.id] });
        }
      } catch {
        /* Ignore malformed WS frames; next polling interval will refresh. */
      }
    };
    return () => ws.close();
  }, [accessToken, activePeriode?.id, canReadExecutive, queryClient]);

  return (
    <main className="executive-dashboard">
      <section className="dashboard-hero" aria-label="Executive NKO overview">
        <div className="hero-copy">
          <div className="hero-kicker">
            <SkLed state="on" label="PULSE live" />
            <span>{nkoSnapshot.periode}</span>
          </div>
          <h1>Executive NKO Dashboard</h1>
          <p>
            Dashboard Phase 3 mengikuti blueprint Konkin: KPI kuantitatif, maturity-level JSONB,
            bobot pilar, pengurang compliance, trend, heatmap, forecast, dan fallback demo saat data live belum lengkap.
          </p>
          <div className="hero-actions">
            {canOpenAssessment && (
              <Link to="/assessment">
                <SkButton type="button" variant="primary">
                  Assessment
                </SkButton>
              </Link>
            )}
            <Link to="/recommendations">
              <SkButton type="button" variant="secondary">
                Rekomendasi
              </SkButton>
            </Link>
          </div>
        </div>

        <SkPanel className="hero-gauge-panel" title="NKO REAL-TIME">
          <NkoGauge value={nkoSnapshot.nkoTotal} />
          <div className="snapshot-grid">
            <div>
              <span>{formatScore(nkoSnapshot.grossPillar)}</span>
              <small>Gross Pilar I-V</small>
            </div>
            <div>
              <span>-{formatScore(nkoSnapshot.complianceDeduction)}</span>
              <small>Pengurang VI</small>
            </div>
            <div>
              <span>{formatScore(nkoSnapshot.forecast)}</span>
              <small>Forecast</small>
            </div>
          </div>
          <p className="snapshot-note">
            Sumber data: {dataSource}. Update terakhir: {nkoSnapshot.updatedAt}. Perubahan terakhir:{" "}
            {nkoSnapshot.changedIndikator}.
          </p>
        </SkPanel>
      </section>

      <section className="dashboard-grid signal-grid" aria-label="Operating signals">
        {operatingSignals.map((signal) => (
          <SkPanel key={signal.label} className="signal-panel">
            <span>{signal.label}</span>
            <strong>{signal.value}</strong>
            <small>{signal.caption}</small>
          </SkPanel>
        ))}
      </section>

      <section className="dashboard-grid scenario-grid" aria-label="Scenario simulation">
        <SkPanel title="Scenario Simulator" className="scenario-panel">
          <div className="scenario-head">
            <div>
              <h2>What-if NKO</h2>
              <p>Simulasi dummy untuk melihat sensitivitas EAF, EFOR, maturity, dan compliance.</p>
            </div>
            <div className="scenario-toggle">
              <span>{scenarioEnabled ? "ON" : "OFF"}</span>
              <SkToggle
                checked={scenarioEnabled}
                label="Aktifkan scenario simulator"
                onCheckedChange={setScenarioEnabled}
              />
            </div>
          </div>

          <div className="scenario-controls">
            <label>
              <span>EAF uplift</span>
              <strong>+{scenario.eaf.toFixed(1)} pp</strong>
              <SkSlider
                label="EAF uplift"
                min={0}
                max={3}
                step={0.1}
                value={scenario.eaf}
                onChange={(event) => setScenario((current) => ({ ...current, eaf: Number(event.currentTarget.value) }))}
              />
            </label>
            <label>
              <span>EFOR reduction</span>
              <strong>-{scenario.efor.toFixed(1)} pp</strong>
              <SkSlider
                label="EFOR reduction"
                min={0}
                max={1.2}
                step={0.1}
                value={scenario.efor}
                onChange={(event) => setScenario((current) => ({ ...current, efor: Number(event.currentTarget.value) }))}
              />
            </label>
            <label>
              <span>Outage maturity</span>
              <strong>+{scenario.outage.toFixed(2)} level</strong>
              <SkSlider
                label="Outage maturity uplift"
                min={0}
                max={0.45}
                step={0.05}
                value={scenario.outage}
                onChange={(event) => setScenario((current) => ({ ...current, outage: Number(event.currentTarget.value) }))}
              />
            </label>
            <label>
              <span>SMAP recovery</span>
              <strong>+{scenario.smap.toFixed(2)} level</strong>
              <SkSlider
                label="SMAP recovery"
                min={0}
                max={0.5}
                step={0.05}
                value={scenario.smap}
                onChange={(event) => setScenario((current) => ({ ...current, smap: Number(event.currentTarget.value) }))}
              />
            </label>
          </div>
        </SkPanel>

        <SkPanel title="Scenario Impact" className="scenario-impact-panel">
          <div className="scenario-impact-score">
            <span>{scenarioDelta >= 0 ? "+" : ""}{formatScore(scenarioDelta)}</span>
            <small>delta NKO terhadap baseline 103,36</small>
          </div>
          <div className="scenario-impact-stack">
            <div>
              <span>Baseline</span>
              <strong>{formatScore(dashboardModel.snapshot.nkoTotal)}</strong>
            </div>
            <div>
              <span>Scenario</span>
              <strong>{formatScore(nkoSnapshot.nkoTotal)}</strong>
            </div>
            <div>
              <span>Compliance</span>
              <strong>-{formatScore(nkoSnapshot.complianceDeduction)}</strong>
            </div>
          </div>
          <SkButton
            type="button"
            variant="secondary"
            onClick={() => {
              setScenario({ eaf: 0, efor: 0, outage: 0, smap: 0 });
              setScenarioEnabled(false);
            }}
          >
            Reset Scenario
          </SkButton>
        </SkPanel>
      </section>

      <section className="dashboard-grid pilar-grid" aria-label="Pilar breakdown">
        {pillars.map((pillar) => (
          <SkPanel key={pillar.code} className="pilar-panel">
            <div className="pilar-code">{pillar.code}</div>
            <h2>{pillar.name}</h2>
            <div className="pilar-meter" aria-hidden="true">
              <span style={{ width: `${Math.min(100, (pillar.contribution / pillar.weight) * 100)}%` }} />
            </div>
            <div className="pilar-stats">
              <strong>{formatScore(pillar.contribution)}</strong>
              <span>/ {pillar.weight.toFixed(2)}</span>
            </div>
            <SkBadge tone={pillar.status === "turun" ? "warning" : "success"}>
              {pillar.status} {pillar.trend > 0 ? "+" : ""}
              {pillar.trend.toFixed(2)}
            </SkBadge>
          </SkPanel>
        ))}
      </section>

      <section className="dashboard-grid analytics-grid">
        <SkPanel title="Trend NKO + Forecast" className="trend-panel">
          <TrendChart />
        </SkPanel>

        <SkPanel title="Heatmap Maturity" className="heatmap-panel">
          <div className="heatmap-table" role="table" aria-label="Maturity heatmap">
            <div className="heatmap-row heatmap-head" role="row">
              <span>Stream</span>
              <span>TW1</span>
              <span>TW2</span>
              <span>TW3</span>
              <span>TW4</span>
            </div>
            {heatmap.map((row) => (
              <div className="heatmap-row" role="row" key={row.stream}>
                <strong>{row.stream}</strong>
                {row.values.map((value, index) => (
                  <span key={`${row.stream}-${index}`} className={`heat-cell ${levelClass(value)}`}>
                    {value.toFixed(2)}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </SkPanel>
      </section>

      <section className="dashboard-grid reconciliation-grid" aria-label="NKO reconciliation">
        <SkPanel title="NKO Reconciliation" className="reconciliation-panel">
          <div className="waterfall-stack" aria-label="Gross pillar contribution">
            {pillars.map((pillar) => (
              <div
                key={pillar.code}
                className="waterfall-segment"
                style={{ width: `${Math.max(8, (pillar.contribution / grossPillarTotal) * 100)}%` }}
              >
                <span>{pillar.code}</span>
                <strong>{formatScore(pillar.contribution)}</strong>
              </div>
            ))}
          </div>
          <div className="reconciliation-formula">
            <div>
              <span>Gross Pilar I-V</span>
              <strong>{formatScore(nkoSnapshot.grossPillar)}</strong>
            </div>
            <div>
              <span>Pengurang VI</span>
              <strong>-{formatScore(nkoSnapshot.complianceDeduction)}</strong>
            </div>
            <div>
              <span>NKO Final</span>
              <strong>{formatScore(nkoSnapshot.nkoTotal)}</strong>
            </div>
          </div>
        </SkPanel>

        <SkPanel title="Formula Ledger" className="ledger-panel">
          <div className="ledger-table" role="table" aria-label="Stream formula ledger">
            <div className="ledger-row ledger-head" role="row">
              <span>Stream</span>
              <span>Metode</span>
              <span>Aktual</span>
              <span>Target</span>
              <span>Score</span>
              <span>Dampak</span>
            </div>
            {streams.map((stream) => (
              <div className="ledger-row" role="row" key={stream.code}>
                <strong>{stream.code}</strong>
                <span>{stream.polarity}</span>
                <span>{stream.actual}</span>
                <span>{stream.target}</span>
                <span>{formatScore(stream.score)}</span>
                <span>
                  {stream.kind === "compliance"
                    ? `-${formatScore(stream.deduction)}`
                    : formatScore(stream.contribution)}
                </span>
              </div>
            ))}
          </div>
        </SkPanel>
      </section>

      <section className="dashboard-grid stream-grid" aria-label="Stream formula cards">
        {streams.map((stream) => (
          <button
            key={stream.code}
            type="button"
            className="stream-button"
            aria-pressed={selectedStream.code === stream.code}
            onClick={() => setSelectedCode(stream.code)}
          >
            <SkPanel className="stream-panel">
              <div className="stream-head">
                <div>
                  <span className="stream-code">{stream.code}</span>
                  <h2>{stream.name}</h2>
                </div>
                <SkBadge tone={streamTone(stream.kind)}>{stream.kind}</SkBadge>
              </div>
              <dl className="stream-metadata">
                <div>
                  <dt>Satuan</dt>
                  <dd>{stream.unit}</dd>
                </div>
                <div>
                  <dt>Polaritas</dt>
                  <dd>{stream.polarity}</dd>
                </div>
                <div>
                  <dt>Bobot</dt>
                  <dd>{stream.weight}</dd>
                </div>
                <div>
                  <dt>Nilai</dt>
                  <dd>{formatScore(stream.score)}</dd>
                </div>
              </dl>
              <div className="formula-strip">{stream.formula}</div>
              <div className="actual-target">
                <span>Realisasi: {stream.actual}</span>
                <span>Target: {stream.target}</span>
              </div>
              <p>{stream.note}</p>
            </SkPanel>
          </button>
        ))}
      </section>

      <section className="dashboard-grid drilldown-grid">
        <SkPanel title={`${selectedStream.code} DETAIL`} className="drilldown-panel">
          <div className="drilldown-head">
            <div>
              <h2>{selectedStream.name}</h2>
              <p>{selectedStream.note}</p>
            </div>
            <div className="drilldown-score">
              <span>{formatScore(selectedStream.score)}</span>
              <small>{selectedStream.unit}</small>
            </div>
          </div>

          <div className="calculation-trace" aria-label={`${selectedStream.code} calculation trace`}>
            <div>
              <span>Realisasi</span>
              <strong>{selectedStream.actual}</strong>
            </div>
            <div>
              <span>Target</span>
              <strong>{selectedStream.target}</strong>
            </div>
            <div>
              <span>Score</span>
              <strong>{formatScore(selectedStream.score)}</strong>
            </div>
            <div>
              <span>{selectedStream.kind === "compliance" ? "Pengurang" : "Kontribusi"}</span>
              <strong>
                {selectedStream.kind === "compliance"
                  ? `-${formatScore(selectedStream.deduction)}`
                  : formatScore(selectedStream.contribution)}
              </strong>
            </div>
          </div>

          <div className="component-grid">
            {(componentPoints[selectedStream.code] ?? []).map((item) => (
              <div className={`component-chip ${item.state}`} key={item.label}>
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </div>
            ))}
          </div>

          <div className="bidang-bars">
            {(bidangScores[selectedStream.code] ?? []).map((row) => {
              const max = selectedStream.kind === "quantitative" ? 120 : 4;
              const width = Math.max(6, Math.min(100, (row.value / max) * 100));
              return (
                <div className="bidang-bar" key={row.bidang}>
                  <span>{row.bidang}</span>
                  <div>
                    <i style={{ width: `${width}%` }} />
                  </div>
                  <strong>{selectedStream.kind === "quantitative" ? formatScore(row.value) : row.value.toFixed(2)}</strong>
                </div>
              );
            })}
          </div>
        </SkPanel>

        <SkPanel title="Recommendation Pipeline" className="pipeline-panel">
          <div className="pipeline-stack">
            {pipeline.map((item) => (
              <div key={item.label}>
                <SkBadge tone={item.tone}>{item.label}</SkBadge>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
          <div className="pipeline-total">
            <span>47</span>
            <small>total rekomendasi dummy aktif + historis</small>
          </div>
        </SkPanel>
      </section>

      <section className="dashboard-grid lower-grid">
        <SkPanel title="Needs Attention">
          <ul className="attention-list">
            {attention.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </SkPanel>

        <SkPanel title="Aggregation Rules">
          <div className="rule-stack">
            <div>
              <strong>KPI positif</strong>
              <span>Realisasi / Target x 100%</span>
            </div>
            <div>
              <strong>KPI negatif</strong>
              <span>{`{2 - (Realisasi / Target)} x 100%`}</span>
            </div>
            <div>
              <strong>Maturity Level</strong>
              <span>Sub-area ke area ke stream, normalisasi missing/N/A.</span>
            </div>
            <div>
              <strong>NKO</strong>
              <span>Jumlah Pilar I-V dikurangi Compliance, cap pengurang -10.</span>
            </div>
          </div>
        </SkPanel>
      </section>
    </main>
  );
}
