---
phase: 01-foundation-master-data-auth
plan: 04
subsystem: frontend-skeleton-design-system
status: complete
tags: [frontend, design-system, vite, tailwind-v4, motion, vitest, skeuomorphic, branding]
dependency_graph:
  requires:
    - "01-01"  # repo scaffold + .gitignore baseline
  provides:
    - frontend-vite-react18-typescript-skeleton
    - tailwind-v4-tokens-via-theme-inline
    - dec-003-skeuomorphic-token-palette
    - pulse-heartbeat-keyframes-healthy-and-alert
    - skeuomorphic-primitive-barrel-six
    - bi-i18n-lookup-map
    - axios-instance-with-401-refresh-coalesce
    - tanstack-query-client-30s-stale
    - vitest-jsdom-test-bootstrap
  affects:
    - "01-02"  # Plan 02 owns frontend/Dockerfile + nginx upstream — needs the build output shape locked
    - "01-07"  # Plan 07 (auth UI + master browse) consumes the barrel + i18n + heartbeat
tech_stack:
  added:
    - "React ^18.3.1 + react-dom ^18.3.1"
    - "Vite ^7.3.3 (was plan ^7.15.0; bumped to latest existing 7.x)"
    - "TypeScript ~5.9.2 (strict mode + bundler resolution)"
    - "Tailwind CSS ^4.3.0 + @tailwindcss/vite ^4.3.0 + tw-animate-css ^1.4.0"
    - "Motion ^12.38.0 (package renamed from framer-motion)"
    - "react-router-dom ^6.30.0 (Pitfall #5: not v7)"
    - "@tanstack/react-query ^5.100.9"
    - "Zustand ^5.0.13"
    - "react-hook-form ^7.75.0 + @hookform/resolvers ^3.10 + Zod ^4.4.3"
    - "axios ^1.16.0"
    - "sonner ^2.0.7"
    - "vitest ^4.1.5 + @testing-library/react ^16.3.2 + jest-dom + user-event + jsdom 25"
    - "eslint 9 + @typescript-eslint 8 + eslint-plugin-react-hooks 5"
  patterns:
    - "Tailwind v4: @theme inline in src/index.css replaces v3 tailwind.config.js + postcss config"
    - "Per-state CSS custom property (--sk-led-glow) overridden via [data-state=\"...\"] attribute selectors so jsdom-incompatible @keyframes still encode the B-03 contract structurally"
    - "MotionConfig reducedMotion=\"user\" wraps the Router so every Motion v12 component honors prefers-reduced-motion automatically"
    - "Singleton refresh-on-401 promise in axios interceptor coalesces concurrent 401s into one /auth/refresh call"
    - "forwardRef on every form primitive (SkInput, SkSelect, SkButton) so react-hook-form's register(...) compiles without ref-type gymnastics"
    - "Barrel re-export with `export type { *Props }` so Plan 07 imports both runtime + types from one path"
key_files:
  created:
    - frontend/package.json
    - frontend/pnpm-lock.yaml
    - frontend/.gitignore
    - frontend/.eslintrc.cjs
    - frontend/components.json
    - frontend/index.html
    - frontend/tsconfig.json
    - frontend/tsconfig.app.json
    - frontend/tsconfig.node.json
    - frontend/vite.config.ts
    - frontend/src/main.tsx
    - frontend/src/App.tsx
    - frontend/src/index.css
    - frontend/src/styles/pulse-heartbeat.css
    - frontend/src/styles/tokens.test.ts
    - frontend/src/lib/i18n.ts
    - frontend/src/lib/query-client.ts
    - frontend/src/lib/api.ts
    - frontend/src/test/setup.ts
    - frontend/src/components/skeuomorphic/index.ts
    - frontend/src/components/skeuomorphic/SkLed.tsx
    - frontend/src/components/skeuomorphic/SkLed.test.tsx
    - frontend/src/components/skeuomorphic/SkButton.tsx
    - frontend/src/components/skeuomorphic/SkPanel.tsx
    - frontend/src/components/skeuomorphic/SkInput.tsx
    - frontend/src/components/skeuomorphic/SkInput.test.tsx
    - frontend/src/components/skeuomorphic/SkSelect.tsx
    - frontend/src/components/skeuomorphic/SkBadge.tsx
  modified: []
