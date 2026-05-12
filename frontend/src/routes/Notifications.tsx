import { SkBadge, SkButton, SkPanel } from "@/components/skeuomorphic";
import { useMarkAllNotificationsRead, useNotifications } from "@/lib/phase2-api";

export default function Notifications() {
  const notifications = useNotifications();
  const markAllRead = useMarkAllNotificationsRead();
  const rows = notifications.data?.data ?? [];
  const unread = rows.filter((row) => !row.read_at).length;

  return (
    <main style={{ padding: "1.5rem", display: "grid", gap: "1rem" }}>
      <SkPanel title="Notifikasi">
        <div style={{ display: "grid", gap: "0.75rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.75rem" }}>
            <SkBadge tone={unread > 0 ? "info" : "neutral"}>{unread} belum dibaca</SkBadge>
            <SkButton
              variant="secondary"
              disabled={unread === 0 || markAllRead.isPending}
              onClick={() => markAllRead.mutate()}
            >
              Tandai Semua Dibaca
            </SkButton>
          </div>
          {rows.map((row) => (
            <article
              key={row.id}
              style={{
                padding: "0.75rem",
                borderRadius: 8,
                background: row.read_at ? "var(--sk-surface-1)" : "var(--sk-surface-2)",
                border: "1px solid var(--sk-bevel-dark)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                <SkBadge tone={row.read_at ? "neutral" : "info"}>{row.type}</SkBadge>
                <strong>{row.title}</strong>
                <span style={{ marginLeft: "auto", color: "var(--sk-text-mid)", fontSize: "0.8rem" }}>
                  {new Date(row.created_at).toLocaleString("id-ID")}
                </span>
              </div>
              <p style={{ margin: "0.5rem 0 0", color: "var(--sk-text-mid)" }}>{row.body}</p>
            </article>
          ))}
          {rows.length === 0 && <p style={{ margin: 0, color: "var(--sk-text-mid)" }}>Belum ada notifikasi.</p>}
        </div>
      </SkPanel>
    </main>
  );
}
