/**
 * PULSE Master — ML Stream rubric tree (REQ-dynamic-ml-schema).
 *
 * Renders `ml_stream.structure` JSONB as a collapsible tree
 * (areas → sub_areas → criteria L0..L4). Phase-1 uses native
 * `<details><summary>` for accessibility-friendly collapse without a tree
 * widget dependency. Phase-2/6 may switch to a richer component.
 *
 * When no `id` param is present (operator hits /master/stream-ml without an
 * id), this screen lists all streams and links to each. With an id, it
 * loads the full detail and renders the tree.
 *
 * W-01 contract: SkPanel / SkBadge only — no raw form controls.
 */
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { SkPanel, SkBadge } from "@/components/skeuomorphic";
import { api } from "@/lib/api";
import { t } from "@/lib/i18n";

interface MlStreamSummary {
  id: string;
  kode: string;
  nama: string;
  version: string;
}

interface MlStreamDetail extends MlStreamSummary {
  structure: {
    areas?: Array<{
      kode?: string;
      nama?: string;
      sub_areas?: Array<{
        kode?: string;
        nama?: string;
        criteria?: {
          level_0?: string;
          level_1?: string;
          level_2?: string;
          level_3?: string;
          level_4?: string;
        };
      }>;
    }>;
  };
}

interface ListEnvelope {
  data: MlStreamSummary[];
  meta?: unknown;
}

function StreamIndex() {
  const query = useQuery({
    queryKey: ["ml-stream"],
    queryFn: async () => {
      const { data } = await api.get<ListEnvelope>("/ml-stream");
      return data;
    },
  });

  if (query.isPending) {
    return (
      <SkPanel title={t("master.stream")} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-text-mid)" }}>{t("common.loading")}</p>
      </SkPanel>
    );
  }

  if (query.isError) {
    return (
      <SkPanel title={t("master.stream")} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-level-0)" }}>{t("common.error")}</p>
      </SkPanel>
    );
  }

  const rows = query.data?.data ?? [];

  return (
    <div style={{ display: "grid", gap: "0.5rem" }}>
      <SkPanel title={t("master.stream")} style={{ padding: "1rem" }}>
        <p style={{ color: "var(--sk-text-mid)", margin: 0 }}>{rows.length} stream</p>
      </SkPanel>
      {rows.map((s) => (
        <Link
          key={s.id}
          to={`/master/stream-ml/${s.id}`}
          style={{ textDecoration: "none" }}
        >
          <SkPanel
            style={{
              padding: "0.75rem 1rem",
              display: "grid",
              gridTemplateColumns: "auto 1fr auto",
              gap: "1rem",
              alignItems: "center",
            }}
          >
            <SkBadge tone="info">{s.kode}</SkBadge>
            <span style={{ color: "var(--sk-text-hi)" }}>{s.nama}</span>
            <SkBadge tone="neutral">v{s.version}</SkBadge>
          </SkPanel>
        </Link>
      ))}
    </div>
  );
}

function StreamDetail({ id }: { id: string }) {
  const query = useQuery({
    queryKey: ["ml-stream", id],
    queryFn: async () => {
      const { data } = await api.get<MlStreamDetail>(`/ml-stream/${id}`);
      return data;
    },
  });

  if (query.isPending) {
    return (
      <SkPanel title={t("master.stream")} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-text-mid)" }}>{t("common.loading")}</p>
      </SkPanel>
    );
  }

  if (query.isError || !query.data) {
    return (
      <SkPanel title={t("master.stream")} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-level-0)" }}>{t("common.error")}</p>
      </SkPanel>
    );
  }

  const stream = query.data;
  const areas = stream.structure?.areas ?? [];

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <SkPanel title={`${stream.kode} — ${stream.nama}`} style={{ padding: "1rem" }}>
        <p style={{ color: "var(--sk-text-mid)", margin: 0 }}>
          Version {stream.version} · {areas.length} area
        </p>
      </SkPanel>

      {areas.length === 0 ? (
        <SkPanel style={{ padding: "1rem" }}>
          <p style={{ color: "var(--sk-text-mid)", margin: 0 }}>{t("common.empty")}</p>
        </SkPanel>
      ) : (
        areas.map((area, ai) => (
          <SkPanel key={`area-${ai}`} style={{ padding: "1rem" }}>
            <details open>
              <summary
                style={{
                  cursor: "pointer",
                  fontFamily: "var(--sk-font-display)",
                  fontSize: "1.1rem",
                  color: "var(--sk-pln-yellow)",
                }}
              >
                {area.kode ? `${area.kode} — ` : ""}{area.nama ?? "Area"}
              </summary>
              <div style={{ display: "grid", gap: "0.5rem", marginTop: "0.75rem" }}>
                {(area.sub_areas ?? []).map((sub, si) => (
                  <details key={`sub-${ai}-${si}`} style={{ marginLeft: "1rem" }}>
                    <summary
                      style={{
                        cursor: "pointer",
                        color: "var(--sk-text-hi)",
                        fontSize: "0.95rem",
                      }}
                    >
                      {sub.kode ? `${sub.kode} — ` : ""}{sub.nama ?? "Sub-area"}
                    </summary>
                    {sub.criteria && (
                      <div style={{ display: "grid", gap: "0.25rem", marginTop: "0.5rem", marginLeft: "1rem" }}>
                        {(["level_0", "level_1", "level_2", "level_3", "level_4"] as const).map(
                          (lvl, li) => (
                            <div
                              key={lvl}
                              style={{
                                display: "grid",
                                gridTemplateColumns: "auto 1fr",
                                gap: "0.5rem",
                                fontSize: "0.875rem",
                              }}
                            >
                              <SkBadge
                                tone={
                                  li === 0
                                    ? "danger"
                                    : li === 1
                                      ? "warning"
                                      : li === 4
                                        ? "success"
                                        : "neutral"
                                }
                              >
                                L{li}
                              </SkBadge>
                              <span style={{ color: "var(--sk-text-mid)" }}>
                                {sub.criteria?.[lvl] ?? "—"}
                              </span>
                            </div>
                          ),
                        )}
                      </div>
                    )}
                  </details>
                ))}
              </div>
            </details>
          </SkPanel>
        ))
      )}
    </div>
  );
}

export default function MlStreamTree() {
  const { id } = useParams<{ id?: string }>();
  return id ? <StreamDetail id={id} /> : <StreamIndex />;
}
