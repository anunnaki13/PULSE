---
phase: 01-foundation-master-data-auth
plan: 07
type: execute
wave: 5
depends_on: [02, 04, 05, 06]
files_modified:
  - frontend/src/types/index.ts
  - frontend/src/lib/auth-store.ts
  - frontend/src/lib/api.ts
  - frontend/src/routes/ProtectedRoute.tsx
  - frontend/src/routes/Login.tsx
  - frontend/src/routes/Dashboard.tsx
  - frontend/src/routes/master/MasterLayout.tsx
  - frontend/src/routes/master/KonkinTemplate.tsx
  - frontend/src/routes/master/BidangList.tsx
  - frontend/src/routes/master/MlStreamTree.tsx
  - frontend/src/routes/AppShell.tsx
  - frontend/src/App.tsx
  - frontend/src/routes/ProtectedRoute.test.tsx
  - frontend/src/routes/Login.test.tsx
  - backend/app/seed/__init__.py
  - backend/app/seed/__main__.py
  - backend/app/seed/bidang.py
  - backend/app/seed/konkin_2026.py
  - backend/app/seed/admin_user.py
  - backend/app/seed/pilot_rubrics/__init__.py
  - backend/app/seed/pilot_rubrics/outage.py
  - backend/app/seed/pilot_rubrics/smap.py
  - backend/app/seed/pilot_rubrics/eaf.py
  - backend/app/seed/pilot_rubrics/efor.py
  - backend/tests/test_seed_idempotency.py
autonomous: false
requirements:
  - REQ-route-guards
  - REQ-pulse-branding
  - REQ-pulse-heartbeat-animation
  - REQ-bidang-master
  - REQ-konkin-template-crud
  - REQ-dynamic-ml-schema
  - REQ-health-checks
  - REQ-backup-restore
must_haves:
  truths:
    - "An operator can navigate to http://localhost:3399, see the PULSE login screen with the tagline `Denyut Kinerja Pembangkit, Real-Time.` and the animating Pulse Heartbeat LED, enter admin credentials, and arrive at /dashboard"
    - "Login form uses skeuomorphic primitives only (`SkInput`/`SkSelect`/`SkButton`/`SkPanel`/`SkLed`/`SkBadge`) — NO raw `<input>`/`<select>`/`<button>` tags (W-01 contract)"
    - "Master-data screens use skeuomorphic primitives only — same W-01 contract"
    - "All Role identifiers in the frontend (`Role` type union, ProtectedRoute `allow` lists, role-based nav visibility) use the SIX spec names from CONTEXT.md Auth: `super_admin`, `admin_unit`, `pic_bidang`, `asesor`, `manajer_unit`, `viewer` (B-01/B-02)"
    - "`admin_unit` (and `super_admin`) can navigate to `/master/konkin-template/2026` and see the 6 perspektif (I–VI) with Konkin 2026 bobots — VI shows `is_pengurang=true, bobot=0.00, pengurang_cap=10.00` (W-07)"
    - "`admin_unit` can navigate to `/master/bidang` and see the seeded PLTU Tenayan bidang list"
    - "`admin_unit` can navigate to `/master/stream-ml/{id}` and see the Outage / SMAP / EAF / EFOR rubric trees rendered from `ml_stream.structure` JSONB"
    - "`pic_bidang` user logs in and is redirected away from `/master/*` to `/dashboard` (frontend half of REQ-route-guards)"
    - "`docker compose exec pulse-backend python -m app.seed` is idempotent — running it twice produces no duplicates and no errors"
    - "`docker compose up -d --wait` brings all six services to `healthy` state (REQ-health-checks end-to-end)"
    - "The seeded admin user has role `admin_unit` (CONTEXT.md Auth) — ROADMAP success criterion #1 'Admin' = user with role admin_unit"
    - "Restore-from-backup drill succeeds once (REQ-backup-restore acceptance)"
    - "`grep -ri siskonkin` against the entire repo (excluding `.planning/intel/classifications/` and `.git/`) returns zero hits (REQ-pulse-branding final audit)"
  artifacts:
    - path: "frontend/src/types/index.ts"
      provides: "Role TS union with the six spec names (B-01/B-02)"
      contains: "super_admin"
    - path: "frontend/src/routes/Login.tsx"
      provides: "PULSE-branded login page using SkInput/SkButton/SkPanel/SkLed (W-01); no raw <input>/<button>"
      contains: "Denyut Kinerja Pembangkit"
    - path: "frontend/src/routes/ProtectedRoute.tsx"
      provides: "Role-gated route wrapper using spec role names"
      contains: "super_admin"
    - path: "frontend/src/lib/auth-store.ts"
      provides: "Zustand auth state — user, accessToken (in-memory only)"
      contains: "create"
    - path: "backend/app/seed/__main__.py"
      provides: "Idempotent CLI entrypoint: `python -m app.seed`"
      contains: "asyncio.run"
    - path: "backend/app/seed/konkin_2026.py"
      provides: "Six perspektif rows with Konkin 2026 bobots; VI is pengurang (W-07)"
      contains: "is_pengurang=True"
    - path: "backend/app/seed/admin_user.py"
      provides: "Idempotent first admin user creation with role admin_unit (CONTEXT.md Auth)"
      contains: "admin_unit"
  key_links:
    - from: "frontend/src/routes/Login.tsx"
      to: "frontend/src/lib/auth-store.ts"
      via: "login() call on submit"
      pattern: "login\\("
    - from: "frontend/src/routes/Login.tsx"
      to: "frontend/src/components/skeuomorphic/index.ts"
      via: "Barrel import (W-10)"
      pattern: "@/components/skeuomorphic"
    - from: "frontend/src/routes/ProtectedRoute.tsx"
      to: "frontend/src/lib/auth-store.ts"
      via: "useAuthStore for isAuthenticated + roles"
      pattern: "useAuthStore"
    - from: "backend/app/seed/__main__.py"
      to: "backend/app/seed/konkin_2026.py + bidang.py + pilot_rubrics/* + admin_user.py"
      via: "Orchestrator imports and runs each"
      pattern: "konkin_2026"
    - from: "backend/app/seed/admin_user.py"
      to: "Role table 'admin_unit'"
      via: "INSERT user + INSERT user_roles via role lookup"
      pattern: "admin_unit"
---

## Revision History