decisions:
  - "vite pin bumped to ^7.3.3 (plan said ^7.15.0 which does not exist on npm; latest 7.x is 7.3.3, latest overall 8.0.11). Kept the v7 line per plan intent (Pitfall #6 is about Tailwind v4 with Vite plugin, not Vite version)."
  - "vite.config.ts uses `defineConfig` from \"vitest/config\" (not \"vite\") because vitest 3+ split the types module. Without this, tsc rejects the `test` block as unknown on UserConfigExport. /// <reference types=\"vitest/config\" /> is also required."
  - "vitest CLI reporter `--reporter=basic` removed in vitest 4.x — used `--reporter=default` for the smoke run."
  - "Added \"node\" to tsconfig.app.json compilerOptions.types alongside vitest/globals + jest-dom because tokens.test.ts reads CSS source via node:fs / node:url / node:path. Vitest already runs in node + jsdom mode; the runtime always had access, this just teaches tsc strict-mode about it (B-05 still holds — vitest/globals + jest-dom are still listed)."
  - "Created a minimal SkLed + barrel index.ts inside Task 2's commit (not Task 3 as the plan's files_modified table suggests) because Task 2's App.tsx imports SkLed from @/components/skeuomorphic — tsc -b --noEmit would otherwise fail in Task 2's verify gate. Task 3 then expands the barrel with the other five primitives + tests."
  - "B-03 contract evidence is split across two files: SkLed.test.tsx asserts the data-state attribute drives behavior (jsdom does not execute @keyframes), and tokens.test.ts is the load-bearing structural assertion — it regexes pulse-heartbeat.css for both `data-state=\"on\"][...]--sk-led-glow: var(--sk-pln-yellow-glow)` and `data-state=\"alert\"][...]--sk-led-glow: var(--sk-led-alert-glow)`. Plan §Task 3 §8 note explicitly authorizes this fallback."
metrics:
  duration_minutes: 25
  completed_date: "2026-05-11"
  tasks_completed: 3
  tasks_paused_at_checkpoint: 0
  files_created: 29
  files_modified: 0
  commits: 3
---

# Phase 1 Plan 04: Frontend Skeleton + Design System — Summary

**One-liner:** Stood up the React 18 + Vite 7 + TypeScript 5.9 frontend with Tailwind v4 (`@theme inline`), the full DEC-003 skeuomorphic token palette, two distinct Pulse Heartbeat keyframes (healthy yellow 70 BPM / alert red 120 BPM) with per-state `--sk-led-glow` custom property (B-03), MotionConfig reducedMotion="user" gating, BI-default i18n lookup, axios with refresh-on-401 coalescing, and six Phase-1 skeuomorphic primitives (`SkLed/SkButton/SkPanel/SkInput/SkSelect/SkBadge`) behind a barrel — verified by **31 passing vitest tests** and a clean `tsc -b --noEmit` strict-mode build, both via `pnpm exec` inside WSL2 `Ubuntu-22.04`.

---

## What was built

### Task 1 (commit `856b215`) — Wave 0 frontend bootstrap

Twelve files for the build/test/style foundation, plus `frontend/.gitignore` for tsbuildinfo coverage:

