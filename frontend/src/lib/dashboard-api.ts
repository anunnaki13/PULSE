import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { dashboardModel } from "@/lib/dashboard-fixtures";
import type { ComputedStream, DashboardSnapshot, PillarSummary, StreamKind } from "@/lib/dashboard-calculations";

type DashboardSnapshotDto = {
  id: string;
  periode_id: string;
  nko_total: string | number;
  gross_pilar_total: string | number;
  compliance_deduction: string | number;
  source: "live" | "fallback" | "demo";
  updated_at: string;
};

export type DashboardExecutiveDto = {
  snapshot: DashboardSnapshotDto;
  data: {
    pilar?: Array<{
      kode: string;
      nama: string;
      bobot?: number;
      score?: number;
      contribution?: number;
      trend?: number;
    }>;
    streams?: Array<{
      kode: string;
      nama: string;
      unit: string;
      polarity: string;
      formula: string;
      realisasi?: number | null;
      target?: number | null;
      score?: number | null;
      contribution?: number;
      deduction?: number;
    }>;
    source?: "live" | "fallback" | "demo";
    changed_indikator_id?: string | null;
  };
};

function asNumber(value: string | number | null | undefined, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function inferKind(stream: { kode: string; unit: string }): StreamKind {
  if (stream.kode === "SMAP") return "compliance";
  if (stream.unit === "level") return "maturity";
  return "quantitative";
}

function formatValue(value: number | null | undefined, unit: string) {
  if (value == null) return "-";
  const formatted = value.toLocaleString("id-ID", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return unit === "%" ? `${formatted}%` : formatted;
}

export function dashboardResponseToModel(dto: DashboardExecutiveDto, periodeName?: string) {
  const streams: ComputedStream[] = (dto.data.streams?.length ? dto.data.streams : []).map((stream) => {
    const fallback = dashboardModel.streams.find((item) => item.code === stream.kode);
    const unit = stream.unit === "level" ? "Level 0-4" : stream.unit;
    const actualValue = asNumber(stream.realisasi, fallback?.actualValue ?? 0);
    const targetValue = asNumber(stream.target, fallback?.targetValue ?? 0);
    const score = asNumber(stream.score, fallback?.score ?? 0);
    const kind = inferKind(stream);
    return {
      code: stream.kode,
      name: stream.nama,
      kind,
      pillar: fallback?.pillar ?? (kind === "compliance" ? "VI" : "I"),
      unit,
      formula: stream.formula,
      polarity: (fallback?.polarity ?? (stream.polarity === "negatif" ? "negatif" : "positif")) as ComputedStream["polarity"],
      actualValue,
      targetValue,
      weight: fallback?.weight ?? 0,
      note: fallback?.note ?? "Data stream berasal dari snapshot NKO backend.",
      actual: formatValue(actualValue, stream.unit),
      target: formatValue(targetValue, stream.unit),
      score,
      contribution: asNumber(stream.contribution, fallback?.contribution ?? 0),
      deduction: asNumber(stream.deduction, fallback?.deduction ?? 0),
    };
  });

  const pillars: PillarSummary[] = (dto.data.pilar?.length ? dto.data.pilar : []).map((pillar) => {
    const fallback = dashboardModel.pillars.find((item) => item.code === pillar.kode);
    const trend = asNumber(pillar.trend, fallback?.trend ?? 0);
    return {
      code: pillar.kode,
      name: pillar.nama,
      weight: asNumber(pillar.bobot, fallback?.weight ?? 0),
      contribution: asNumber(pillar.contribution, fallback?.contribution ?? 0),
      trend,
      status: trend < -0.05 ? "turun" : trend > 0.05 ? "naik" : "stabil",
    };
  });

  const nkoTotal = asNumber(dto.snapshot.nko_total, dashboardModel.snapshot.nkoTotal);
  const snapshot: DashboardSnapshot = {
    periode: periodeName ?? `Periode ${dto.snapshot.periode_id.slice(0, 8)}`,
    nkoTotal,
    grossPillar: asNumber(dto.snapshot.gross_pilar_total, dashboardModel.snapshot.grossPillar),
    complianceDeduction: asNumber(dto.snapshot.compliance_deduction, dashboardModel.snapshot.complianceDeduction),
    forecast: nkoTotal + 0.82,
    updatedAt: new Date(dto.snapshot.updated_at).toLocaleString("id-ID", {
      dateStyle: "medium",
      timeStyle: "short",
    }),
    changedIndikator: dto.data.changed_indikator_id ? "Live update" : dto.snapshot.source,
  };

  return {
    streams: streams.length ? streams : dashboardModel.streams,
    pillars: pillars.length ? pillars : dashboardModel.pillars,
    snapshot,
    source: dto.snapshot.source,
  };
}

export function useDashboardExecutive(periodeId: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ["dashboard-executive", periodeId],
    queryFn: async () => {
      const { data } = await api.get<DashboardExecutiveDto>("/dashboard/executive", {
        params: { periode_id: periodeId },
      });
      return data;
    },
    enabled: enabled && !!periodeId,
    refetchInterval: 30_000,
  });
}
