/**
 * PULSE AppShell — top-level layout wrapping every authenticated route.
 *
 * Renders a header (PULSE logotype + heartbeat LED + role badges + logout
 * button) and an `<Outlet />` for the nested route content. Role-aware nav
 * keeps `pic_bidang` / `asesor` / `manajer_unit` / `viewer` from seeing
 * "Master Data" links they can't open anyway.
 *
 * W-01 contract: header uses SkButton / SkLed / SkBadge only — no raw form
 * controls. Semantic structural tags remain.
 */
import { Outlet, useNavigate, Link } from "react-router-dom";
import { useAuthStore } from "@/lib/auth-store";
import { t } from "@/lib/i18n";
import { SkButton, SkLed, SkBadge } from "@/components/skeuomorphic";
import { useNotifications } from "@/lib/phase2-api";

export function AppShell() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const notifications = useNotifications();

  const canSeeMaster =
    user?.roles.includes("super_admin") || user?.roles.includes("admin_unit");
  const canWorkAssessment =
    !!user && user.roles.some((role) => ["super_admin", "pic_bidang", "asesor"].includes(role));
  const unread = (notifications.data?.data ?? []).filter((row) => !row.read_at).length;

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateRows: "auto 1fr",
        background: "var(--sk-surface-0)",
        color: "var(--sk-text-hi)",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          padding: "0.75rem 1.5rem",
          background: "var(--sk-surface-1)",
          borderBottom: "1px solid var(--sk-bevel-dark)",
        }}
      >
        <SkLed state="on" label={t("app.name") + " pulse"} />
        <Link
          to="/dashboard"
          style={{
            fontFamily: "var(--sk-font-display)",
            fontSize: "1.75rem",
            letterSpacing: "0.05em",
            color: "var(--sk-pln-yellow)",
            textDecoration: "none",
          }}
        >
          {t("app.name")}
        </Link>

        <nav style={{ display: "flex", gap: "0.5rem", marginLeft: "1rem", flexWrap: "wrap" }}>
          <Link to="/dashboard" style={{ textDecoration: "none" }}>
            <SkButton variant="ghost" type="button">
              {t("nav.dashboard")}
            </SkButton>
          </Link>
          <Link to="/guide" style={{ textDecoration: "none" }}>
            <SkButton variant="ghost" type="button">
              {t("nav.guide")}
            </SkButton>
          </Link>
          <Link to="/formula-dictionary" style={{ textDecoration: "none" }}>
            <SkButton variant="ghost" type="button">
              {t("nav.formulaDictionary")}
            </SkButton>
          </Link>
          <Link to="/workflow-playbook" style={{ textDecoration: "none" }}>
            <SkButton variant="ghost" type="button">
              {t("nav.workflowPlaybook")}
            </SkButton>
          </Link>
          {canWorkAssessment && (
            <Link to="/assessment" style={{ textDecoration: "none" }}>
              <SkButton variant="ghost" type="button">
                Assessment
              </SkButton>
            </Link>
          )}
          <Link to="/recommendations" style={{ textDecoration: "none" }}>
            <SkButton variant="ghost" type="button">
              Rekomendasi
            </SkButton>
          </Link>
          {canSeeMaster && (
            <>
              <Link to="/periode" style={{ textDecoration: "none" }}>
                <SkButton variant="ghost" type="button">
                  Periode
                </SkButton>
              </Link>
              <Link to="/compliance" style={{ textDecoration: "none" }}>
                <SkButton variant="ghost" type="button">
                  Compliance
                </SkButton>
              </Link>
              <Link to="/audit-logs" style={{ textDecoration: "none" }}>
                <SkButton variant="ghost" type="button">
                  Audit
                </SkButton>
              </Link>
              <Link to="/master/konkin-template/2026" style={{ textDecoration: "none" }}>
                <SkButton variant="ghost" type="button">
                  {t("nav.master")}
                </SkButton>
              </Link>
            </>
          )}
          <Link to="/notifications" style={{ textDecoration: "none" }}>
            <SkButton variant="ghost" type="button">
              Notifikasi {unread > 0 ? `(${unread})` : ""}
            </SkButton>
          </Link>
        </nav>

        <div
          style={{
            marginLeft: "auto",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          {user?.roles.map((role) => (
            <SkBadge key={role} tone="info">
              {role}
            </SkBadge>
          ))}
          <SkButton variant="secondary" type="button" onClick={handleLogout}>
            {t("nav.logout")}
          </SkButton>
        </div>
      </header>

      <Outlet />
    </div>
  );
}
