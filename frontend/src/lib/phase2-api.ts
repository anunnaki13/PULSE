import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export type PeriodeStatus =
  | "draft"
  | "aktif"
  | "self_assessment"
  | "asesmen"
  | "finalisasi"
  | "closed";

export type SessionState =
  | "draft"
  | "submitted"
  | "approved"
  | "overridden"
  | "revision_requested"
  | "abandoned";

export type RecommendationStatus =
  | "open"
  | "in_progress"
  | "pending_review"
  | "closed"
  | "carried_over";

export interface PageEnvelope<T> {
  data: T[];
  meta: { page: number; page_size: number; total: number };
}

export interface Periode {
  id: string;
  tahun: number;
  triwulan: number;
  semester: number;
  nama: string;
  status: PeriodeStatus;
  tanggal_buka: string | null;
  tanggal_tutup: string | null;
  last_transition_reason?: string | null;
  last_transition_at?: string | null;
  updated_at: string;
}

export interface AssessmentSession {
  id: string;
  periode_id: string;
  indikator_id: string;
  bidang_id: string | null;
  state: SessionState;
  payload: Record<string, unknown> | null;
  realisasi: string | number | null;
  target: string | number | null;
  pencapaian: string | number | null;
  nilai: string | number | null;
  nilai_final: string | number | null;
  catatan_pic: string | null;
  catatan_asesor: string | null;
  link_eviden: string | null;
  submitted_at: string | null;
  asesor_reviewed_at: string | null;
  updated_at: string;
  indikator?: {
    id: string;
    kode: string;
    nama: string;
    bobot: string | number;
    polaritas: "positif" | "negatif" | "range";
    formula: string | null;
  } | null;
  ml_stream?: {
    id: string;
    kode: string;
    nama: string;
    version: string;
    structure: {
      areas?: Array<{
        code?: string;
        kode?: string;
        nama?: string;
        sub_areas?: Array<{
          code?: string;
          kode?: string;
          nama?: string;
          weight?: number;
          criteria?: Record<string, string>;
        }>;
      }>;
    };
  } | null;
}

export interface SelfAssessmentSavePayload {
  id: string;
  realisasi?: number | string | null;
  target?: number | string | null;
  catatan_pic?: string | null;
  link_eviden?: string | null;
  payload?: Record<string, unknown> | null;
}

export interface Recommendation {
  id: string;
  source_assessment_id: string;
  source_periode_id: string;
  target_periode_id: string;
  status: RecommendationStatus;
  severity: "low" | "medium" | "high" | "critical";
  deskripsi: string;
  action_items: Array<{ action: string; deadline: string | null; owner_user_id: string | null }>;
  progress_percent: number;
  progress_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationRow {
  id: string;
  user_id: string;
  type: string;
  title: string;
  body: string;
  payload: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}

export interface AuditLogRow {
  id: string;
  user_id: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  before_data: Record<string, unknown> | null;
  after_data: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface InlineRecommendationDraft {
  source_assessment_id: string;
  severity: "low" | "medium" | "high" | "critical";
  deskripsi: string;
  action_items: Array<{ action: string; deadline: string | null; owner_user_id: string | null }>;
  target_periode_id: string;
}

async function getPage<T>(path: string): Promise<PageEnvelope<T>> {
  const { data } = await api.get<PageEnvelope<T>>(path);
  return data;
}

export function usePeriodeList() {
  return useQuery({
    queryKey: ["periode"],
    queryFn: () => getPage<Periode>("/periode?page_size=20"),
  });
}

export function useCreatePeriode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      tahun: number;
      triwulan: number;
      semester: number;
      nama: string;
      tanggal_buka?: string | null;
      tanggal_tutup?: string | null;
    }) => {
      const { data } = await api.post<Periode>("/periode", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["periode"] }),
  });
}

export function useTransitionPeriode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { id: string; target_state: PeriodeStatus; reason?: string }) => {
      const { data } = await api.post<Periode>(`/periode/${payload.id}/transition`, {
        target_state: payload.target_state,
        reason: payload.reason || null,
      });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["periode"] });
      qc.invalidateQueries({ queryKey: ["assessment-sessions"] });
      qc.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}

export function useAssessmentSessions() {
  return useQuery({
    queryKey: ["assessment-sessions"],
    queryFn: () => getPage<AssessmentSession>("/assessment/sessions?page_size=100"),
  });
}

export function useSaveSelfAssessment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: saveSelfAssessment,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assessment-sessions"] }),
  });
}

export async function saveSelfAssessment(payload: SelfAssessmentSavePayload) {
  const { id, ...body } = payload;
  const { data } = await api.patch<AssessmentSession>(`/assessment/sessions/${id}/self-assessment`, body);
  return data;
}

export function useSubmitAssessment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<AssessmentSession>(`/assessment/sessions/${id}/submit`, {});
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assessment-sessions"] }),
  });
}

export function useAsesorReviewAssessment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      id: string;
      decision: "approve" | "override" | "request_revision";
      nilai_final?: number | string | null;
      catatan_asesor?: string | null;
      inline_recommendations?: InlineRecommendationDraft[] | null;
    }) => {
      const { id, ...body } = payload;
      const { data } = await api.post<AssessmentSession>(`/assessment/sessions/${id}/asesor-review`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessment-sessions"] });
      qc.invalidateQueries({ queryKey: ["recommendations"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useRecommendations() {
  return useQuery({
    queryKey: ["recommendations"],
    queryFn: () => getPage<Recommendation>("/recommendations?page_size=100"),
  });
}

export function useUpdateRecommendationProgress() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { id: string; progress_percent?: number; progress_notes?: string }) => {
      const { id, ...body } = payload;
      const { data } = await api.patch<Recommendation>(`/recommendations/${id}/progress`, body);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recommendations"] }),
  });
}

export function useMarkRecommendationCompleted() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<Recommendation>(`/recommendations/${id}/mark-completed`, {});
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recommendations"] }),
  });
}

export function useVerifyRecommendationClose() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { id: string; asesor_close_notes: string }) => {
      const { id, ...body } = payload;
      const { data } = await api.post<Recommendation>(`/recommendations/${id}/verify-close`, body);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recommendations"] }),
  });
}

export function useNotifications() {
  return useQuery({
    queryKey: ["notifications"],
    queryFn: () => getPage<NotificationRow>("/notifications?page_size=50"),
    refetchInterval: 15_000,
  });
}

export function useMarkAllNotificationsRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.patch<{ data: { marked: number } }>("/notifications/read-all");
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useAuditLogs() {
  return useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => getPage<AuditLogRow>("/audit-logs?page_size=100"),
  });
}

export const statusTone = (status: string) => {
  if (["approved", "closed", "finalisasi"].includes(status)) return "success" as const;
  if (["submitted", "pending_review", "asesmen", "self_assessment"].includes(status)) {
    return "warning" as const;
  }
  if (["overridden", "revision_requested", "critical"].includes(status)) return "danger" as const;
  return "info" as const;
};
