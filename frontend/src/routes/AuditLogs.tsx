import { SkBadge, SkPanel } from "@/components/skeuomorphic";
import { useAuditLogs } from "@/lib/phase2-api";

function short(value: string | null) {
  return value ? value.slice(0, 8) : "-";
}

export default function AuditLogs() {
  const auditLogs = useAuditLogs();
  const rows = auditLogs.data?.data ?? [];

  return (
    <main style={{ padding: "1.5rem", display: "grid", gap: "1rem" }}>
      <SkPanel title="Audit Log" style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", minWidth: 1040, borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--sk-text-mid)" }}>
              <th style={{ padding: "0.5rem" }}>Waktu</th>
              <th style={{ padding: "0.5rem" }}>Action</th>
              <th style={{ padding: "0.5rem" }}>Entity</th>
              <th style={{ padding: "0.5rem" }}>User</th>
              <th style={{ padding: "0.5rem" }}>IP</th>
              <th style={{ padding: "0.5rem" }}>Before / After</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} style={{ borderTop: "1px solid var(--sk-bevel-dark)" }}>
                <td style={{ padding: "0.5rem", color: "var(--sk-text-mid)" }}>
                  {new Date(row.created_at).toLocaleString("id-ID")}
                </td>
                <td style={{ padding: "0.5rem", fontFamily: "var(--sk-font-mono)" }}>{row.action}</td>
                <td style={{ padding: "0.5rem" }}>
                  <SkBadge tone="info">{row.entity_type ?? "system"}</SkBadge>
                  <span style={{ marginLeft: "0.4rem", fontFamily: "var(--sk-font-mono)", color: "var(--sk-text-mid)" }}>
                    {short(row.entity_id)}
                  </span>
                </td>
                <td style={{ padding: "0.5rem", fontFamily: "var(--sk-font-mono)" }}>{short(row.user_id)}</td>
                <td style={{ padding: "0.5rem", color: "var(--sk-text-mid)" }}>{row.ip_address ?? "-"}</td>
                <td style={{ padding: "0.5rem" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap", color: "var(--sk-text-mid)", fontSize: "0.75rem" }}>
                      {row.before_data ? JSON.stringify(row.before_data, null, 2) : "-"}
                    </pre>
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap", color: "var(--sk-text-mid)", fontSize: "0.75rem" }}>
                      {row.after_data ? JSON.stringify(row.after_data, null, 2) : "-"}
                    </pre>
                  </div>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} style={{ padding: "1rem", color: "var(--sk-text-mid)" }}>
                  Belum ada audit log.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </SkPanel>
    </main>
  );
}
