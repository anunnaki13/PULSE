import { Link } from "react-router-dom";
import { useMemo, useState } from "react";
import {
  SkBadge,
  SkButton,
  SkInput,
  SkLed,
  SkLevelSelector,
  SkPanel,
  SkSelect,
  SkSlider,
  SkToggle,
} from "@/components/skeuomorphic";
import { useAssessmentAutoSave } from "@/lib/offline-assessment-queue";
import {
  type AiAnomalyResponse,
  type AiComparativeAnalysisResponse,
  type AiInlineHelp,
  useAiStatus,
  useAnomalyCheck,
  useComparativeAnalysis,
  useDraftJustification,
  useDraftRecommendation,
  useInlineHelp,
} from "@/lib/ai-api";
import {
  type AssessmentSession,
  statusTone,
  useAsesorReviewAssessment,
  useAssessmentSessions,
  useSaveSelfAssessment,
  useSubmitAssessment,
} from "@/lib/phase2-api";
import { useAuthStore } from "@/lib/auth-store";

type Draft = {
  target: string;
  realisasi: string;
  catatan_pic: string;
  link_eviden: string;
  payload: Record<string, MlPayloadItem>;
};

type MlPayloadItem = {
  kode: string;
  nama: string;
  area: string;
  criteria: Record<string, string>;
  weight?: number;
  level: number;
  value: number | null;
  tidak_dinilai: boolean;
  tidak_dinilai_reason: string;
  lock_integer: boolean;
};

type ReviewDraft = {
  nilai_final: string;
  catatan_asesor: string;
  recommendations: InlineRecommendationDraft[];
};

type InlineRecommendationDraft = {
  severity: "low" | "medium" | "high" | "critical";
  rekomendasi: string;
  action_items: InlineActionDraft[];
};

type InlineActionDraft = {
  action: string;
  deadline: string;
};

function fmt(value: string | number | null) {
  if (value === null || value === undefined) return "-";
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(2) : String(value);
}

function payloadFrom(row: AssessmentSession): Record<string, MlPayloadItem> {
  const source = row.payload ?? {};
  const fromRubric = row.ml_stream?.structure?.areas?.flatMap((area) =>
    (area.sub_areas ?? []).map((sub) => {
      const key = sub.kode ?? sub.code ?? sub.nama ?? "sub_area";
      const existing = source[key] && typeof source[key] === "object" ? (source[key] as Partial<MlPayloadItem>) : {};
      const level = Number.isFinite(Number(existing.level)) ? Number(existing.level) : 3;
      return [
        key,
        {
          kode: key,
          nama: sub.nama ?? key,
          area: area.nama ?? area.kode ?? area.code ?? "Maturity",
          criteria: sub.criteria ?? {},
          weight: Number.isFinite(Number(sub.weight)) ? Number(sub.weight) : undefined,
          level,
          value: existing.value == null ? level + 0.5 : Number(existing.value),
          tidak_dinilai: Boolean(existing.tidak_dinilai),
          tidak_dinilai_reason: String(existing.tidak_dinilai_reason ?? ""),
          lock_integer: Boolean(existing.lock_integer),
        },
      ] as const;
    }),
  );
  if (fromRubric && fromRubric.length > 0) return Object.fromEntries(fromRubric);

  const entries = Object.entries(source)
    .filter(([, value]) => value && typeof value === "object")
    .map(([key, value]) => {
      const item = value as Partial<MlPayloadItem>;
      const level = Number.isFinite(Number(item.level)) ? Number(item.level) : 3;
      return [
        key,
        {
          kode: key,
          nama: String(item.nama ?? key),
          area: String(item.area ?? "Maturity"),
          criteria: item.criteria ?? {},
          level,
          value: item.value == null ? level + 0.5 : Number(item.value),
          tidak_dinilai: Boolean(item.tidak_dinilai),
          tidak_dinilai_reason: String(item.tidak_dinilai_reason ?? ""),
          lock_integer: Boolean(item.lock_integer),
        },
      ] as const;
    });
  if (entries.length > 0) return Object.fromEntries(entries);
  return {
    sub_area_1: {
      kode: "sub_area_1",
      nama: "Sub-area 1",
      area: "Maturity",
      criteria: {},
      level: 3,
      value: 3.5,
      tidak_dinilai: false,
      tidak_dinilai_reason: "",
      lock_integer: false,
    },
  };
}

