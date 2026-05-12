import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PageEnvelope } from "@/lib/phase2-api";

export interface ComplianceLaporanDefinisi {
  id: string;
  kode: string;
  nama: string;
  default_due_day: number;
  pengurang_per_keterlambatan: string | number;
  pengurang_per_invaliditas: string | number;
  is_active: boolean;
}

export interface ComplianceSubmission {
  id: string;
  periode_id: string;
  definisi_id: string;
  bulan: number;
  tanggal_jatuh_tempo: string;
  tanggal_submit: string | null;
  keterlambatan_hari: number;
  is_valid: boolean;
  catatan: string | null;
  created_at: string;
  updated_at: string;
}

export interface ComplianceKomponen {
  id: string;
  kode: string;
  nama: string;
  formula: Record<string, unknown>;
  pengurang_cap: string | number;
  is_active: boolean;
}

export interface ComplianceKomponenRealisasi {
  id: string;
  periode_id: string;
  komponen_id: string;
  nilai: string | number;
  pengurang: string | number;
  payload: Record<string, unknown>;
  catatan: string | null;
  created_at: string;
  updated_at: string;
}

export interface ComplianceSummaryRow {
  type: "laporan" | "komponen";
  kode: string;
  nama: string;
  bulan?: number;
  keterlambatan_hari?: number;
  is_valid?: boolean;
  nilai?: number;
  pengurang: number;
}

export interface ComplianceSummary {
  periode_id: string;
  report_count: number;
  late_report_count: number;
  invalid_report_count: number;
  component_count: number;
  laporan_pengurang: string | number;
  komponen_pengurang: string | number;
  total_pengurang_raw: string | number;
  total_pengurang: string | number;
  cap: string | number;
  rows: ComplianceSummaryRow[];
}

export interface ComplianceSubmissionPayload {
  periode_id: string;
  definisi_id: string;
  bulan: number;
  tanggal_jatuh_tempo: string;
  tanggal_submit: string | null;
  is_valid: boolean;
  catatan?: string | null;
}

export interface ComplianceComponentPayload {
  periode_id: string;
  komponen_id: string;
  nilai: number;
  pengurang: number;
  payload: Record<string, unknown>;
  catatan?: string | null;
}

async function getPage<T>(path: string): Promise<PageEnvelope<T>> {
  const { data } = await api.get<PageEnvelope<T>>(path);
  return data;
}

export function asNumber(value: string | number | null | undefined, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function useComplianceDefinitions() {
  return useQuery({
    queryKey: ["compliance-definitions"],
    queryFn: () => getPage<ComplianceLaporanDefinisi>("/compliance/laporan-definisi?page_size=100"),
  });
}

export function useComplianceSubmissions(periodeId: string | undefined) {
  return useQuery({
    queryKey: ["compliance-submissions", periodeId],
    queryFn: () => getPage<ComplianceSubmission>(`/compliance/submissions?periode_id=${periodeId}&page_size=200`),
    enabled: !!periodeId,
  });
}

export function useComplianceComponents() {
  return useQuery({
    queryKey: ["compliance-components"],
    queryFn: () => getPage<ComplianceKomponen>("/compliance/components?page_size=100"),
  });
}

export function useComplianceSummary(periodeId: string | undefined) {
  return useQuery({
    queryKey: ["compliance-summary", periodeId],
    queryFn: async () => {
      const { data } = await api.get<ComplianceSummary>("/compliance/summary", { params: { periode_id: periodeId } });
      return data;
    },
    enabled: !!periodeId,
    refetchInterval: 30_000,
  });
}

export function useUpsertComplianceSubmission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ComplianceSubmissionPayload) => {
      const { data } = await api.post<ComplianceSubmission>("/compliance/submissions", payload);
      return data;
    },
    onSuccess: (row) => {
      qc.invalidateQueries({ queryKey: ["compliance-submissions", row.periode_id] });
      qc.invalidateQueries({ queryKey: ["compliance-summary", row.periode_id] });
      qc.invalidateQueries({ queryKey: ["dashboard-executive", row.periode_id] });
    },
  });
}

export function useUpsertComplianceComponent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ComplianceComponentPayload) => {
      const { data } = await api.post<ComplianceKomponenRealisasi>("/compliance/component-realizations", payload);
      return data;
    },
    onSuccess: (row) => {
      qc.invalidateQueries({ queryKey: ["compliance-summary", row.periode_id] });
      qc.invalidateQueries({ queryKey: ["dashboard-executive", row.periode_id] });
    },
  });
}
