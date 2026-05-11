/**
 * PULSE Master — Konkin Template browser.
 *
 * Task 1 minimal stub (so App.tsx's lazy-free import resolves under tsc).
 * Task 2 expands this with the full TanStack Query call + perspektif card
 * grid + W-07 pengurang badge.
 *
 * W-01 contract: SkPanel / SkBadge only — no raw form controls.
 */
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { SkPanel, SkBadge } from "@/components/skeuomorphic";
import { api } from "@/lib/api";
import { t } from "@/lib/i18n";

interface PerspektifPublic {
  id: string;
  kode: string;
  nama: string;
  bobot: string;
  is_pengurang: boolean;
  pengurang_cap: string | null;
  sort_order: number;
}

interface TemplateHeader {
  id: string;
  tahun: number;
  nama: string;
  locked: boolean;
}

interface TemplateListEnvelope {
  data: TemplateHeader[];
  meta?: unknown;
}

interface PerspektifListEnvelope {
  data: PerspektifPublic[];
}

export default function KonkinTemplate() {
  const { tahun } = useParams<{ tahun: string }>();
  const tahunNum = tahun ? Number(tahun) : NaN;

  // Step 1: list templates and pick the one whose tahun matches the URL.
  const listQuery = useQuery({
    queryKey: ["konkin", "templates"],
    queryFn: async () => {
      const { data } = await api.get<TemplateListEnvelope>("/konkin/templates");
      return data;
    },
  });

  const match = listQuery.data?.data.find((tpl) => tpl.tahun === tahunNum);

  // Step 2: load the perspektif rows via the separate endpoint
  // GET /konkin/templates/{id}/perspektif. The template detail endpoint
  // returns only the header (id/tahun/nama/locked); perspektif rows live
  // under a child collection so the lock-validator can paginate.
  const detailQuery = useQuery({
    queryKey: ["konkin", "template", match?.id, "perspektif"],
    queryFn: async () => {
      const { data } = await api.get<PerspektifListEnvelope>(
        `/konkin/templates/${match!.id}/perspektif`,
      );
      return data;
    },
    enabled: !!match,
  });

  if (listQuery.isPending || detailQuery.isPending) {
    return (
      <SkPanel title={t("master.konkin")} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-text-mid)" }}>{t("common.loading")}</p>
      </SkPanel>
    );
  }

  if (listQuery.isError || detailQuery.isError) {
    return (
      <SkPanel title={t("master.konkin")} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-level-0)" }}>{t("common.error")}</p>
      </SkPanel>
    );
  }

  if (!match || !detailQuery.data) {
    return (
      <SkPanel title={t("master.konkin")} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-text-mid)" }}>{t("common.empty")}</p>
      </SkPanel>
    );
  }

  const perspektif = [...(detailQuery.data?.data ?? [])].sort(
    (a, b) => a.sort_order - b.sort_order,
  );

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <SkPanel title={`${t("master.konkin")} — ${match.nama}`} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-text-mid)", margin: 0 }}>
          Tahun {match.tahun} · {match.locked ? "Locked" : "Draft"} · {perspektif.length} perspektif
        </p>
      </SkPanel>

      {perspektif.map((p) => (
        <SkPanel
          key={p.id}
          style={{
            padding: "1rem",
            display: "grid",
            gridTemplateColumns: "auto 1fr auto",
            gap: "1rem",
            alignItems: "center",
          }}
        >
          <span
            style={{
              fontFamily: "var(--sk-font-display)",
              fontSize: "1.5rem",
              color: "var(--sk-pln-yellow)",
              minWidth: "3rem",
            }}
          >
            {p.kode}
          </span>
          <div>
            <h3 style={{ margin: 0, fontSize: "1rem", color: "var(--sk-text-hi)" }}>{p.nama}</h3>
            <p style={{ margin: "0.25rem 0 0", color: "var(--sk-text-mid)", fontSize: "0.875rem" }}>
              Bobot: {p.bobot}
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            {p.is_pengurang ? (
              <SkBadge tone="warning" data-testid={`pengurang-${p.kode}`}>
                pengurang max -{p.pengurang_cap ?? "0"}
              </SkBadge>
            ) : (
              <SkBadge tone="success">penambah</SkBadge>
            )}
          </div>
        </SkPanel>
      ))}
    </div>
  );
}
