/**
 * PULSE Dashboard landing route (post-login).
 *
 * Phase-1 scope: greeting, role badges, and the heartbeat LED. Real KPI
 * widgets (NKO gauge + perspektif cards) land in Phase 3. For Phase 1 this
 * is just the safe surface every authenticated user lands on.
 *
 * Role-based nav: `admin_unit` + `super_admin` see a "Master Data" CTA. All
 * other roles get the greeting + role badge only.
 *
 * W-01 contract: uses SkPanel / SkBadge / SkLed / SkButton — no raw form
 * controls. Semantic structural tags remain.
 */
import { Link } from "react-router-dom";
import { useAuthStore } from "@/lib/auth-store";
import { t } from "@/lib/i18n";
import { SkPanel, SkBadge, SkLed, SkButton } from "@/components/skeuomorphic";

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);

  const canSeeMaster =
    user?.roles.includes("super_admin") || user?.roles.includes("admin_unit");

  return (
    <main style={{ padding: "2rem", display: "grid", gap: "1rem" }}>
      <SkPanel title={t("nav.dashboard")} style={{ padding: "1.5rem" }}>
        <header
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            marginBottom: "1rem",
          }}
        >
          <SkLed state="on" label={t("app.name") + " pulse"} />
          <h1
            style={{
              fontFamily: "var(--sk-font-display)",
              fontSize: "2rem",
              margin: 0,
              letterSpacing: "0.04em",
              color: "var(--sk-pln-yellow)",
            }}
          >
            {user ? `Halo, ${user.full_name}` : t("app.name")}
          </h1>
        </header>

        <p style={{ color: "var(--sk-text-mid)", margin: 0 }}>{t("app.tagline")}</p>

        {user && user.roles.length > 0 && (
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "0.5rem",
              marginTop: "1rem",
            }}
          >
            {user.roles.map((role) => (
              <SkBadge key={role} tone="info" data-testid={`role-badge-${role}`}>
                {role}
              </SkBadge>
            ))}
          </div>
        )}

        {canSeeMaster && (
          <div style={{ marginTop: "1.5rem" }}>
            {/* W-01: SkButton wrapping a router Link via asChild-style render. */}
            <Link
              to="/master/konkin-template/2026"
              style={{ textDecoration: "none", display: "inline-block" }}
            >
              <SkButton variant="primary" type="button">
                {t("nav.master")}
              </SkButton>
            </Link>
          </div>
        )}

        <p
          style={{
            color: "var(--sk-text-lo)",
            fontStyle: "italic",
            marginTop: "1.5rem",
            marginBottom: 0,
          }}
        >
          {t("common.empty")}
        </p>
      </SkPanel>
    </main>
  );
}
