/**
 * PULSE Master — Bidang list browse (REQ-bidang-master).
 *
 * Phase-1 scope: flat list sorted by kode. Phase-2 will surface the
 * parent_id tree.
 *
 * W-01 contract: SkPanel / SkBadge only — no raw form controls.
 */
import { useQuery } from "@tanstack/react-query";
import { SkPanel, SkBadge } from "@/components/skeuomorphic";
import { api } from "@/lib/api";
import { t } from "@/lib/i18n";

interface BidangPublic {
  id: string;
  kode: string;
  nama: string;
  parent_id: string | null;
}

interface BidangListEnvelope {
  data: BidangPublic[];
  meta?: unknown;
}

export default function BidangList() {
  const query = useQuery({
    queryKey: ["bidang"],
    queryFn: async () => {
      const { data } = await api.get<BidangListEnvelope>("/bidang?page=1&page_size=100");
      return data;
    },
  });

  if (query.isPending) {
    return (
      <SkPanel title={t("master.bidang")} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-text-mid)" }}>{t("common.loading")}</p>
      </SkPanel>
    );
  }

  if (query.isError) {
    return (
      <SkPanel title={t("master.bidang")} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-level-0)" }}>{t("common.error")}</p>
      </SkPanel>
    );
  }

  const rows = [...(query.data?.data ?? [])].sort((a, b) => a.kode.localeCompare(b.kode));

  if (rows.length === 0) {
    return (
      <SkPanel title={t("master.bidang")} style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--sk-text-mid)" }}>{t("common.empty")}</p>
      </SkPanel>
    );
  }

  return (
    <div style={{ display: "grid", gap: "0.5rem" }}>
      <SkPanel title={t("master.bidang")} style={{ padding: "1rem" }}>
        <p style={{ color: "var(--sk-text-mid)", margin: 0 }}>{rows.length} bidang</p>
      </SkPanel>
      {rows.map((row) => (
        <SkPanel
          key={row.id}
          style={{
            padding: "0.75rem 1rem",
            display: "grid",
            gridTemplateColumns: "auto 1fr auto",
            gap: "1rem",
            alignItems: "center",
          }}
        >
          <SkBadge tone="neutral">{row.kode}</SkBadge>
          <span style={{ color: "var(--sk-text-hi)" }}>{row.nama}</span>
          {row.parent_id ? (
            <SkBadge tone="info">sub</SkBadge>
          ) : (
            <SkBadge tone="success">root</SkBadge>
          )}
        </SkPanel>
      ))}
    </div>
  );
}