- **Iteration 1 (initial):** Auth wiring, login page, ProtectedRoute, three browse screens, idempotent seed (bidang + Konkin 2026 + Outage/SMAP/EAF/EFOR + admin user), e2e checkpoint.
- **Iteration 2 (this revision):**
  - **B-01 + B-02 fix:** `Role` TS union switched to the six spec names `super_admin | admin_unit | pic_bidang | asesor | manajer_unit | viewer`. ProtectedRoute `allow=[...]` arrays use these. App.tsx admin gate is `allow=["super_admin","admin_unit"]`. Tests use spec names. Login form uses spec names where it surfaces a role badge.
  - **W-01 fix:** Login.tsx + master screens consume `SkInput`/`SkSelect`/`SkBadge`/`SkButton`/`SkPanel`/`SkLed` from the `@/components/skeuomorphic` barrel (W-10). NO raw `<input>`/`<select>`/`<button>` tags on those screens (verify scans for them).
  - **W-07 fix:** Konkin 2026 seed sets perspektif VI as `is_pengurang=True, bobot=0.00, pengurang_cap=Decimal("10.00")` (CONTEXT.md Data Model). Lock validator (Plan 06) accepts the template because it filters by `is_pengurang=False` when summing bobots.
  - **B-04 fix:** No frontend impact directly. Seed admin_user creates a user without `bidang_id` (it's nullable per Plan 06). Master-data seed runs after Plan 06's migration so `bidang_id` exists in the schema.
  - **B-06 fix:** Verify blocks now run real `pnpm exec vitest` and (in checkpoint) `docker compose exec pulse-backend pytest -x -q`. Seed idempotency proven via a new test file `backend/tests/test_seed_idempotency.py`.
  - **CONTEXT.md "Admin = admin_unit" wording:** ROADMAP success criterion #1 reading reaffirmed; admin_unit user is the one created by `INITIAL_ADMIN_*` env vars. The Phase-1 e2e checkpoint walks the operator through logging in with `admin_unit` credentials.
  - **Wave shift:** This plan moves from wave 4 to **wave 5** because Plan 06 is now wave 4 (W-04 fix).

<objective>
Wire the frontend auth path (login + ProtectedRoute + axios interceptor with refresh-on-401), ship the three master-data browse screens consuming Plan 06's endpoints (using the skeuomorphic barrel — W-01/W-10), deliver the idempotent seed module (`python -m app.seed`) including a `admin_unit` first admin (CONTEXT.md Auth), and gate the phase at a verification checkpoint that proves all six ROADMAP success criteria.

Purpose: This is the integration plan. It closes the loop on REQ-route-guards (frontend half), REQ-pulse-branding (Login screen), REQ-pulse-heartbeat-animation, REQ-bidang-master + REQ-konkin-template-crud + REQ-dynamic-ml-schema, REQ-health-checks + REQ-backup-restore.
Output: Auth-wired frontend, three browse screens (skeuomorphic primitives only), seed module producing the full Konkin 2026 PLTU Tenayan structure (with W-07 pengurang convention) + Outage/SMAP/EAF/EFOR rubrics + admin_unit user, plus a hands-on verification of all phase acceptance criteria.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/01-foundation-master-data-auth/01-CONTEXT.md
@.planning/phases/01-foundation-master-data-auth/01-RESEARCH.md
@.planning/phases/01-foundation-master-data-auth/01-02-SUMMARY.md
@.planning/phases/01-foundation-master-data-auth/01-03-SUMMARY.md
@.planning/phases/01-foundation-master-data-auth/01-04-SUMMARY.md
@.planning/phases/01-foundation-master-data-auth/01-05-SUMMARY.md
@.planning/phases/01-foundation-master-data-auth/01-06-SUMMARY.md

<!-- Source docs needed for accurate seed -->
@01_DOMAIN_MODEL.md

<interfaces>
<!-- Backend contracts (consumed) - from Plan 05/06 SUMMARYs -->
POST /api/v1/auth/login   {email, password}                -> {access_token, refresh_token, user}
GET  /api/v1/auth/me                                       -> UserPublic {id, email, full_name, is_active, bidang_id, roles[]}
POST /api/v1/auth/logout                                   -> 204
POST /api/v1/auth/refresh {refresh_token?}                 -> {access_token, refresh_token}
GET  /api/v1/bidang?page=&page_size=                       -> {data:[BidangPublic], meta}
GET  /api/v1/konkin/templates                              -> {data:[TemplatePublic], meta}
GET  /api/v1/konkin/templates/{id}                         -> TemplateDetail (perspektif + indikator; perspektif rows include is_pengurang + pengurang_cap — W-07)
GET  /api/v1/ml-stream                                     -> {data:[MlStreamPublic], meta}
GET  /api/v1/ml-stream/{id}                                -> MlStreamDetail (with structure JSONB)

<!-- Frontend primitives (consumed via barrel) - from Plan 04 SUMMARY -->
@/components/skeuomorphic: SkLed, SkButton, SkPanel, SkInput, SkSelect, SkBadge   (W-01 + W-10)
@/lib/i18n: t(key)
@/lib/api: axios instance with refresh-on-401 interceptor
@/lib/query-client: TanStack Query client

<!-- Role TS union (B-01/B-02) -->
type Role = "super_admin" | "admin_unit" | "pic_bidang" | "asesor" | "manajer_unit" | "viewer";
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Frontend types + auth wiring + Login (skeuomorphic primitives only) + ProtectedRoute (six spec roles) + AppShell + tests</name>
  <files>
    frontend/src/types/index.ts,
    frontend/src/lib/auth-store.ts,
    frontend/src/lib/api.ts,
    frontend/src/routes/ProtectedRoute.tsx,
    frontend/src/routes/Login.tsx,
    frontend/src/routes/Dashboard.tsx,
    frontend/src/routes/AppShell.tsx,
    frontend/src/App.tsx,
    frontend/src/routes/ProtectedRoute.test.tsx,
    frontend/src/routes/Login.test.tsx
  </files>
  <action>
    1. `frontend/src/types/index.ts` — **B-01/B-02 spec role union**:
       ```ts
       export type Role =
         | "super_admin"
         | "admin_unit"
         | "pic_bidang"
         | "asesor"
         | "manajer_unit"
         | "viewer";

       export interface UserPublic {
         id: string;
         email: string;
         full_name: string;
         is_active: boolean;
         bidang_id: string | null;
         roles: Role[];
       }
       ```
       The roles list maps 1-1 to the seeded `roles.name` rows in Plan 05's 0002 migration.

    2. `frontend/src/lib/auth-store.ts` — Zustand store; tokens kept ONLY in memory:
       ```ts
       import { create } from "zustand";
       import type { UserPublic } from "@/types";
       import { api } from "./api";

       interface AuthState {
         user: UserPublic | null;
         accessToken: string | null;
         isAuthenticated: boolean;
         login(email: string, password: string): Promise<void>;
         logout(): Promise<void>;
         hydrateFromCookie(): Promise<void>;
         setSession(user: UserPublic, accessToken: string): void;
       }

       export const useAuthStore = create<AuthState>((set) => ({
         user: null,
         accessToken: null,
         isAuthenticated: false,
         setSession: (user, accessToken) => set({ user, accessToken, isAuthenticated: true }),
         async login(email, password) {
           const { data } = await api.post("/auth/login", { email, password });
           set({ user: data.user, accessToken: data.access_token, isAuthenticated: true });
           api.defaults.headers.common.Authorization = `Bearer ${data.access_token}`;
         },
         async logout() {
           try { await api.post("/auth/logout"); } catch {}
           delete api.defaults.headers.common.Authorization;
           set({ user: null, accessToken: null, isAuthenticated: false });
         },
         async hydrateFromCookie() {
           try {
             const { data } = await api.get("/auth/me");
             set({ user: data, isAuthenticated: true });
           } catch { /* not authenticated; stay logged out */ }
         },
       }));
       ```

    3. Update `frontend/src/lib/api.ts` (extension of Plan 04's file): wire CSRF echo. Read `csrf_token` cookie on every mutating request and set `X-CSRF-Token` header. Add request interceptor:
       ```ts
       function getCookie(name: string): string | null {
         const m = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
         return m ? decodeURIComponent(m[1]) : null;
       }
       api.interceptors.request.use((cfg) => {
         if (["post","put","patch","delete"].includes((cfg.method || "").toLowerCase())) {
           const csrf = getCookie("csrf_token");
           if (csrf) cfg.headers["X-CSRF-Token"] = csrf;
         }
         return cfg;
       });
       ```
       This satisfies B-07 from the frontend side (every mutating request — including admin import-from-excel — sends the CSRF header).

    4. `frontend/src/routes/ProtectedRoute.tsx` — uses spec role names:
       ```tsx
       import { Navigate, Outlet, useLocation } from "react-router-dom";
       import { useAuthStore } from "@/lib/auth-store";
       import type { Role } from "@/types";

       interface Props { allow?: Role[]; redirectTo?: string; }

       export function ProtectedRoute({ allow, redirectTo = "/login" }: Props) {
         const { user, isAuthenticated } = useAuthStore();
         const location = useLocation();
         if (!isAuthenticated) {
           return <Navigate to={redirectTo} state={{ from: location }} replace />;
         }
         if (allow && !allow.some((r) => user?.roles.includes(r))) {
           // pic_bidang redirected to /dashboard per ROADMAP success criterion #2
           return <Navigate to="/dashboard" replace />;
         }
         return <Outlet />;
       }
       ```

    5. `frontend/src/routes/Login.tsx` — **W-01 contract: only skeuomorphic primitives, no raw <input>/<button>/<select>**:
       ```tsx
       import { useForm } from "react-hook-form";
       import { z } from "zod";
       import { zodResolver } from "@hookform/resolvers/zod";
       import { useNavigate, useLocation } from "react-router-dom";
       import { toast } from "sonner";
       import { useAuthStore } from "@/lib/auth-store";
       import { t } from "@/lib/i18n";
       import { SkLed, SkButton, SkPanel, SkInput } from "@/components/skeuomorphic";

       const Schema = z.object({
         email: z.string().email(),
         password: z.string().min(1),
       });
       type Form = z.infer<typeof Schema>;

       export default function Login() {
         const navigate = useNavigate(); const location = useLocation();
         const login = useAuthStore((s) => s.login);
         const { register, handleSubmit, formState: { errors, isSubmitting } } =
           useForm<Form>({ resolver: zodResolver(Schema) });

         const onSubmit = async (data: Form) => {
           try {
             await login(data.email, data.password);
             const to = (location.state as any)?.from?.pathname || "/dashboard";
             navigate(to, { replace: true });
           } catch {
             toast.error(t("login.wrong"));
           }
         };

         return (
           <main style={{ display: "grid", placeItems: "center", height: "100vh" }}>
             <SkPanel inset title={t("login.title")}>
               <header style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                 <SkLed state="on" label={t("app.name") + " heartbeat"} />
                 <h1 style={{ fontFamily: "var(--sk-font-display)", fontSize: "3rem", margin: 0, letterSpacing: "0.05em" }}>
                   {t("app.name")}
                 </h1>
               </header>
               <p style={{ color: "var(--sk-text-mid)", marginTop: 0 }}>{t("app.tagline")}</p>
               <form onSubmit={handleSubmit(onSubmit)} style={{ display: "grid", gap: "0.75rem" }}>
                 <label style={{ display: "grid", gap: "0.25rem" }}>
                   <span>{t("login.username")}</span>
                   <SkInput type="email" autoComplete="email" invalid={!!errors.email} {...register("email")} />
                   {errors.email && <span role="alert" style={{ color: "var(--sk-level-0)" }}>{errors.email.message}</span>}
                 </label>
                 <label style={{ display: "grid", gap: "0.25rem" }}>
                   <span>{t("login.password")}</span>
                   <SkInput type="password" autoComplete="current-password" invalid={!!errors.password} {...register("password")} />
                   {errors.password && <span role="alert" style={{ color: "var(--sk-level-0)" }}>{errors.password.message}</span>}
                 </label>
                 <SkButton type="submit" variant="primary" disabled={isSubmitting}>
                   {isSubmitting ? t("common.loading") : t("login.submit")}
                 </SkButton>
               </form>
             </SkPanel>
           </main>
         );
       }
       ```
       Note: `<form>`, `<header>`, `<label>`, `<span>`, `<p>`, `<h1>`, `<main>` are still used (semantic structure). The W-01 contract bans only **form-control HTML primitives** that have a skeuomorphic equivalent: `<input>`, `<select>`, `<textarea>`, `<button>`. Use `SkInput` / `SkSelect` / `SkButton` instead.

    6. `frontend/src/routes/Dashboard.tsx` — landing for any authenticated user. Phase 1 contents: greeting (`Halo, {user.full_name}`), nav links visible based on role (admin_unit/super_admin sees Master Data link), an `SkLed state="on"`, role displayed via `SkBadge`, and `t("common.empty")` placeholder. Use only skeuomorphic primitives where applicable.

    7. `frontend/src/routes/AppShell.tsx` — top-level layout with header (PULSE logotype + heartbeat LED + nav `SkButton`s + logout `SkButton`), `<Outlet />` for nested routes. Role badges rendered via `SkBadge` (e.g. `<SkBadge tone="info">admin_unit</SkBadge>`).

    8. **Update `frontend/src/App.tsx`** — replace the Wave-2 placeholder route tree:
       ```tsx
       import { MotionConfig } from "motion/react";
       import { Routes, Route, Navigate } from "react-router-dom";
       import { useEffect } from "react";
       import { useAuthStore } from "@/lib/auth-store";
       import { ProtectedRoute } from "@/routes/ProtectedRoute";
       import Login from "@/routes/Login";
       import Dashboard from "@/routes/Dashboard";
       import { AppShell } from "@/routes/AppShell";
       import KonkinTemplate from "@/routes/master/KonkinTemplate";
       import BidangList from "@/routes/master/BidangList";
       import MlStreamTree from "@/routes/master/MlStreamTree";
       import { MasterLayout } from "@/routes/master/MasterLayout";

       export default function App() {
         const hydrate = useAuthStore((s) => s.hydrateFromCookie);
         useEffect(() => { hydrate(); }, [hydrate]);

         return (
           <MotionConfig reducedMotion="user">
             <Routes>
               <Route path="/login" element={<Login />} />
               <Route element={<ProtectedRoute />}>
                 <Route element={<AppShell />}>
                   <Route path="/dashboard" element={<Dashboard />} />
                   {/* B-01/B-02: spec role names verbatim */}
                   <Route element={<ProtectedRoute allow={["super_admin","admin_unit"]} />}>
                     <Route path="/master" element={<MasterLayout />}>
                       <Route path="konkin-template/:tahun" element={<KonkinTemplate />} />
                       <Route path="bidang" element={<BidangList />} />
                       <Route path="stream-ml/:id" element={<MlStreamTree />} />
                     </Route>
                   </Route>
                 </Route>
               </Route>
               <Route path="/" element={<Navigate to="/dashboard" replace />} />
               <Route path="*" element={<Navigate to="/dashboard" replace />} />
             </Routes>
           </MotionConfig>
         );
       }
       ```

    9. `frontend/src/routes/ProtectedRoute.test.tsx` — covers REQ-route-guards frontend half, using spec role names:
       - unauthenticated → redirected to /login
       - `pic_bidang` user navigating to /master/* → redirected to /dashboard
       - `admin_unit` user navigating to /master/* → renders child Outlet
       - `super_admin` user navigating to /master/* → renders child Outlet
       - `manajer_unit` user navigating to /master/* → redirected to /dashboard
       Use `MemoryRouter` and zustand store reset between tests.

    10. `frontend/src/routes/Login.test.tsx` — covers REQ-pulse-branding + REQ-pulse-heartbeat-animation + W-01:
        - Renders the PULSE brand string
        - Renders the BI tagline
        - Renders a `[data-state="on"]` SkLed (heartbeat)
        - Wrong password shows the `t("login.wrong")` toast
        - **W-01 audit**: assert that the rendered Login DOM contains zero `<input data-sk!=...>` and zero `<button>` elements that are NOT `data-sk` adorned (i.e., every form control is a skeuomorphic primitive):
          ```tsx
          it("W-01: Login uses only skeuomorphic primitives for form controls", () => {
            const { container } = render(<Login />, { wrapper: TestWrapper });
            // Every native input / button rendered by the page must come from Sk* primitives.
            container.querySelectorAll("input").forEach((el) => {
              expect(el).toHaveAttribute("data-sk", "input");
            });
            container.querySelectorAll("button").forEach((el) => {
              expect(el.getAttribute("data-sk")).toMatch(/button/);
            });
          });
          ```
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        # B-01/B-02: spec roles in TS
        $types = Get-Content 'frontend/src/types/index.ts' -Raw;
        foreach ($r in 'super_admin','admin_unit','pic_bidang','asesor','manajer_unit','viewer') {
          if ($types -notmatch $r) { Write-Output ('B-01/B-02 missing role in types: ' + $r); exit 1 }
        };
        # No legacy capitalized 'Admin' / 'PIC' / 'Asesor' as Role identifiers in App.tsx ProtectedRoute allow lists
        $app = Get-Content 'frontend/src/App.tsx' -Raw;
        if ($app -match 'allow=\\[\"Admin\"' -or $app -match 'allow=\\[\"PIC\"') { Write-Output 'legacy role names in App.tsx allow lists'; exit 2 };
        if ($app -notmatch 'super_admin') { exit 3 };
        if ($app -notmatch 'admin_unit')  { exit 4 };
        # W-01: Login imports from barrel and uses SkInput/SkButton/SkPanel/SkLed
        $login = Get-Content 'frontend/src/routes/Login.tsx' -Raw;
        if ($login -notmatch '@/components/skeuomorphic') { Write-Output 'W-10: Login must import via barrel'; exit 5 };
        foreach ($prim in 'SkInput','SkButton','SkPanel','SkLed') {
          if ($login -notmatch $prim) { Write-Output ('W-01: Login must use ' + $prim); exit 6 }
        };
        # W-01 source-level audit: no raw <input> / <button> / <select> tags in Login.tsx (only Sk* primitives)
        # Strip JS comments and string literals before scanning to avoid false positives.
        $loginNoComments = $login -replace '/\*[\s\S]*?\*/','' -replace '//.*',''
        if ($loginNoComments -match '<input\\b') { Write-Output 'W-01 violation: raw <input> in Login.tsx'; exit 7 };
        if ($loginNoComments -match '<button\\b') { Write-Output 'W-01 violation: raw <button> in Login.tsx'; exit 8 };
        if ($loginNoComments -match '<select\\b') { Write-Output 'W-01 violation: raw <select> in Login.tsx'; exit 9 };
        # ProtectedRoute uses Role type
        $pr = Get-Content 'frontend/src/routes/ProtectedRoute.tsx' -Raw;
        if ($pr -notmatch 'useAuthStore')   { exit 10 };
        if ($pr -notmatch '/dashboard')     { exit 11 };
        if ($pr -notmatch 'Role') { exit 12 };
        # Auth store must keep tokens in memory only (no localStorage)
        $auth = Get-Content 'frontend/src/lib/auth-store.ts' -Raw;
        if ($auth -match 'localStorage' -or $auth -match 'sessionStorage') { Write-Output 'tokens must stay in memory'; exit 13 };
        if ($auth -notmatch 'hydrateFromCookie') { exit 14 };
        $api = Get-Content 'frontend/src/lib/api.ts' -Raw;
        if ($api -notmatch 'X-CSRF-Token')  { exit 15 };
        # B-06: real vitest run
        Push-Location frontend
        pnpm exec vitest --run --reporter=basic src/routes 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Output 'vitest failed'; exit 16 };
        pnpm exec tsc -b --noEmit 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 17 };
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Role TS union has six spec names; App.tsx admin gate uses ["super_admin","admin_unit"]; Login renders with PULSE brand + tagline + heartbeat LED + skeuomorphic primitives only (no raw input/button/select — W-01); auth store tokens in-memory; axios echoes CSRF; vitest + tsc green.
  </done>
