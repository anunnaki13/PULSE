/**
 * PULSE root component (Plan 07 — Wave 5).
 *
 * Replaces the Plan 04 placeholder route tree with the real auth-gated
 * shell:
 *
 *   /login                                   → Login (public)
 *   /dashboard                               → Dashboard (any authenticated user)
 *   /master/konkin-template/:tahun           → KonkinTemplate (admin gate)
 *   /master/bidang                           → BidangList         (admin gate)
 *   /master/stream-ml                        → MlStreamTree index (admin gate)
 *   /master/stream-ml/:id                    → MlStreamTree detail (admin gate)
 *
 * B-01/B-02: admin gate uses the spec role names verbatim,
 *   `allow=["super_admin","admin_unit"]`. The plan-checker greps App.tsx
 *   for both strings.
 *
 * MotionConfig reducedMotion="user" wraps the Router so every Motion v12
 * component honors prefers-reduced-motion automatically.
 *
 * Auth hydration: on every app boot we call /auth/me. If the httpOnly
 * access_token cookie is still valid, the Zustand store flips to
 * authenticated and the user lands on whichever route they typed. If not,
 * ProtectedRoute bounces them to /login.
 */
import { MotionConfig } from "motion/react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useEffect } from "react";
import { useAuthStore } from "@/lib/auth-store";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import Login from "@/routes/Login";
import Dashboard from "@/routes/Dashboard";
import ComplianceTracker from "@/routes/ComplianceTracker";
import AssessmentList from "@/routes/AssessmentList";
import PeriodeAdmin from "@/routes/PeriodeAdmin";
import Recommendations from "@/routes/Recommendations";
import Notifications from "@/routes/Notifications";
import AuditLogs from "@/routes/AuditLogs";
import MenuGuide from "@/routes/MenuGuide";
import FormulaDictionary from "@/routes/FormulaDictionary";
import { AppShell } from "@/routes/AppShell";
import { MasterLayout } from "@/routes/master/MasterLayout";
import KonkinTemplate from "@/routes/master/KonkinTemplate";
import BidangList from "@/routes/master/BidangList";
import MlStreamTree from "@/routes/master/MlStreamTree";

export default function App() {
  const hydrate = useAuthStore((s) => s.hydrateFromCookie);
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <MotionConfig reducedMotion="user">
      <Routes>
        {/* Public auth surface */}
        <Route path="/login" element={<Login />} />

        {/* All authenticated routes live behind the outer ProtectedRoute. */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/dashboard/executive" element={<Dashboard />} />
            <Route path="/guide" element={<MenuGuide />} />
            <Route path="/formula-dictionary" element={<FormulaDictionary />} />
            <Route path="/assessment" element={<AssessmentList />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route element={<ProtectedRoute allow={["super_admin"]} />}>
              <Route path="/periode" element={<PeriodeAdmin />} />
              <Route path="/audit-logs" element={<AuditLogs />} />
            </Route>
            <Route element={<ProtectedRoute allow={["super_admin", "admin_unit"]} />}>
              <Route path="/compliance" element={<ComplianceTracker />} />
            </Route>

            {/* B-01/B-02: spec role names verbatim. pic_bidang / asesor /
                manajer_unit / viewer hit this gate and get redirected to
                /dashboard (ROADMAP success criterion #2). */}
            <Route element={<ProtectedRoute allow={["super_admin", "admin_unit"]} />}>
              <Route path="/master" element={<MasterLayout />}>
                <Route path="konkin-template/:tahun" element={<KonkinTemplate />} />
                <Route path="bidang" element={<BidangList />} />
                <Route path="stream-ml" element={<MlStreamTree />} />
                <Route path="stream-ml/:id" element={<MlStreamTree />} />
              </Route>
            </Route>
          </Route>
        </Route>

        {/* Fallbacks */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </MotionConfig>
  );
}