| Path | Role |
|------|------|
| `frontend/package.json` | RESEARCH.md Standard Stack pins (locked exceptions: React 18.3, react-router-dom 6.30, motion 12.38, tailwindcss 4.3, vite **7.3.3**) |
| `frontend/pnpm-lock.yaml` | 313 packages added by `pnpm install` (drvfs mount, 1m 46s) |
| `frontend/.gitignore` | `*.tsbuildinfo`, `.vite/`, `.vitest/`, `coverage/`, `dist/` |
| `frontend/.eslintrc.cjs` | ESLint 9 + `@typescript-eslint` + `react-hooks` (strict rules deferred to Plan 07) |
| `frontend/components.json` | shadcn config — style new-york, baseColor neutral, css-vars true |
| `frontend/index.html` | `<html lang="id">`, title `PULSE — Performance & Unit Live Scoring Engine`, Google Fonts preconnect for Bebas Neue / Oswald / Barlow / JetBrains Mono / Share Tech Mono |
| `frontend/tsconfig.json` | Root: project references → app + node |
| `frontend/tsconfig.app.json` | Strict mode + bundler resolution + `paths: { "@/*": ["./src/*"] }` + `types: ["vitest/globals", "@testing-library/jest-dom", "node"]` (B-05 + tokens-test fix) |
| `frontend/tsconfig.node.json` | For vite.config.ts itself |
| `frontend/vite.config.ts` | `defineConfig` from `vitest/config`, plugins `[react(), tailwindcss()]`, alias `@`, test block (jsdom + globals + setupFiles + css true) |
| `frontend/src/index.css` | Tailwind v4 entry + full DEC-003 token palette + `@theme inline` mapping |
| `frontend/src/styles/pulse-heartbeat.css` | Two keyframes + per-state `--sk-led-glow` + reduced-motion gate |
| `frontend/src/test/setup.ts` | `import "@testing-library/jest-dom"` + `afterEach(cleanup)` |

### Task 2 (commit `14bc5f1`) — App entrypoints + MotionConfig + i18n + axios

| Path | Role |
|------|------|
| `frontend/src/main.tsx` | React 18 `createRoot` + StrictMode + QueryClientProvider + BrowserRouter + Sonner Toaster; throws explicit bootstrap error if `#root` missing |
| `frontend/src/App.tsx` | `<MotionConfig reducedMotion="user">` wraps Router; Wave-5 placeholder route renders PULSE name (display font, yellow) + tagline + heartbeat `<SkLed state="on" label="System pulse" />` |
| `frontend/src/lib/i18n.ts` | Hand-rolled BI lookup map; `t("app.tagline")` → "Denyut Kinerja Pembangkit, Real-Time." Returns raw path on miss so missing keys surface visibly |
| `frontend/src/lib/query-client.ts` | `QueryClient` with `staleTime: 30_000`, `refetchOnWindowFocus: false`, `retry: 1` |
| `frontend/src/lib/api.ts` | axios `{baseURL: "/api/v1", withCredentials: true, timeout: 20_000}`; singleton refresh-on-401 promise coalesces concurrent 401s into one `POST /auth/refresh`, then replays the original request once |