</task>

<task type="auto">
  <name>Task 2: Master-data browse UI (skeuomorphic-only) + idempotent seed (bidang + Konkin 2026 with W-07 pengurang VI + Outage/SMAP/EAF/EFOR + admin_unit user) + seed idempotency test</name>
  <files>
    frontend/src/routes/master/MasterLayout.tsx,
    frontend/src/routes/master/KonkinTemplate.tsx,
    frontend/src/routes/master/BidangList.tsx,
    frontend/src/routes/master/MlStreamTree.tsx,
    backend/app/seed/__init__.py,
    backend/app/seed/__main__.py,
    backend/app/seed/bidang.py,
    backend/app/seed/konkin_2026.py,
    backend/app/seed/admin_user.py,
    backend/app/seed/pilot_rubrics/__init__.py,
    backend/app/seed/pilot_rubrics/outage.py,
    backend/app/seed/pilot_rubrics/smap.py,
    backend/app/seed/pilot_rubrics/eaf.py,
    backend/app/seed/pilot_rubrics/efor.py,
    backend/tests/test_seed_idempotency.py
  </files>
  <action>
    Frontend browse (3 screens) — **W-01 contract: skeuomorphic primitives only for form controls**:

    1. `MasterLayout.tsx` — left-rail nav: bidang / konkin-template / stream-ml; <Outlet /> on right. Tablist uses `SkButton` items with arrow-key navigation.

    2. `KonkinTemplate.tsx` — `useParams<{tahun: string}>()`; `useQuery(['konkin','templates'], () => api.get('/konkin/templates'))`; pick the template whose `tahun` matches the URL; render six perspektif rows as `<SkPanel>` cards. Each card shows kode, nama, bobot, and a `<SkBadge tone="warning">pengurang max -{pengurang_cap}</SkBadge>` if `is_pengurang === true` (W-07 surface). Drill-down: clicking a perspektif shows the indikator list.

    3. `BidangList.tsx` — `useQuery(['bidang'], () => api.get('/bidang?page=1&page_size=100'))`; renders the seeded list (flat sorted by kode for Phase 1). Each row uses an `SkPanel` row.

    4. `MlStreamTree.tsx` — `useParams<{id: string}>()`; `useQuery(['ml-stream', id], () => api.get(\`/ml-stream/\${id}\`))`; render `structure.areas[].sub_areas[].criteria.level_0..level_4` tree using `<details><summary>`.

    Backend seed (8 files):

    5. `backend/app/seed/__init__.py` — exposes `async def run_seed()` orchestrator.

    6. `backend/app/seed/__main__.py`:
       ```python
       import asyncio
       from app.seed import run_seed
       def main(): asyncio.run(run_seed())
       if __name__ == "__main__": main()
       ```

    7. `backend/app/seed/bidang.py` — REQ-bidang-master seed list verbatim. Idempotent: `INSERT ... ON CONFLICT (kode) DO NOTHING`.

    8. `backend/app/seed/konkin_2026.py` — **W-07 fix**: creates template `tahun=2026, nama="Konkin 2026 PLTU Tenayan"` then six perspektif rows:
       ```python
       from decimal import Decimal
       PERSPEKTIF_2026 = [
           {"kode": "I",   "nama": "Economic & Social Value",   "bobot": Decimal("46.00"), "is_pengurang": False, "pengurang_cap": None},
           {"kode": "II",  "nama": "Model Business Innovation", "bobot": Decimal("25.00"), "is_pengurang": False, "pengurang_cap": None},
           {"kode": "III", "nama": "Technology Leadership",     "bobot": Decimal("6.00"),  "is_pengurang": False, "pengurang_cap": None},
           {"kode": "IV",  "nama": "Energize Investment",       "bobot": Decimal("8.00"),  "is_pengurang": False, "pengurang_cap": None},
           {"kode": "V",   "nama": "Unleash Talent",            "bobot": Decimal("15.00"), "is_pengurang": False, "pengurang_cap": None},
           # W-07: VI is pengurang. Stored bobot=0.00 to satisfy lock validator (which filters by is_pengurang=False),
           # pengurang_cap=10.00 — Phase-3 NKO calc subtracts up to -10 from gross.
           {"kode": "VI",  "nama": "Compliance",                "bobot": Decimal("0.00"),  "is_pengurang": True,  "pengurang_cap": Decimal("10.00")},
       ]
       # SUM(bobot WHERE is_pengurang=False) = 46+25+6+8+15 = 100.00 ✓
       ```
       Plus indikator seed (sourced from `01_DOMAIN_MODEL.md`). At minimum cover the four pilot indikator (EAF, EFOR, Outage Management, SMAP) so success criterion #5 holds. All inserts guarded by existence check on `(template_id, kode)`.

    9. `backend/app/seed/pilot_rubrics/{outage,smap,eaf,efor}.py` — each creates an `MlStream` row (kode, nama, version="2026.1") and populates `structure` JSONB with the area tree. Source content from `01_DOMAIN_MODEL.md`. Idempotency: skip if MlStream with that kode already exists.

       **Coverage**: Outage and SMAP get at least one area with at least one sub-area with all five levels populated. EAF and EFOR can ship a minimal `{areas: []}` skeleton (KPI form is Phase 2).

    10. `backend/app/seed/admin_user.py` — **CONTEXT.md Auth fix**: idempotent admin with role **`admin_unit`**:
        ```python
        from sqlalchemy import select
        from app.models.user import User
        from app.models.role import Role
        from app.core.security import hash_password
        from app.core.config import settings

        async def seed_admin_user(db) -> None:
            email = settings.INITIAL_ADMIN_EMAIL
            existing = await db.scalar(select(User).where(User.email == email))
            if existing:
                print(f"[seed] admin_unit user already exists: {email}")
                return
            admin_role = await db.scalar(select(Role).where(Role.name == "admin_unit"))
            assert admin_role is not None, "Role 'admin_unit' must be seeded by 0002 migration before seed runs"
            u = User(
                email=email,
                full_name="Administrator Unit",
                password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD.get_secret_value()),
                # bidang_id stays None — admin_unit is unit-scoped but Phase 1 admin spans the whole unit.
            )
            u.roles = [admin_role]
            db.add(u)
            print(f"[seed] created admin_unit user: {email}")
        ```

    Orchestrator in `__init__.py`:
    ```python
    from app.db.session import async_sessionmaker, engine
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def run_seed():
        from .bidang import seed_bidang
        from .konkin_2026 import seed_konkin_2026
        from .pilot_rubrics import seed_pilot_rubrics
        from .admin_user import seed_admin_user
        async with SessionLocal() as db:
            await seed_bidang(db); await db.commit()
            await seed_konkin_2026(db); await db.commit()
            await seed_pilot_rubrics(db); await db.commit()
            await seed_admin_user(db); await db.commit()
            print("[seed] complete")
    ```

    11. `backend/tests/test_seed_idempotency.py` — proves `run_seed()` twice produces identical row counts (B-06):
        ```python
        import pytest
        from sqlalchemy import select, func
        from app.models.bidang import Bidang
        from app.models.user import User
        from app.models.konkin_template import KonkinTemplate
        from app.models.perspektif import Perspektif
        from app.models.ml_stream import MlStream

        @pytest.mark.asyncio
        async def test_seed_runs_idempotently(db_session):
            from app.seed import run_seed
            await run_seed()
            counts1 = {
                "bidang": await db_session.scalar(select(func.count()).select_from(Bidang)),
                "users":  await db_session.scalar(select(func.count()).select_from(User)),
                "templates": await db_session.scalar(select(func.count()).select_from(KonkinTemplate)),
                "perspektif": await db_session.scalar(select(func.count()).select_from(Perspektif)),
                "ml_stream": await db_session.scalar(select(func.count()).select_from(MlStream)),
            }
            await run_seed()
            counts2 = {k: await db_session.scalar(select(func.count()).select_from(t))
                       for k, t in [("bidang", Bidang), ("users", User), ("templates", KonkinTemplate),
                                    ("perspektif", Perspektif), ("ml_stream", MlStream)]}
            assert counts1 == counts2, f"non-idempotent: {counts1} vs {counts2}"

        @pytest.mark.asyncio
        async def test_admin_user_has_admin_unit_role(db_session):
            from app.seed import run_seed
            await run_seed()
            from app.core.config import settings
            user = await db_session.scalar(select(User).where(User.email == settings.INITIAL_ADMIN_EMAIL))
            assert user is not None
            role_names = {r.name for r in user.roles}
            assert "admin_unit" in role_names, f"got roles {role_names}"

        @pytest.mark.asyncio
        async def test_perspektif_VI_is_pengurang(db_session):
            from app.seed import run_seed
            await run_seed()
            v6 = await db_session.scalar(select(Perspektif).where(Perspektif.kode == "VI"))
            assert v6 is not None
            assert v6.is_pengurang is True
            assert v6.bobot == 0  # stored as 0.00 (W-07)
            assert v6.pengurang_cap == 10  # 10.00
        ```
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $files = 'backend/app/seed/__init__.py','backend/app/seed/__main__.py','backend/app/seed/bidang.py','backend/app/seed/konkin_2026.py','backend/app/seed/admin_user.py','backend/app/seed/pilot_rubrics/outage.py','backend/app/seed/pilot_rubrics/smap.py','backend/app/seed/pilot_rubrics/eaf.py','backend/app/seed/pilot_rubrics/efor.py','backend/tests/test_seed_idempotency.py';
        foreach ($f in $files) { if (-not (Test-Path $f)) { Write-Output ('missing: ' + $f); exit 1 } };
        $k = Get-Content 'backend/app/seed/konkin_2026.py' -Raw;
        if ($k -notmatch '46\\.00') { exit 2 };
        if ($k -notmatch '25\\.00') { exit 3 };
        if ($k -notmatch '15\\.00') { exit 4 };
        if ($k -notmatch 'is_pengurang.*True') { Write-Output 'W-07: VI must be is_pengurang=True'; exit 5 };
        if ($k -notmatch 'pengurang_cap.*10') { Write-Output 'W-07: VI must have pengurang_cap=10'; exit 6 };
        # Check non-pengurang sum to 100 by visual: I=46 + II=25 + III=6 + IV=8 + V=15 = 100. The file must contain all five.
        foreach ($v in '\"I\"','\"II\"','\"III\"','\"IV\"','\"V\"','\"VI\"') {
          if ($k -notmatch $v) { Write-Output ('W-07: missing perspektif ' + $v); exit 7 }
        };
        $b = Get-Content 'backend/app/seed/bidang.py' -Raw;
        if ($b -notmatch 'BID_OM_1') { exit 8 };
        if ($b -notmatch 'BID_AMS')  { exit 9 };
        if ($b -notmatch 'ON CONFLICT' -and $b -notmatch 'WHERE.*kode') { Write-Output 'idempotency guard missing'; exit 10 };
        # admin_user must use admin_unit (B-01/B-02 + CONTEXT.md Auth)
        $a = Get-Content 'backend/app/seed/admin_user.py' -Raw;
        if ($a -notmatch 'admin_unit') { Write-Output 'admin_user must use admin_unit role'; exit 11 };
        # No legacy Admin/PIC/Asesor as standalone capitalized strings in admin_user.py
        if ($a -match '\"Admin\"' -and $a -notmatch 'admin_unit') { exit 12 };
        $o = Get-Content 'backend/app/seed/pilot_rubrics/outage.py' -Raw;
        if ($o -notmatch 'OUTAGE')   { exit 13 };
        if ($o -notmatch 'level_4')  { exit 14 };
        # W-01 audit on master screens
        $kt = Get-Content 'frontend/src/routes/master/KonkinTemplate.tsx' -Raw;
        if ($kt -notmatch 'useQuery')  { exit 15 };
        if ($kt -notmatch '@/components/skeuomorphic') { Write-Output 'W-01: master screen must import barrel'; exit 16 };
        $ktNoCom = $kt -replace '/\*[\s\S]*?\*/','' -replace '//.*',''
        if ($ktNoCom -match '<button\\b') { Write-Output 'W-01: raw <button> in KonkinTemplate.tsx'; exit 17 };
        if ($ktNoCom -match '<input\\b')  { Write-Output 'W-01: raw <input> in KonkinTemplate.tsx';  exit 18 };
        $bl = Get-Content 'frontend/src/routes/master/BidangList.tsx' -Raw;
        if ($bl -notmatch 'bidang')    { exit 19 };
        if ($bl -notmatch '@/components/skeuomorphic') { exit 20 };
        $ml = Get-Content 'frontend/src/routes/master/MlStreamTree.tsx' -Raw;
        if ($ml -notmatch 'structure') { exit 21 };
        # B-06: real Python import (seed module must import without errors)
        Push-Location backend
        python -c 'from app.seed import run_seed; from app.seed.bidang import seed_bidang; from app.seed.konkin_2026 import seed_konkin_2026; from app.seed.admin_user import seed_admin_user; from app.seed.pilot_rubrics.outage import seed as out_seed; print(\"seed imports OK\")' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 22 };
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    All seed files exist + import-clean; Konkin 2026 perspektif VI flagged `is_pengurang=True, bobot=0.00, pengurang_cap=10.00` (W-07); other five perspektif sum to 100 when filtered; bidang seed covers PLTU Tenayan list; pilot rubrics include level_0..level_4 for Outage and SMAP; admin user seed uses **admin_unit** role (CONTEXT.md Auth); three browse screens import via barrel and use no raw input/button/select (W-01); seed idempotency test in place.
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 3: Phase 1 end-to-end verification</name>
  <what-built>
    The full Phase 1 stack:
    - Docker Compose six-service infrastructure (Plan 02; backup sidecar uses dcron — W-08)
    - FastAPI backend with auth (six spec roles), master data (W-07 pengurang, B-04 users.bidang_id FK, B-07 CSRF on import-from-excel), and the health endpoint family including admin-only `/health/detail` + `/metrics` (W-02)
    - React 18 frontend with skeuomorphic design system (six primitives + barrel — W-01/W-10), Pulse Heartbeat keyframes (healthy + alert — B-03), login + master browse using only Sk* primitives
    - Seed module producing bidang + Konkin 2026 (W-07 pengurang VI) + Outage/SMAP/EAF/EFOR + **admin_unit** user (CONTEXT.md Auth)
    - Backup sidecar with internal dcron

    This checkpoint walks you through every ROADMAP Phase-1 success criterion and pauses for your confirmation.
  </what-built>
  <how-to-verify>
    Run the following commands and observations in order. Capture output and any anomalies in your reply.

    **Step 0 — Prepare host (one-time):**
    ```powershell
    mkdir C:\var\backups\pulse -Force   # or whichever path you set in .env
    notepad .env
    ```
    Edit .env: fill `JWT_SECRET_KEY` (32+ chars), `POSTGRES_PASSWORD`, `INITIAL_ADMIN_EMAIL` (e.g. admin@pulse.tenayan.local), `INITIAL_ADMIN_PASSWORD`.

    **Step 1 — Bring up the stack:**
    ```powershell
    docker info                       # CONTEXT.md Test Infrastructure preflight
    docker compose build
    docker compose up -d --wait
    docker compose ps
    ```
    Expected: all 6 services with `Status=running (healthy)`.

    **Step 2 — Apply migrations and seed (idempotency proof):**
    ```powershell
    docker compose exec pulse-backend alembic upgrade head
    docker compose exec pulse-backend python -m app.seed
    docker compose exec pulse-backend python -m app.seed   # second run — must be idempotent
    ```
    Expected: first run prints `[seed] complete` with row counts; second run prints the same with all idempotency guards firing.

    **Step 3 — Verify health endpoint family (ROADMAP success #4 + W-02):**
    ```powershell
    Invoke-WebRequest http://localhost:3399/api/v1/health | Select-Object -ExpandProperty Content
    # Expected public response: {"status":"ok","db":"ok","redis":"ok","version":"0.1.0"}

    # /health/detail and /metrics MUST require admin auth (W-02). Anonymously:
    try { Invoke-WebRequest http://localhost:3399/api/v1/health/detail } catch { $_.Exception.Response.StatusCode }
    try { Invoke-WebRequest http://localhost:3399/api/v1/metrics } catch { $_.Exception.Response.StatusCode }
    # Expected: 401 (or 403 if a non-admin token is presented)
    ```

    **Step 4 — Verify branding (ROADMAP success #3):**
    Open `http://localhost:3399` in a browser. Expect:
    - Word **PULSE** in display font
    - Tagline **"Denyut Kinerja Pembangkit, Real-Time."** visible
    - Yellow LED pulses (heartbeat at ~70 BPM = ~857 ms cycle)
    - With OS-level "Reduce Motion" toggled ON, the LED stops animating
    - **B-03**: trigger an alert state (e.g. point a dev tool to set `data-state="alert"` on the LED) — the glow shifts to red and the cadence accelerates

    Then run:
    ```powershell
    Get-ChildItem -Recurse -File -Exclude *.png,*.jpg,*.ico |
      Where-Object { $_.FullName -notmatch '\\\.git\\|\\\.planning\\\\intel\\\\classifications\\|node_modules|dist|build|\\\.venv|__pycache__' } |
      Select-String -SimpleMatch -CaseSensitive:$false 'siskonkin'
    ```
    Expected: ZERO lines.

    **Step 5 — Verify auth round-trip (ROADMAP success #1, "Admin = admin_unit"):**
    Log in via the UI with `${INITIAL_ADMIN_EMAIL}` / `${INITIAL_ADMIN_PASSWORD}`. Expect navigation to `/dashboard`. Then click "Master Data" → "Template Konkin 2026" → URL `/master/konkin-template/2026`. Expect six perspektif rows (I–VI) with bobots populated; **VI shows the pengurang badge** (W-07).

    Verify the seeded user's role:
    ```powershell
    docker compose exec pulse-db psql -U pulse -d pulse -c "
      SELECT u.email, r.name AS role
      FROM users u JOIN user_roles ur ON ur.user_id = u.id JOIN roles r ON r.id = ur.role_id
      WHERE u.email = '$env:INITIAL_ADMIN_EMAIL';
    "
    ```
    Expected: one row with `role = admin_unit`.

    Also verify the role table has all six spec rows:
    ```powershell
    docker compose exec pulse-db psql -U pulse -d pulse -c "SELECT name FROM roles ORDER BY name;"
    # Expected: admin_unit, asesor, manajer_unit, pic_bidang, super_admin, viewer
    ```

    Verify users.bidang_id column exists (B-04):
    ```powershell
    docker compose exec pulse-db psql -U pulse -d pulse -c "\\d users"
    # Expected: column 'bidang_id uuid' present, plus FK constraint 'fk_users_bidang_id'.
    ```

    **Step 6 — Verify role gating (ROADMAP success #2):**
    Create a `pic_bidang` user via SQL inside the container:
    ```powershell
    docker compose exec pulse-db psql -U pulse -d pulse -c "
      INSERT INTO users (id, email, full_name, password_hash, is_active)
      VALUES (uuid_generate_v4(), 'pic@pulse.local', 'PIC Test', crypt('pic-pwd', gen_salt('bf')), true);
      INSERT INTO user_roles SELECT u.id, r.id FROM users u, roles r WHERE u.email='pic@pulse.local' AND r.name='pic_bidang';
    "
    ```
    Then log out, log in as `pic@pulse.local`, attempt to navigate to `/master/konkin-template/2026` — expect redirect to `/dashboard`.

    Repeat with a `manajer_unit` user (also expect redirect away from /master/*).

    **Step 7 — Verify no-upload contract (ROADMAP success #5):**
    ```powershell
    docker compose exec pulse-backend pytest tests/test_no_upload_policy.py -x -v
    ```
    Expected: 2 tests pass; OpenAPI multipart set equals exactly `{/api/v1/konkin/templates/{template_id}/import-from-excel}`.

    Verify the import endpoint requires CSRF (B-07):
    ```powershell
    # Request without X-CSRF-Token (cookie auth) must be rejected
    # (Use the browser network tab during a real import attempt; or an explicit curl/Invoke with cookies.)
    ```

    **Step 8 — Verify backup + restore drill (ROADMAP success #6):**
    ```powershell
    docker compose exec pulse-backup /scripts/backup.sh
    docker compose exec pulse-backup ls -lh /backups
    docker compose exec pulse-db psql -U pulse -d pulse -c "CREATE DATABASE pulse_restore_drill;"
    docker compose exec -e PGDATABASE=pulse_restore_drill pulse-backup /scripts/restore.sh <backup-filename>
    docker compose exec pulse-db psql -U pulse -d pulse_restore_drill -c "SELECT COUNT(*) FROM bidang;"
    docker compose exec pulse-db psql -U pulse -d pulse -c "DROP DATABASE pulse_restore_drill;"
    ```
    Expected: backup file appears in /backups; restore-drill DB has the bidang rows.

    **Step 9 — Verify cron (W-08 dcron):**
    ```powershell
    docker compose exec pulse-backup crond -V 2>&1 | Select-String dcron   # confirms dcron, not busybox-suid
    docker compose exec pulse-backup cat /etc/crontabs/root
    ```
    Expected: dcron present; two crontab lines (02:00 daily backup, 03:00 Sunday rsync).

    **Step 10 — Full test suites (real pytest + vitest — B-06):**
    ```powershell
    docker compose exec pulse-backend pytest -x -q
    docker compose exec pulse-frontend pnpm exec vitest --run --reporter=basic
    ```
    Expected: green across the board.

    Reply with:
    - "phase 1 verified" if every step passed
    - Otherwise, paste the step number + the exact output of the failing command
  </how-to-verify>
  <resume-signal>
    Type "phase 1 verified" (only after all 10 steps green) OR paste the failing step output for `/gsd-plan-phase --gaps` to generate a closure plan.
  </resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Browser → /api/v1/* | Auth-gated; rate-limited |
| Operator → docker compose | Operator is trusted (host-level access) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-07-S-01 | Spoofing | Token in localStorage | mitigate | Auth-store Zustand kept in-memory only; verify rejects any string match on `localStorage` / `sessionStorage`. |
| T-07-T-01 | Tampering | CSRF on cookie-mode endpoints | mitigate | api.ts request interceptor echoes `csrf_token` cookie as `X-CSRF-Token` header on all mutating verbs (POST/PUT/PATCH/DELETE). Backend Plan 06 enforces on all mutating routes including import-from-excel (B-07). |
| T-07-I-01 | Information disclosure | Admin password in .env committed | mitigate | `.gitignore` (Plan 01) excludes `.env`; verify visual check. |
| T-07-E-01 | Elevation | pic_bidang reaches /master/* via direct URL | mitigate | ProtectedRoute role gate redirects to /dashboard; backend also returns 403 via require_role("super_admin","admin_unit") (defense in depth). |
| T-07-E-02 | Elevation | manajer_unit / asesor / viewer reach master CRUD | mitigate | Same gate — only super_admin and admin_unit pass require_role on writes. |
</threat_model>

<verification>
The checkpoint runs every ROADMAP success criterion as a literal shell + browser check, including the new W-02 / W-07 / W-08 / B-03 / B-04 / B-07 evidence steps.
</verification>

<success_criteria>
- All ROADMAP §"Phase 1: Foundation" success criteria 1-6 pass
- `docker compose up -d --wait` reaches healthy on all six services
- Seed is idempotent (two runs produce identical row counts; `test_seed_idempotency.py` passes)
- Six roles seeded; admin user has role `admin_unit`; `users.bidang_id` column + FK present
- Perspektif VI flagged is_pengurang=True with pengurang_cap=10.00 (W-07)
- `grep -ri siskonkin` returns zero hits
- pytest + vitest both green (real test runs, not ast smoke)
- Restore drill succeeds
- dcron in pulse-backup (not busybox-suid)
- /health/detail + /metrics admin-gated (W-02)
- import-from-excel rejects no-CSRF cookie-auth requests (B-07)
- Login + master screens use only skeuomorphic primitives (W-01)
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-master-data-auth/01-07-SUMMARY.md` listing:
1. Final route table for the frontend (path → role gate → component)
2. Seed inventory (counts of each entity after `make seed`); confirmation that perspektif VI is_pengurang=true, pengurang_cap=10.00 (W-07)
3. **Six-role audit** (B-01/B-02): rows present in `roles`, plus the seeded admin user's `role` join — should be `admin_unit`
4. **B-04 evidence**: `\\d users` output showing `bidang_id` column and `fk_users_bidang_id` constraint
5. **B-07 evidence**: import-from-excel deps list (require_role + require_csrf) — paste from master_konkin.py
6. **B-03 evidence**: screenshot or DevTools snapshot showing different glow color in alert vs healthy LED
7. **W-02 evidence**: `curl http://localhost:3399/api/v1/health/detail` anonymous returns 401; with admin token returns 200
8. **W-08 evidence**: `crond -V` reports dcron
9. Checkpoint outputs (paste the operator's verification responses for steps 1–10)
10. Any anomalies that triggered `/gsd-plan-phase --gaps`
</output>
