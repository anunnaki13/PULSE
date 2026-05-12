/**
 * PULSE route guard (REQ-route-guards — frontend half).
 *
 * Two gates in one wrapper:
 *
 * 1. **Auth gate.** If no authenticated user, redirect to `/login`. The
 *    original location is preserved in `state.from` so the login handler can
 *    bounce the user back after a successful login (deep-link friendly).
 *
 * 2. **Role gate.** When `allow=[...]` is passed, the user's `roles` must
 *    intersect the allow list. Otherwise redirect to `/dashboard` per
 *    ROADMAP success criterion #2 ("`pic_bidang` user is redirected away
 *    from /master/*"). The dashboard is the fallback safe surface for any
 *    authenticated role.
 *
 * B-01/B-02: the `allow` arg is typed `Role[]` (the spec-name union), so any
 * caller that tries to pass a legacy name like `"Admin"` is a tsc error.
 */
import { Navigate, Outlet, useLocation } from "react-router-dom";
import type { Role } from "@/types";
import { useAuthStore } from "@/lib/auth-store";

export interface ProtectedRouteProps {
  /** Allow-list of role names. Omit to mean "any authenticated user". */
  allow?: Role[];
  /** Redirect destination when not authenticated. Default: `/login`. */
  redirectTo?: string;
}

export function ProtectedRoute({ allow, redirectTo = "/login" }: ProtectedRouteProps) {
  const { user, isAuthenticated, hasHydrated } = useAuthStore();
  const location = useLocation();

  if (!hasHydrated) {
    return null;
  }

  if (!isAuthenticated || !user) {
    // Auth gate. Preserve the original target so login can bounce back.
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  if (allow && allow.length > 0) {
    // Role gate. The user must hold at least ONE role in the allow list.
    const userRoles = user.roles ?? [];
    const hasMatch = allow.some((r) => userRoles.includes(r));
    if (!hasMatch) {
      // pic_bidang / asesor / manajer_unit / viewer attempting /master/* land here.
      return <Navigate to="/dashboard" replace />;
    }
  }

  return <Outlet />;
}