Plus a stub `SkLed.tsx` + barrel `index.ts` (so App.tsx's barrel import resolves under tsc in this task — see "Deviations" §SkLed-stub-in-task-2).

### Task 3 (commit `5322ab6`) — Six skeuomorphic primitives + tests

| Path | Role |
|------|------|
| `frontend/src/components/skeuomorphic/SkLed.tsx` | Indicator LED; `state` drives heartbeat CSS via `data-state` attribute |
| `frontend/src/components/skeuomorphic/SkButton.tsx` | Tactile button; raised/sunk bevel via box-shadow inset stack; `variant` primary/secondary/ghost; forwardRef |
| `frontend/src/components/skeuomorphic/SkPanel.tsx` | Control-room panel wrapper; `inset` toggles raised↔recessed; `title` adds aria-labelled caption strip |
| `frontend/src/components/skeuomorphic/SkInput.tsx` | Recessed text input; forwardRef; `invalid` → red border + `aria-invalid="true"` |
| `frontend/src/components/skeuomorphic/SkSelect.tsx` | Native-select wrapper; keeps free keyboard nav; forwardRef |
| `frontend/src/components/skeuomorphic/SkBadge.tsx` | Status/role pill; `tone` maps to DEC-003 level palette |
| `frontend/src/components/skeuomorphic/index.ts` | Barrel: 6 runtime exports + 6 `*Props` type re-exports (W-10) |
| `frontend/src/components/skeuomorphic/SkLed.test.tsx` | 4 tests — data-state contract, alert color, off state, distinct B-03 states |
| `frontend/src/components/skeuomorphic/SkInput.test.tsx` | 3 tests — data-sk + aria-label, invalid → aria-invalid, ref forwarding |
| `frontend/src/styles/tokens.test.ts` | 24 tests — 20 token declarations, no-legacy-brand, B-03 dual keyframes, B-03 alert keyframe uses correct glow var, reduced-motion gate |

---

## Final dependency pin table (read back from `frontend/package.json`)

### Dependencies
| Package | Pin |
|---------|-----|
| `react` | `^18.3.1` |
| `react-dom` | `^18.3.1` |
| `react-router-dom` | `^6.30.0` |
| `@tanstack/react-query` | `^5.100.9` |
| `zustand` | `^5.0.13` |
| `react-hook-form` | `^7.75.0` |
| `@hookform/resolvers` | `^3.10` |
| `zod` | `^4.4.3` |
| `axios` | `^1.16.0` |
| `motion` | `^12.38.0` |
| `sonner` | `^2.0.7` |

### DevDependencies
| Package | Pin |
|---------|-----|
| `typescript` | `~5.9.2` |
| `vite` | `^7.3.3` *(bumped from plan's invalid `^7.15.0`)* |
| `@vitejs/plugin-react` | `^5.0.0` |
| `tailwindcss` | `^4.3.0` |
| `@tailwindcss/vite` | `^4.3.0` |
| `tw-animate-css` | `^1.4.0` |
| `vitest` | `^4.1.5` |
| `@testing-library/react` | `^16.3.2` |
| `@testing-library/jest-dom` | `^6.6.0` |
| `@testing-library/user-event` | `^14.5.2` |
| `jsdom` | `^25.0.0` |
| `@types/react` | `^18.3.20` |
| `@types/react-dom` | `^18.3.6` |
| `@types/node` | `^20.17.0` |
| `eslint` | `^9` |
| `@typescript-eslint/parser` | `^8` |
| `@typescript-eslint/eslint-plugin` | `^8` |
| `eslint-plugin-react-hooks` | `^5` |

`packageManager`: `pnpm@9.15.0` (auto-downloaded by corepack inside WSL — installed pnpm runtime resolved to 10.15.0 per host_toolchain note).

---

## tsconfig.app.json compilerOptions.types (B-05 evidence)

```json
"types": ["vitest/globals", "@testing-library/jest-dom", "node"]
```

- `vitest/globals` — exposes `describe`, `it`, `expect`, `vi`, `beforeEach`, `afterEach` without imports (B-05 contract).
- `@testing-library/jest-dom` — adds `toHaveAttribute`, `toBeInTheDocument`, `toHaveClass`, etc. to the `expect` chain.
- `node` — added (deviation Rule 3 — Blocking) so `tokens.test.ts` can import `node:fs`/`node:url`/`node:path` under strict-mode tsc. Vitest already runs in node env; this just teaches tsc.

---

## Token palette table (DEC-003 mapping)

All declared under `:root` in `frontend/src/index.css`.

| Token | Value | DEC-003 mapping |
|---|---|---|
| `--sk-surface-0` | `#0a0e14` | Surface 0 — control-room deepest dark |
| `--sk-surface-1` | `#11161f` | Surface 1 — primary panel ground |
| `--sk-surface-2` | `#1a2030` | Surface 2 — recessed inputs / inset wells |
| `--sk-surface-3` | `#232a3d` | Surface 3 — raised secondary buttons |
| `--sk-bevel-light` | `rgba(255,255,255,0.06)` | Top bevel highlight |
| `--sk-bevel-dark` | `rgba(0,0,0,0.40)` | Bottom bevel shadow |
| `--sk-pln-blue` | `#1e3a8a` | PLN brand blue |
| `--sk-pln-blue-glow` | `rgba(30, 58, 138, 0.55)` | Blue glow halo |
| `--sk-pln-yellow` | `#fbbf24` | PLN brand yellow (heartbeat default) |
| `--sk-pln-yellow-glow` | `rgba(251, 191, 36, 0.55)` | Yellow glow halo (healthy heartbeat) |
| `--sk-level-0` | `#dc2626` | Level 0 — red (alert) |
| `--sk-level-1` | `#f59e0b` | Level 1 — amber |
| `--sk-level-2` | `#facc15` | Level 2 — yellow |
| `--sk-level-3` | `#84cc16` | Level 3 — lime |
| `--sk-level-4` | `#10b981` | Level 4 — emerald (target) |
| **`--sk-led-glow`** | `var(--sk-pln-yellow-glow)` (default) | **B-03 fix:** parameterized per-state glow custom property; overridden by `.sk-led[data-state="..."]` rules |
| **`--sk-led-alert-glow`** | `rgba(239, 68, 68, 0.65)` | **B-03 fix:** L0-derived red glow used by the alert keyframe |
| `--sk-lcd-bg` | `#0d1610` | LCD screen ground |
| `--sk-lcd-green` | `#4ade80` | LCD foreground |
| `--sk-lcd-glow` | `rgba(74, 222, 128, 0.65)` | LCD glow |
| `--sk-text-hi` | `#e5e7eb` | High-emphasis text |
| `--sk-text-mid` | `#9ca3af` | Mid-emphasis text |
| `--sk-text-lo` | `#6b7280` | Low-emphasis text / disabled |
| `--sk-font-display` | `"Bebas Neue","Oswald", system-ui, sans-serif` | Display (PULSE wordmark) |
| `--sk-font-body` | `"Barlow", system-ui, sans-serif` | Body |
| `--sk-font-mono` | `"JetBrains Mono", ui-monospace, monospace` | Mono (code / inputs) |
| `--sk-font-lcd` | `"Share Tech Mono", "JetBrains Mono", monospace` | LCD digit font |

---

## Two heartbeat keyframes side-by-side (B-03 evidence)

```css
/* Healthy heartbeat — yellow (PLN). 70 BPM ≈ 0.857s cycle. */
@keyframes pulse-heartbeat-healthy {
  0%, 60%, 100% {
    transform: scale(1);
    opacity: 1;
    box-shadow: 0 0 8px var(--sk-pln-yellow-glow);
  }
  30% {
    transform: scale(1.15);
    opacity: 0.85;
    box-shadow: 0 0 16px var(--sk-pln-yellow-glow);
  }
}

/* Alert heartbeat — red glow, faster (~120 BPM ≈ 0.5s). The glow color
   MUST differ from the healthy keyframe's glow (B-03 contract). */
@keyframes pulse-heartbeat-alert {
  0%, 60%, 100% {
    transform: scale(1);
    opacity: 1;
    box-shadow: 0 0 8px var(--sk-led-alert-glow);
  }
  30% {
    transform: scale(1.18);
    opacity: 0.85;
    box-shadow: 0 0 18px var(--sk-led-alert-glow);
  }
}
```

Per-state custom property assignment (proven by `tokens.test.ts`):

```css
.sk-led[data-state="on"]    { animation: pulse-heartbeat-healthy 0.857s ease-in-out infinite; --sk-led-glow: var(--sk-pln-yellow-glow); }
.sk-led[data-state="alert"] { background: var(--sk-level-0); animation: pulse-heartbeat-alert 0.5s ease-in-out infinite; --sk-led-glow: var(--sk-led-alert-glow); }
```

Reduced-motion gate:

```css
@media (prefers-reduced-motion: reduce) {
  .sk-led[data-state="on"], .sk-led[data-state="alert"] { animation: none; }
}
```

---

## Vitest run output (real test count + duration — B-06 evidence)

Final run (after Task 3) inside WSL2 Ubuntu-22.04:

```
✓ src/components/skeuomorphic/SkInput.test.tsx (3 tests) 33ms
✓ src/components/skeuomorphic/SkLed.test.tsx   (4 tests) 61ms
✓ src/styles/tokens.test.ts                    (24 tests) 10ms

 Test Files  3 passed (3)
      Tests  31 passed (31)
   Start at  11:52:50
   Duration  20.34s (transform 713ms, setup 13.50s, import 701ms, tests 104ms, environment 21.15s)
```

Wave-0 smoke (Task 1 verify):

```
$ pnpm exec vitest --run --reporter=default --passWithNoTests
RUN v4.1.5 …/frontend
No test files found, exiting with code 0
```

Strict typecheck (every task verify):

```
$ pnpm exec tsc -b --noEmit
$ echo $?
0
```

---

## Six primitive public APIs (for Plan 07 to consume via barrel)

```ts
// import { SkLed, SkButton, SkPanel, SkInput, SkSelect, SkBadge } from "@/components/skeuomorphic";

export interface SkLedProps {
  state: "off" | "on" | "alert";
  color?: "yellow" | "green" | "red";
  label?: string;                // visually-hidden accessible name
  style?: CSSProperties;
}

export interface SkButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  pressed?: boolean;
}
// forwardRef'd; type defaults to "button" so it doesn't submit forms.

export interface SkPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  inset?: boolean;     // false = raised module, true = recessed well
  title?: string;      // adds role=group + aria-label
}

export interface SkInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;   // → border level-0, aria-invalid="true"
  label?: string;      // → aria-label
}
// forwardRef'd for react-hook-form.

export interface SkSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  invalid?: boolean;
  label?: string;
}
// forwardRef'd for react-hook-form. Native <select> keeps free keyboard nav.

export interface SkBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: "neutral" | "info" | "success" | "warning" | "danger";
}
```

Plan 07 import contract (consume via barrel):

```ts
import { SkLed, SkButton, SkPanel, SkInput, SkSelect, SkBadge } from "@/components/skeuomorphic";
```

No raw `<input>` / `<select>` / `<button>` allowed on Login or master-data screens (W-01 contract).

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Plan pinned `vite ^7.15.0`, a version that does not exist on npm**

- **Found during:** Task 1 `pnpm install`.
- **Issue:** `ERR_PNPM_NO_MATCHING_VERSION  No matching version found for vite@^7.15.0`. Verified via `pnpm view vite versions`: latest 7.x is **7.3.3**; latest overall is **8.0.11**; there is no 7.15.x line.
- **Fix:** Bumped `package.json` to `"vite": "^7.3.3"`. Kept on the v7 line per plan intent (RESEARCH.md Pitfall #6 is about Tailwind v4's `@tailwindcss/vite` plugin pairing, not about Vite version specifically).
- **Verify-gate impact:** None — the Task 1 PowerShell `<automated>` only regex-checks `"tailwindcss":\s*"\^4"` / `"motion":\s*"\^12"` / `"react":\s*"\^18"` / `"react-router-dom":\s*"\^6\.30"`. Vite version is not regex'd.
- **Files modified:** `frontend/package.json`.
- **Commit:** `856b215`.

**2. [Rule 3 — Blocking] vitest 4.x removed the `basic` reporter**

- **Found during:** Task 1 verify smoke run.
- **Issue:** `pnpm exec vitest --run --reporter=basic --passWithNoTests` failed with `Failed to load url basic (resolved id: basic). Does the file exist?` — vitest 4.x routes unknown reporter names through the module resolver. The `basic` reporter was a vitest 1-3.x feature.
- **Fix:** Used `--reporter=default` for the smoke run. Behavior is equivalent (per-file single-line summary, plus per-test detail on failure).
- **Commit:** `856b215` (the deviation is in the verify methodology, not in committed source — the plan's literal `<automated>` flag was the bug).

**3. [Rule 3 — Blocking] vite.config.ts `test` block rejected by tsc**

- **Found during:** Task 1 first `tsc -b --noEmit` after writing vite.config.ts.
- **Issue:** With `defineConfig` imported from `"vite"` and `/// <reference types="vitest" />`, tsc emitted `TS2769: ... 'test' does not exist in type 'UserConfigExport'`. Vitest 3+ split the types module: the merged config types now live in `vitest/config`, not `vitest`.
- **Fix:** Changed to `import { defineConfig } from "vitest/config"` and `/// <reference types="vitest/config" />`. Both vitest runtime (which already accepted the file) and tsc strict-mode now agree on the config shape.
- **Files modified:** `frontend/vite.config.ts`.
- **Commit:** `856b215`.

**4. [Rule 3 — Blocking] tokens.test.ts node:* imports rejected by tsc under the plan's tsconfig.app.json**

- **Found during:** Task 3 `tsc -b --noEmit`.
- **Issue:** The plan's tsconfig.app.json sets `types: ["vitest/globals", "@testing-library/jest-dom"]`, which **replaces** (does not extend) the default node types. So tokens.test.ts emitted `TS2307: Cannot find module 'node:fs'` etc. — even though vitest at runtime resolved the imports fine (test passed when first run).
- **Fix:** Appended `"node"` to the types array → `types: ["vitest/globals", "@testing-library/jest-dom", "node"]`. B-05 contract (vitest globals + jest-dom in types) is preserved — the plan's verify regex `vitest/globals` and `@testing-library/jest-dom` still match.
- **Files modified:** `frontend/tsconfig.app.json`.
- **Commit:** `5322ab6`.

**5. [Rule 3 — Blocking] SkLed + barrel had to land in Task 2's commit (plan said Task 3)**

- **Found during:** Task 2 verify (`tsc -b --noEmit`).
- **Issue:** The plan's Task 2 App.tsx imports `SkLed` from `@/components/skeuomorphic`. The plan's `<files>` list for Task 2 does not include the barrel or SkLed.tsx — those are listed under Task 3. With per-task commits and per-task verify gates, Task 2's tsc would fail because the import target does not exist.
- **Fix:** Created a minimal `SkLed.tsx` (matching the plan's Task 3 §1 spec) + barrel `index.ts` (re-exporting only SkLed) in Task 2's commit. Task 3 then expanded the barrel with the other five primitives + tests, and added the rest of the barrel re-exports.
- **Files affected:** `frontend/src/components/skeuomorphic/SkLed.tsx` (created Task 2), `frontend/src/components/skeuomorphic/index.ts` (created Task 2, expanded Task 3).
- **Commit:** `14bc5f1` (initial SkLed + stub barrel), `5322ab6` (full barrel + 5 more primitives + 3 tests).

### Authentication / Human-Action Gates

None. This plan is pure scaffolding — no network credentials, no external services, no human verification required.

---

## Known Stubs

| Stub | Location | Reason | Resolved by |
|------|----------|--------|-------------|
| Wave-5 placeholder landing route in `App.tsx` | `/` route shows PULSE heading + tagline + heartbeat LED only | The router isn't supposed to flesh out Login/Dashboard/Master in Phase 1 Plan 04 — those are Plan 07's scope. The placeholder still satisfies ROADMAP success criterion #3 (PULSE branding + tagline + heartbeat visible on day one). | **Plan 01-07** (Wave 5 — auth UI + master browse) |
| Refresh-on-401 interceptor in `api.ts` has no Zustand auth-store wiring | After `/auth/refresh` fails, the interceptor propagates the original 401 but doesn't clear an in-memory user object | Plan 07 owns the Zustand auth store; this seam stays a no-op until then. The promise-coalescing logic is already correct so concurrent 401s don't fire multiple refresh calls. | **Plan 01-05** (auth backend) + **Plan 01-07** (auth UI wiring) |
| CSRF echo interceptor not yet present in `api.ts` | B-07 fix lives in Plan 07 per CONTEXT.md §API | Plan 07 adds the `X-CSRF-Token` request interceptor that reads the `pulse-csrf` cookie. The httpOnly cookie auth path is already established here via `withCredentials: true`. | **Plan 01-07** |

None of these block Plan 04's stated goal — the heartbeat is visible, the tokens are wired, the primitives ship behind a barrel, and the i18n + axios infrastructure is ready for Plan 07 to consume.

---

## Threat Flags

None. Surface introduced is exactly what the plan's `<threat_model>` enumerates:

- T-04-S-01 (Spoofing — JWT in localStorage anti-pattern): **mitigated** — `api.ts` uses `withCredentials: true` exclusively; the only token-shaped persistence will be Plan 07's Zustand in-memory store. No localStorage write paths exist.
- T-04-T-01 (Tampering — `dangerouslySetInnerHTML`): **mitigated** — no `dangerouslySetInnerHTML` call anywhere in the committed code.
- T-04-I-01 (Info disclosure — secret-looking placeholders in i18n): **mitigated** — i18n keyset reviewed; no token/secret patterns; only UI strings.
- T-04-D-01 (DoS — animation thrashing under reduced motion): **mitigated** — `@media (prefers-reduced-motion: reduce)` disables both keyframes (tokens.test.ts asserts this structurally), and `MotionConfig reducedMotion="user"` in `App.tsx` covers framer-motion siblings.

No new endpoints, no new auth paths, no schema changes.

---

## TDD Gate Compliance

Plan 01-04 frontmatter does not declare `type: tdd` and no task carries `tdd="true"`. The plan IS test-first in spirit (Wave-0 vitest bootstrap in Task 1 lands before any feature task references `pnpm exec vitest …`, B-06 fix), and Tasks 2/3 ship implementation + tests together — but this is not the formal RED/GREEN/REFACTOR gate. The plan-checker did not require it. Skipped.

---

## Self-Check: PASSED

Verified after writing this SUMMARY (commit hashes from `git log` inside the worktree):

```
[ -f frontend/package.json ]                                   → FOUND
[ -f frontend/pnpm-lock.yaml ]                                 → FOUND
[ -f frontend/.gitignore ]                                     → FOUND
[ -f frontend/tsconfig.app.json ]                              → FOUND
[ -f frontend/vite.config.ts ]                                 → FOUND
[ -f frontend/index.html ]                                     → FOUND
[ -f frontend/src/main.tsx ]                                   → FOUND
[ -f frontend/src/App.tsx ]                                    → FOUND
[ -f frontend/src/index.css ]                                  → FOUND
[ -f frontend/src/styles/pulse-heartbeat.css ]                 → FOUND
[ -f frontend/src/styles/tokens.test.ts ]                      → FOUND
[ -f frontend/src/lib/i18n.ts ]                                → FOUND
[ -f frontend/src/lib/api.ts ]                                 → FOUND
[ -f frontend/src/lib/query-client.ts ]                        → FOUND
[ -f frontend/src/test/setup.ts ]                              → FOUND
[ -f frontend/src/components/skeuomorphic/index.ts ]           → FOUND
[ -f frontend/src/components/skeuomorphic/SkLed.tsx ]          → FOUND
[ -f frontend/src/components/skeuomorphic/SkLed.test.tsx ]     → FOUND
[ -f frontend/src/components/skeuomorphic/SkButton.tsx ]       → FOUND
[ -f frontend/src/components/skeuomorphic/SkPanel.tsx ]        → FOUND
[ -f frontend/src/components/skeuomorphic/SkInput.tsx ]        → FOUND
[ -f frontend/src/components/skeuomorphic/SkInput.test.tsx ]   → FOUND
[ -f frontend/src/components/skeuomorphic/SkSelect.tsx ]       → FOUND
[ -f frontend/src/components/skeuomorphic/SkBadge.tsx ]        → FOUND

git log --oneline | grep 856b215  → FOUND  (Task 1: bootstrap)
git log --oneline | grep 14bc5f1  → FOUND  (Task 2: app entrypoints)
git log --oneline | grep 5322ab6  → FOUND  (Task 3: primitives + tests)

pnpm exec vitest --run            → 3 test files, 31 tests passed
pnpm exec tsc -b --noEmit         → exit 0
```

All claims verified.
