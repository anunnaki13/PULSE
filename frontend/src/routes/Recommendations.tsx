import { useState } from "react";
import { SkBadge, SkButton, SkInput, SkPanel, SkSlider } from "@/components/skeuomorphic";
import {
  statusTone,
  useMarkRecommendationCompleted,
  useRecommendations,
  useUpdateRecommendationProgress,
  useVerifyRecommendationClose,
} from "@/lib/phase2-api";

export default function Recommendations() {
  const recommendations = useRecommendations();
  const updateProgress = useUpdateRecommendationProgress();
  const markCompleted = useMarkRecommendationCompleted();
  const verifyClose = useVerifyRecommendationClose();
  const rows = recommendations.data?.data ?? [];
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [closeNotes, setCloseNotes] = useState<Record<string, string>>({});

  return (
    <main style={{ padding: "1.5rem", display: "grid", gap: "1rem" }}>
      <SkPanel title="Recommendation Tracker">
        <div style={{ display: "grid", gap: "0.75rem" }}>
          {rows.map((row) => (
            <article
              key={row.id}
              style={{
                display: "grid",
                gap: "0.5rem",
                padding: "0.75rem",
                borderRadius: 8,
                background: "var(--sk-surface-1)",
                border: "1px solid var(--sk-bevel-dark)",
              }}
            >
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                <SkBadge tone={statusTone(row.status)}>{row.status}</SkBadge>
                <SkBadge tone={row.severity === "critical" || row.severity === "high" ? "danger" : "warning"}>
                  {row.severity}
                </SkBadge>
                <span style={{ marginLeft: "auto", fontFamily: "var(--sk-font-mono)", color: "var(--sk-text-mid)" }}>
                  {row.progress_percent}%
                </span>
              </div>
              <p style={{ margin: 0, color: "var(--sk-text-hi)" }}>{row.deskripsi}</p>
              <div style={{ display: "grid", gridTemplateColumns: "minmax(160px, 1fr) minmax(180px, 2fr)", gap: "0.75rem", alignItems: "center" }}>
                <SkSlider
                  label={`Progress ${row.deskripsi}`}
                  value={row.progress_percent}
                  min={0}
                  max={100}
                  step={5}
                  disabled={row.status === "closed" || row.status === "carried_over"}
                  onChange={(event) =>
                    updateProgress.mutate({ id: row.id, progress_percent: Number(event.currentTarget.value) })
                  }
                />
                <SkInput
                  label="Catatan progress"
                  placeholder="Catatan progress"
                  value={notes[row.id] ?? row.progress_notes ?? ""}
                  onChange={(event) => setNotes((prev) => ({ ...prev, [row.id]: event.target.value }))}
                  onBlur={(event) => updateProgress.mutate({ id: row.id, progress_notes: event.target.value })}
                  disabled={row.status === "closed" || row.status === "carried_over"}
                />
              </div>
              <div style={{ display: "grid", gap: "0.35rem" }}>
                {row.action_items.map((item, index) => (
                  <div key={index} style={{ color: "var(--sk-text-mid)", fontSize: "0.875rem" }}>
                    {index + 1}. {item.action}
                    {item.deadline ? ` - ${item.deadline}` : ""}
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
                <SkButton
                  variant="secondary"
                  disabled={row.status === "pending_review" || row.status === "closed" || row.status === "carried_over"}
                  onClick={() => markCompleted.mutate(row.id)}
                >
                  Mark Completed
                </SkButton>
                {row.status === "pending_review" && (
                  <>
                    <SkInput
                      label="Catatan close asesor"
                      placeholder="Catatan close asesor"
                      value={closeNotes[row.id] ?? ""}
                      onChange={(event) => setCloseNotes((prev) => ({ ...prev, [row.id]: event.target.value }))}
                      style={{ minWidth: 260 }}
                    />
                    <SkButton
                      disabled={!closeNotes[row.id]}
                      onClick={() =>
                        verifyClose.mutate({ id: row.id, asesor_close_notes: closeNotes[row.id] })
                      }
                    >
                      Verify Close
                    </SkButton>
                  </>
                )}
              </div>
            </article>
          ))}
          {rows.length === 0 && <p style={{ margin: 0, color: "var(--sk-text-mid)" }}>Belum ada rekomendasi.</p>}
        </div>
      </SkPanel>
    </main>
  );
}
