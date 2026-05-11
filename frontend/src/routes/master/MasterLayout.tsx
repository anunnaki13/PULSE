/**
 * PULSE Master Data layout.
 *
 * Phase-1 stub created in Task 1 commit so App.tsx's import resolves under
 * tsc strict mode. Task 2 expands this with the left-rail nav tabs (bidang
 * / konkin-template / stream-ml) and the heading-bar.
 *
 * W-01: uses SkPanel / SkButton (no raw form controls).
 */
import { NavLink, Outlet } from "react-router-dom";
import { SkPanel, SkButton } from "@/components/skeuomorphic";
import { t } from "@/lib/i18n";

interface NavItem {
  to: string;
  label: string;
}

const NAV: NavItem[] = [
  { to: "/master/konkin-template/2026", label: "konkin" },
  { to: "/master/bidang", label: "bidang" },
  { to: "/master/stream-ml", label: "stream" },
];

export function MasterLayout() {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "240px 1fr",
        gap: "1rem",
        padding: "1.5rem",
        minHeight: "calc(100vh - 64px)",
      }}
    >
      <SkPanel title={t("nav.master")} style={{ padding: "1rem", alignSelf: "start" }}>
        <nav role="tablist" aria-label={t("nav.master")} style={{ display: "grid", gap: "0.5rem" }}>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              role="tab"
              style={{ textDecoration: "none" }}
            >
              {({ isActive }) => (
                <SkButton
                  type="button"
                  variant={isActive ? "primary" : "secondary"}
                  pressed={isActive}
                  style={{ width: "100%", textAlign: "left" }}
                >
                  {t(`master.${item.label}`)}
                </SkButton>
              )}
            </NavLink>
          ))}
        </nav>
      </SkPanel>
      <section style={{ minWidth: 0 }}>
        <Outlet />
      </section>
    </div>
  );
}
