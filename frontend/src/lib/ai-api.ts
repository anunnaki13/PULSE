import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface AiStatus {
  available: boolean;
  mode: "mock" | "openrouter" | "unavailable";
  routine_model: string;
  complex_model: string;
  message: string;
}

export interface AiSuggestionResponse {
  log_id: string;
  suggestion_type: string;
  text: string;
  model_used: string;
  fallback_used: boolean;
  pii_masked: boolean;
}

export interface AiDraftRecommendationResponse extends AiSuggestionResponse {
  structured: {
    severity: "low" | "medium" | "high" | "critical";
    deskripsi: string;
    action_items: Array<{ action: string; deadline: string | null; owner_user_id: string | null }>;
    target_outcome: string;
  };
}

export interface AiAnomalyResponse extends AiSuggestionResponse {
  classification: "legitimate_improvement" | "data_entry_error" | "needs_verification" | "suspicious";
  risk_score: number;
  reasons: string[];
}

export interface AiInlineHelp {
  id: string;
  indikator_id: string;
  apa_itu: string;
  formula_explanation: string;
  best_practice: string;
  common_pitfalls: string;
  related_indikator: unknown[];
  generated_by_model: string;
  generated_at: string;
  expires_at: string | null;
}

export interface AiComparativeAnalysisResponse extends AiSuggestionResponse {
  trend: Array<{ periode: string; score: number }>;
}

export function useAiStatus() {
  return useQuery({
    queryKey: ["ai-status"],
    queryFn: async () => {
      const { data } = await api.get<AiStatus>("/ai/status");
      return data;
    },
    refetchInterval: 30_000,
  });
}

export function useDraftJustification() {
  return useMutation({
    mutationFn: async (payload: { assessment_session_id: string; user_note?: string | null }) => {
      const { data } = await api.post<AiSuggestionResponse>("/ai/draft-justification", payload);
      return data;
    },
  });
}

export function useDraftRecommendation() {
  return useMutation({
    mutationFn: async (payload: { assessment_session_id: string; user_note?: string | null }) => {
      const { data } = await api.post<AiDraftRecommendationResponse>("/ai/draft-recommendation", payload);
      return data;
    },
  });
}

export function useAnomalyCheck() {
  return useMutation({
    mutationFn: async (payload: { assessment_session_id: string; user_note?: string | null }) => {
      const { data } = await api.post<AiAnomalyResponse>("/ai/anomaly-check", payload);
      return data;
    },
  });
}

export function useInlineHelp() {
  return useMutation({
    mutationFn: async (indikatorId: string) => {
      const { data } = await api.get<AiInlineHelp>(`/ai/inline-help/${indikatorId}`);
      return data;
    },
  });
}

export function useComparativeAnalysis() {
  return useMutation({
    mutationFn: async (payload: { assessment_session_id: string }) => {
      const { data } = await api.post<AiComparativeAnalysisResponse>("/ai/comparative-analysis", payload);
      return data;
    },
  });
}