function draftFrom(row: AssessmentSession): Draft {
  return {
    target: row.target == null ? "" : String(row.target),
    realisasi: row.realisasi == null ? "" : String(row.realisasi),
    catatan_pic: row.catatan_pic ?? "",
    link_eviden: row.link_eviden ?? "",
    payload: payloadFrom(row),
  };
}

function reviewFrom(row: AssessmentSession): ReviewDraft {
  return {
    nilai_final: row.nilai == null ? "" : String(row.nilai),
    catatan_asesor: row.catatan_asesor ?? "",
    recommendations: [emptyRecommendationDraft()],
  };
}

function emptyRecommendationDraft(): InlineRecommendationDraft {
  return {
    severity: "medium",
    rekomendasi: "",
    action_items: [emptyActionDraft()],
  };
}

function emptyActionDraft(): InlineActionDraft {
  return {
    action: "",
    deadline: "",
  };
}

function AssessmentRow({ row }: { row: AssessmentSession }) {
  const user = useAuthStore((state) => state.user);
  const aiStatus = useAiStatus();
  const draftJustification = useDraftJustification();
  const draftRecommendation = useDraftRecommendation();
  const anomalyCheck = useAnomalyCheck();
  const inlineHelp = useInlineHelp();
  const comparativeAnalysis = useComparativeAnalysis();
  const saveSelfAssessment = useSaveSelfAssessment();
  const submitAssessment = useSubmitAssessment();
  const asesorReview = useAsesorReviewAssessment();
  const [draft, setDraft] = useState<Draft>(() => draftFrom(row));
  const [review, setReview] = useState<ReviewDraft>(() => reviewFrom(row));
  const [aiPanel, setAiPanel] = useState<{
    kind: "help" | "compare" | "anomaly" | "draft" | null;
    help?: AiInlineHelp;
    compare?: AiComparativeAnalysisResponse;
    anomaly?: AiAnomalyResponse;
    text?: string;
  }>({ kind: null });

  const editable = row.state === "draft" || row.state === "revision_requested";
  const canUsePicAi = user?.roles.some((role) => role === "pic_bidang" || role === "super_admin") === true;
  const canUseAsesorAi = user?.roles.some((role) => role === "asesor" || role === "super_admin") === true;
  const aiAvailable = aiStatus.data?.available === true;
  const aiDisabledTitle = aiStatus.data?.message ?? "Layanan AI sementara tidak tersedia";
  const asesorAiDisabledTitle = canUseAsesorAi ? aiDisabledTitle : "Butuh role asesor atau super_admin";
  const picAiDisabledTitle = canUsePicAi ? aiDisabledTitle : "Butuh role PIC atau super_admin";
  const savePayload = useMemo(
    () => ({
      id: row.id,
      target: draft.target || null,
      realisasi: draft.realisasi || null,
      catatan_pic: draft.catatan_pic || null,
      link_eviden: draft.link_eviden || null,
      payload: draft.payload,
    }),
    [row.id, draft],
  );
  const autoSaveState = useAssessmentAutoSave(savePayload, editable);

  function updateMl(key: string, patch: Partial<MlPayloadItem>) {
    setDraft((prev) => {
      const current = prev.payload[key];
      const nextLevel = patch.level ?? current.level;
      const nextLock = patch.lock_integer ?? current.lock_integer;
      const value = nextLock ? nextLevel + 0.5 : (patch.value ?? current.value);
      return {
        ...prev,
        payload: {
          ...prev.payload,
          [key]: {
            ...current,
            ...patch,
            level: nextLevel,
            value,
            lock_integer: nextLock,
          },
        },
      };
    });
  }

  function updateRecommendation(index: number, patch: Partial<InlineRecommendationDraft>) {
    setReview((prev) => ({
      ...prev,
      recommendations: prev.recommendations.map((item, i) => (i === index ? { ...item, ...patch } : item)),
    }));
  }

  function updateAction(recommendationIndex: number, actionIndex: number, patch: Partial<InlineActionDraft>) {
    setReview((prev) => ({
      ...prev,
      recommendations: prev.recommendations.map((rec, i) =>
        i === recommendationIndex
          ? {
              ...rec,
              action_items: rec.action_items.map((action, j) => (j === actionIndex ? { ...action, ...patch } : action)),
            }
          : rec,
      ),
    }));
  }

  function addRecommendation() {
    setReview((prev) => ({ ...prev, recommendations: [...prev.recommendations, emptyRecommendationDraft()] }));
  }

  function removeRecommendation(index: number) {
    setReview((prev) => ({
      ...prev,
      recommendations: prev.recommendations.length === 1 ? prev.recommendations : prev.recommendations.filter((_, i) => i !== index),
    }));
  }

  function addAction(recommendationIndex: number) {
    setReview((prev) => ({
      ...prev,
      recommendations: prev.recommendations.map((rec, i) =>
        i === recommendationIndex ? { ...rec, action_items: [...rec.action_items, emptyActionDraft()] } : rec,
      ),
    }));
  }

  function removeAction(recommendationIndex: number, actionIndex: number) {
    setReview((prev) => ({
      ...prev,
      recommendations: prev.recommendations.map((rec, i) =>
        i === recommendationIndex && rec.action_items.length > 1
          ? { ...rec, action_items: rec.action_items.filter((_, j) => j !== actionIndex) }
          : rec,
      ),
    }));
  }

  const inlineRecommendations = review.recommendations
    .map((rec) => ({
      source_assessment_id: row.id,
      target_periode_id: row.periode_id,
      severity: rec.severity,
      deskripsi: rec.rekomendasi.trim(),
      action_items: rec.action_items
        .filter((item) => item.action.trim().length >= 1)
        .map((item) => ({
          action: item.action.trim(),
          deadline: item.deadline || null,
          owner_user_id: null,
        })),
    }))
    .filter((rec) => rec.deskripsi.length >= 10 && rec.action_items.length >= 1);
  const reviewPayloadRecommendations = inlineRecommendations.length > 0 ? inlineRecommendations : null;

  async function handleDraftJustification() {
    const result = await draftJustification.mutateAsync({
      assessment_session_id: row.id,
      user_note: draft.catatan_pic || null,
    });
    setDraft((prev) => ({ ...prev, catatan_pic: result.text }));
    setAiPanel({ kind: "draft", text: result.text });
  }

  async function handleInlineHelp() {
    if (!row.indikator?.id) return;
    const result = await inlineHelp.mutateAsync(row.indikator.id);
    setAiPanel({ kind: "help", help: result });
  }

  async function handleComparativeAnalysis() {
    const result = await comparativeAnalysis.mutateAsync({ assessment_session_id: row.id });
    setAiPanel({ kind: "compare", compare: result });
  }

  async function handleAnomalyCheck() {
    const result = await anomalyCheck.mutateAsync({ assessment_session_id: row.id });
    setAiPanel({ kind: "anomaly", anomaly: result });
  }

  async function handleDraftRecommendation() {
    const result = await draftRecommendation.mutateAsync({ assessment_session_id: row.id });
    setReview((prev) => ({
      ...prev,
      recommendations: [
        {
          severity: result.structured.severity,
          rekomendasi: result.structured.deskripsi,
          action_items: result.structured.action_items.map((item) => ({
            action: item.action,
            deadline: item.deadline ?? "",
          })),
        },
      ],
    }));
    setAiPanel({ kind: "draft", text: result.structured.target_outcome });
  }

  return (
    <tr style={{ borderTop: "1px solid var(--sk-bevel-dark)" }}>
      <td style={{ padding: "0.5rem" }}>
        <SkBadge tone={statusTone(row.state)}>{row.state}</SkBadge>
      </td>
      <td style={{ padding: "0.5rem", fontFamily: "var(--sk-font-mono)", color: "var(--sk-text-mid)" }}>
        {row.id.slice(0, 8)}
        {row.indikator && (
          <div style={{ fontFamily: "var(--sk-font-body)", color: "var(--sk-text-hi)", marginTop: "0.25rem" }}>
            {row.indikator.kode} · {row.indikator.nama}
          </div>
        )}
      </td>
      <td style={{ padding: "0.5rem" }}>{row.bidang_id ? row.bidang_id.slice(0, 8) : "aggregate"}</td>
      <td style={{ padding: "0.5rem" }}>{fmt(row.target)}</td>
      <td style={{ padding: "0.5rem" }}>{fmt(row.realisasi)}</td>
      <td style={{ padding: "0.5rem" }}>{fmt(row.nilai_final ?? row.nilai)}</td>
      <td style={{ padding: "0.5rem" }}>{new Date(row.updated_at).toLocaleString("id-ID")}</td>
      <td style={{ padding: "0.5rem" }}>
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", marginBottom: "0.55rem" }}>
          <SkBadge tone={aiAvailable ? "success" : "warning"}>AI {aiStatus.data?.mode ?? "loading"}</SkBadge>
          <SkButton variant="secondary" disabled={!aiAvailable || !row.indikator?.id || inlineHelp.isPending} title={aiAvailable ? "Inline help indikator" : aiDisabledTitle} onClick={handleInlineHelp}>
            AI Help
          </SkButton>
          <SkButton variant="secondary" disabled={!aiAvailable || comparativeAnalysis.isPending} title={aiAvailable ? "Bandingkan dengan periode sebelumnya" : aiDisabledTitle} onClick={handleComparativeAnalysis}>
            Bandingkan
          </SkButton>
          <SkButton variant="secondary" disabled={!canUseAsesorAi || !aiAvailable || anomalyCheck.isPending} title={canUseAsesorAi && aiAvailable ? "Cek anomali" : asesorAiDisabledTitle} onClick={handleAnomalyCheck}>
            Cek Anomali
          </SkButton>
        </div>
        {aiPanel.kind && (
          <SkPanel inset style={{ marginBottom: "0.7rem", minWidth: 420 }}>
            {aiPanel.kind === "help" && aiPanel.help && (
              <div style={{ display: "grid", gap: "0.35rem" }}>
                <strong>AI Inline Help</strong>
                <span>{aiPanel.help.apa_itu}</span>
                <span><b>Formula:</b> {aiPanel.help.formula_explanation}</span>
                <span><b>Best practice:</b> {aiPanel.help.best_practice}</span>
                <span><b>Pitfall:</b> {aiPanel.help.common_pitfalls}</span>
              </div>
            )}
            {aiPanel.kind === "compare" && aiPanel.compare && (
              <div style={{ display: "grid", gap: "0.35rem" }}>
                <strong>Comparative Analysis</strong>
                <span>{aiPanel.compare.text}</span>
                <span style={{ fontFamily: "var(--sk-font-mono)", color: "var(--sk-text-mid)" }}>
                  {aiPanel.compare.trend.map((point) => `${point.periode}: ${point.score.toFixed(2)}`).join(" | ")}
                </span>
              </div>
            )}
            {aiPanel.kind === "anomaly" && aiPanel.anomaly && (
              <div style={{ display: "grid", gap: "0.35rem" }}>
                <strong>Anomaly: {aiPanel.anomaly.classification} ({aiPanel.anomaly.risk_score})</strong>
                {aiPanel.anomaly.reasons.map((reason) => <span key={reason}>{reason}</span>)}
              </div>
            )}
            {aiPanel.kind === "draft" && aiPanel.text && (
              <div style={{ display: "grid", gap: "0.35rem" }}>
                <strong>AI Draft</strong>
                <span>{aiPanel.text}</span>
              </div>
            )}
          </SkPanel>
        )}
        {editable && (
          <div style={{ display: "grid", gap: "0.65rem", minWidth: 520 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(140px, 1fr))", gap: "0.45rem" }}>
              <SkInput label="Target" placeholder="Target" value={draft.target} onChange={(e) => setDraft((p) => ({ ...p, target: e.target.value }))} />
              <SkInput label="Realisasi" placeholder="Realisasi" value={draft.realisasi} onChange={(e) => setDraft((p) => ({ ...p, realisasi: e.target.value }))} />
              <SkInput label="Catatan PIC" placeholder="Catatan PIC" value={draft.catatan_pic} onChange={(e) => setDraft((p) => ({ ...p, catatan_pic: e.target.value }))} />
              <SkInput label="Link eviden" placeholder="https://..." value={draft.link_eviden} onChange={(e) => setDraft((p) => ({ ...p, link_eviden: e.target.value }))} />
            </div>

            <div style={{ display: "grid", gap: "0.5rem" }}>
              {Object.entries(draft.payload).map(([key, item]) => (
                <div key={key} style={{ display: "grid", gridTemplateColumns: "220px 1fr 84px 54px minmax(160px, 1fr)", gap: "0.5rem", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{item.nama}</div>
                    <div style={{ color: "var(--sk-text-mid)", fontSize: "0.8rem" }}>
                      {item.area} · {item.kode}
                    </div>
                    {item.criteria[`level_${item.level}`] && (
                      <div style={{ color: "var(--sk-text-mid)", fontSize: "0.78rem", marginTop: "0.25rem" }}>
                        {item.criteria[`level_${item.level}`]}
                      </div>
                    )}
                  </div>
                  <SkLevelSelector value={item.level} onChange={(level) => updateMl(key, { level })} />
                  <span style={{ fontFamily: "var(--sk-font-lcd)", color: "var(--sk-lcd-green)" }}>
                    {item.value == null ? "-" : item.value.toFixed(2)}
                  </span>
                  <SkToggle
                    checked={item.tidak_dinilai}
                    label={`${key} tidak dinilai`}
                    onCheckedChange={(checked) => updateMl(key, { tidak_dinilai: checked, value: checked ? null : item.level + 0.5 })}
                  />
                  <SkInput
                    label="Alasan tidak dinilai"
                    placeholder="Alasan tidak dinilai"
                    value={item.tidak_dinilai_reason}
                    disabled={!item.tidak_dinilai}
                    onChange={(e) => updateMl(key, { tidak_dinilai_reason: e.target.value })}
                  />
                  <div style={{ gridColumn: "2 / 4" }}>
                    <SkSlider
                      label={`${key} sub-level`}
                      min={item.level === 0 ? 0 : item.level + 0.01}
                      max={item.level + 1}
                      step={0.01}
                      value={item.value ?? item.level}
                      disabled={item.tidak_dinilai || item.lock_integer}
                      onChange={(e) => updateMl(key, { value: Number(e.currentTarget.value) })}
                    />
                  </div>
                  <SkToggle checked={item.lock_integer} label={`${key} lock integer`} onCheckedChange={(checked) => updateMl(key, { lock_integer: checked })} />
                </div>
              ))}
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
              <SkBadge tone={autoSaveState === "queued" ? "warning" : autoSaveState === "error" ? "danger" : "info"}>
                autosave: {autoSaveState}
              </SkBadge>
              <SkButton variant="secondary" disabled={!canUsePicAi || !aiAvailable || draftJustification.isPending} title={canUsePicAi && aiAvailable ? "Draft justifikasi dari AI" : picAiDisabledTitle} onClick={handleDraftJustification}>
                AI Draft Justifikasi
              </SkButton>
              <SkButton variant="secondary" onClick={() => saveSelfAssessment.mutate(savePayload)}>
                Simpan
              </SkButton>
              <SkButton onClick={() => submitAssessment.mutate(row.id)}>Submit</SkButton>
            </div>
          </div>
        )}

        {row.state === "submitted" && (
          <div style={{ display: "grid", gap: "0.5rem", minWidth: 540 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(140px, 1fr))", gap: "0.45rem" }}>
              <SkInput label="Nilai final override" placeholder="Nilai final" value={review.nilai_final} onChange={(e) => setReview((p) => ({ ...p, nilai_final: e.target.value }))} />
              <SkInput label="Catatan asesor" placeholder="Catatan asesor" value={review.catatan_asesor} onChange={(e) => setReview((p) => ({ ...p, catatan_asesor: e.target.value }))} />
            </div>
            <div style={{ display: "grid", gap: "0.65rem" }}>
              <div>
                <SkButton variant="secondary" disabled={!canUseAsesorAi || !aiAvailable || draftRecommendation.isPending} title={canUseAsesorAi && aiAvailable ? "Draft rekomendasi SMART dari AI" : asesorAiDisabledTitle} onClick={handleDraftRecommendation}>
                  AI Draft Rekomendasi
                </SkButton>
              </div>
              {review.recommendations.map((rec, recIndex) => (
                <div key={recIndex} style={{ display: "grid", gap: "0.45rem", borderTop: "1px solid var(--sk-bevel-dark)", paddingTop: "0.6rem" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "160px minmax(220px, 1fr) auto", gap: "0.45rem", alignItems: "end" }}>
                    <SkSelect
                      label={`Severity rekomendasi ${recIndex + 1}`}
                      value={rec.severity}
                      onChange={(e) => updateRecommendation(recIndex, { severity: e.target.value as InlineRecommendationDraft["severity"] })}
                    >
                      <option value="low">low</option>
                      <option value="medium">medium</option>
                      <option value="high">high</option>
                      <option value="critical">critical</option>
                    </SkSelect>
                    <SkInput
                      label={`Rekomendasi ${recIndex + 1}`}
                      placeholder="Rekomendasi inline"
                      value={rec.rekomendasi}
                      onChange={(e) => updateRecommendation(recIndex, { rekomendasi: e.target.value })}
                    />
                    <SkButton variant="secondary" disabled={review.recommendations.length === 1} onClick={() => removeRecommendation(recIndex)}>
                      Hapus
                    </SkButton>
                  </div>
                  {rec.action_items.map((action, actionIndex) => (
                    <div key={actionIndex} style={{ display: "grid", gridTemplateColumns: "minmax(220px, 1fr) 150px auto", gap: "0.45rem", alignItems: "end" }}>
                      <SkInput
                        label={`Action ${actionIndex + 1}`}
                        placeholder="Action item"
                        value={action.action}
                        onChange={(e) => updateAction(recIndex, actionIndex, { action: e.target.value })}
                      />
                      <SkInput
                        label="Deadline"
                        type="date"
                        value={action.deadline}
                        onChange={(e) => updateAction(recIndex, actionIndex, { deadline: e.target.value })}
                      />
                      <SkButton variant="secondary" disabled={rec.action_items.length === 1} onClick={() => removeAction(recIndex, actionIndex)}>
                        Hapus
                      </SkButton>
                    </div>
                  ))}
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                    <SkButton variant="secondary" onClick={() => addAction(recIndex)}>
                      Tambah Action
                    </SkButton>
                    <SkBadge tone={rec.rekomendasi.trim().length >= 10 && rec.action_items.some((item) => item.action.trim()) ? "success" : "info"}>
                      {rec.action_items.filter((item) => item.action.trim()).length} action
                    </SkBadge>
                  </div>
                </div>
              ))}
              <SkButton variant="secondary" onClick={addRecommendation}>
                Tambah Rekomendasi
              </SkButton>
            </div>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <SkButton
                variant="secondary"
                onClick={() =>
                  asesorReview.mutate({
                    id: row.id,
                    decision: "approve",
                    catatan_asesor: review.catatan_asesor || null,
                    inline_recommendations: reviewPayloadRecommendations,
                  })
                }
              >
                Approve
              </SkButton>
              <SkButton
                variant="secondary"
                onClick={() =>
                  asesorReview.mutate({
                    id: row.id,
                    decision: "request_revision",
                    catatan_asesor: review.catatan_asesor || null,
                    inline_recommendations: reviewPayloadRecommendations,
                  })
                }
              >
                Request Revision
              </SkButton>
              <SkButton
                disabled={review.catatan_asesor.length < 20}
                onClick={() =>
                  asesorReview.mutate({
                    id: row.id,
                    decision: "override",
                    nilai_final: review.nilai_final,
                    catatan_asesor: review.catatan_asesor,
                    inline_recommendations: reviewPayloadRecommendations,
                  })
                }
              >
                Override
              </SkButton>
            </div>
          </div>
        )}
      </td>
    </tr>
  );
}

export default function AssessmentList() {
  const sessions = useAssessmentSessions();
  const rows = sessions.data?.data ?? [];
  const waiting = rows.filter((row) => row.state === "submitted").length;
  const editable = rows.filter((row) => row.state === "draft" || row.state === "revision_requested").length;

  return (
    <main style={{ padding: "1.5rem", display: "grid", gap: "1rem" }}>
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem" }}>
        <SkPanel title="Sesi Assessment">
          <div style={{ fontSize: "2rem", fontFamily: "var(--sk-font-display)", color: "var(--sk-pln-yellow)" }}>
            {sessions.data?.meta.total ?? rows.length}
          </div>
        </SkPanel>
        <SkPanel title="Draft / Revisi">
          <div style={{ fontSize: "2rem", fontFamily: "var(--sk-font-display)" }}>{editable}</div>
        </SkPanel>
        <SkPanel title="Menunggu Asesor">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "2rem", fontFamily: "var(--sk-font-display)" }}>
            <SkLed state={waiting > 0 ? "alert" : "on"} label="review pending" />
            {waiting}
          </div>
        </SkPanel>
      </section>

      <SkPanel title="Assessment Workflow" style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 1160 }}>
          <thead>
            <tr style={{ color: "var(--sk-text-mid)", textAlign: "left" }}>
              <th style={{ padding: "0.5rem" }}>Status</th>
              <th style={{ padding: "0.5rem" }}>Session</th>
              <th style={{ padding: "0.5rem" }}>Bidang</th>
              <th style={{ padding: "0.5rem" }}>Target</th>
              <th style={{ padding: "0.5rem" }}>Realisasi</th>
              <th style={{ padding: "0.5rem" }}>Nilai</th>
              <th style={{ padding: "0.5rem" }}>Update</th>
              <th style={{ padding: "0.5rem" }}>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <AssessmentRow key={row.id} row={row} />
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={8} style={{ padding: "1rem", color: "var(--sk-text-mid)" }}>
                  Belum ada sesi assessment. Admin perlu membuka periode sampai status self_assessment.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </SkPanel>

      <Link to="/dashboard" style={{ textDecoration: "none" }}>
        <SkButton variant="secondary">Kembali ke Dasbor</SkButton>
      </Link>
    </main>
  );
}
