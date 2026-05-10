---
phase: 01-foundation-master-data-auth
plan: 04
type: execute
wave: 2
depends_on: [01]
files_modified:
  - frontend/package.json
  - frontend/pnpm-lock.yaml
  - frontend/tsconfig.json
  - frontend/tsconfig.app.json
  - frontend/tsconfig.node.json
  - frontend/vite.config.ts
  - frontend/index.html
  - frontend/.eslintrc.cjs
  - frontend/components.json
  - frontend/src/main.tsx
  - frontend/src/App.tsx
  - frontend/src/index.css
  - frontend/src/lib/i18n.ts
  - frontend/src/lib/query-client.ts
  - frontend/src/lib/api.ts
  - frontend/src/styles/pulse-heartbeat.css
  - frontend/src/styles/tokens.test.ts
  - frontend/src/components/skeuomorphic/index.ts
  - frontend/src/components/skeuomorphic/SkLed.tsx
  - frontend/src/components/skeuomorphic/SkButton.tsx
  - frontend/src/components/skeuomorphic/SkPanel.tsx
  - frontend/src/components/skeuomorphic/SkInput.tsx
  - frontend/src/components/skeuomorphic/SkSelect.tsx
  - frontend/src/components/skeuomorphic/SkBadge.tsx
  - frontend/src/components/skeuomorphic/SkLed.test.tsx
  - frontend/src/components/skeuomorphic/SkInput.test.tsx
  - frontend/src/test/setup.ts
autonomous: true
requirements:
  - REQ-frontend-stack
  - REQ-pulse-branding
  - REQ-pulse-heartbeat-animation
  - REQ-skeuomorphic-design-system
must_haves:
  truths:
    - "`pnpm install && pnpm build` produces a static dist/ that ships PULSE branding and the Pulse Heartbeat keyframes"
    - "A `<SkLed data-state=\"on\">` element animates with the **healthy** keyframe (yellow glow, 70 BPM ≈ 857ms cycle); `data-state=\"alert\"` animates with the **alert** keyframe whose computed glow color differs from healthy (B-03)"
    - "When the user has `prefers-reduced-motion: reduce`, all heartbeat keyframes are disabled (CSS @media gate + MotionConfig reducedMotion='user')"
    - "Tailwind v4 is configured via `@tailwindcss/vite` + `@theme inline` in src/index.css — no v3 tailwind.config.js + postcss config (RESEARCH.md State of the Art)"
    - "The full skeuomorphic design token palette lives in `:root` CSS variables per DEC-003: surfaces, PLN brand (`--sk-pln-blue`, `--sk-pln-yellow`), level palette L0–L4 (red→emerald), LCD green with glow, typography stack, plus the new `--sk-led-alert-glow` and per-state `--sk-led-glow` custom properties"
    - "**Six skeuomorphic primitives ship in Phase 1 (W-01):** `SkLed`, `SkButton`, `SkPanel`, **`SkInput`**, **`SkSelect`**, **`SkBadge`**, all re-exported from a barrel `frontend/src/components/skeuomorphic/index.ts` (W-10)"
    - "Vitest globals + jest-dom types are reachable in TypeScript strict mode: `frontend/tsconfig.app.json` includes `\"types\": [\"vitest/globals\", \"@testing-library/jest-dom\"]` so `describe`/`it`/`expect`/`toHaveAttribute` resolve under `tsc -b --noEmit` (B-05)"
    - "i18n is a hand-rolled lookup map (Bahasa Indonesia default, structure ready for EN) — no react-i18next bundle"
    - "MotionConfig reducedMotion='user' wraps the entire app — every framer-motion component respects the user's OS preference for free"
    - "Vitest test runner smoke passes via real `pnpm exec vitest --run --reporter=basic` (B-06) — not ast/syntax-only checks"
  artifacts:
    - path: "frontend/package.json"
      provides: "Locked dependency pins per RESEARCH.md Standard Stack (React 18, react-router-dom ^6.30, motion 12.x, tailwindcss 4.x)"
      contains: "\"react\": \"^18.3.1\""
    - path: "frontend/tsconfig.app.json"
      provides: "Vitest globals + jest-dom types in compilerOptions.types (B-05)"
      contains: "vitest/globals"
    - path: "frontend/src/index.css"
      provides: "Tailwind v4 entry + @theme inline tokens + heartbeat keyframes import"
      contains: "@theme inline"
    - path: "frontend/src/styles/pulse-heartbeat.css"
      provides: "Two heartbeat keyframes (healthy yellow, alert red) — B-03 fix"
      contains: "pulse-heartbeat-alert"
    - path: "frontend/src/components/skeuomorphic/index.ts"
      provides: "Barrel re-export of all six Phase-1 primitives (W-10)"
      contains: "SkInput"
    - path: "frontend/src/components/skeuomorphic/SkInput.tsx"
      provides: "Skeuomorphic text input primitive consumed by Login + master screens (W-01)"
      contains: "data-sk"
    - path: "frontend/src/components/skeuomorphic/SkSelect.tsx"
      provides: "Skeuomorphic native-select primitive (W-01)"
      contains: "select"
    - path: "frontend/src/components/skeuomorphic/SkBadge.tsx"
      provides: "Skeuomorphic status/role badge (W-01)"
      contains: "Badge"
    - path: "frontend/src/lib/i18n.ts"
      provides: "Plain TS lookup map; tagline and PULSE name centralized"
      contains: "Denyut Kinerja Pembangkit"
    - path: "frontend/src/App.tsx"
      provides: "App root with MotionConfig reducedMotion='user' wrapping Router"
      contains: "MotionConfig"
  key_links:
    - from: "frontend/src/App.tsx"
      to: "motion/react"
      via: "MotionConfig wrap"
      pattern: "MotionConfig"
    - from: "frontend/src/index.css"
      to: "frontend/src/styles/pulse-heartbeat.css"
      via: "@import \"./styles/pulse-heartbeat.css\""
      pattern: "pulse-heartbeat"
    - from: "frontend/src/components/skeuomorphic/SkLed.tsx"
      to: ".sk-led keyframe"
      via: "className=\"sk-led\" data-state=...";
      pattern: "sk-led"
    - from: "frontend/src/components/skeuomorphic/index.ts"
      to: "all six Phase-1 primitives"
      via: "Re-export barrel"
      pattern: "export.*Sk(Led|Button|Panel|Input|Select|Badge)"
---

## Revision History

- **Iteration 1 (initial):** React 18 + Vite + Tailwind v4 + motion 12 stack, three primitives (SkLed/SkButton/SkPanel), heartbeat keyframes, i18n lookup, axios+TanStack Query.
- **Iteration 2 (this revision):**
  - **B-03 fix:** Heartbeat alert glow now uses two distinct keyframes (`pulse-heartbeat-healthy` yellow / `pulse-heartbeat-alert` red) AND a per-state `--sk-led-glow` CSS custom property so the alert state's computed glow color differs from healthy. New SkLed test asserts the contract.
  - **B-05 fix:** `frontend/tsconfig.app.json` adds `"types": ["vitest/globals", "@testing-library/jest-dom"]` to `compilerOptions`. Verify runs `pnpm exec tsc -b --noEmit`.
  - **B-06 fix:** Task 1 is the **Wave 0 frontend bootstrap** — `pnpm install` runs in this task and the verify executes `pnpm exec vitest --run --reporter=basic --passWithNoTests` as a real test-runner smoke (not ast-only). Tasks 2/3 verify blocks run actual `pnpm exec vitest run <file>`.
  - **W-01 fix:** Adds three more primitives (`SkInput`, `SkSelect`, `SkBadge`) so the full Phase-1 set is six. Login + master screens (Plan 07) consume these — no raw `<input>`/`<select>`/`<button>` tags allowed on those screens.
  - **W-10 fix:** Adds barrel `frontend/src/components/skeuomorphic/index.ts` re-exporting all six primitives. Plan 07 imports via `@/components/skeuomorphic`.

<objective>
Stand up the React 18 + Vite + TypeScript frontend skeleton with the **full** skeuomorphic design token palette (DEC-003), Pulse Heartbeat signature animation with healthy + alert keyframes (B-03), MotionConfig reduced-motion gating, hand-rolled BI i18n lookup, axios + TanStack Query infrastructure, and the **six** Phase-1 skeuomorphic primitives (SkLed, SkButton, SkPanel, SkInput, SkSelect, SkBadge) re-exported from a barrel — enough that Plan 07 can ship the login screen and master-data browse screens with brand + tagline + heartbeat + tactile primitives on day one.

Purpose: REQ-frontend-stack + REQ-skeuomorphic-design-system + REQ-pulse-heartbeat-animation + (start of) REQ-pulse-branding all land here. Plan 07 (Wave 5) consumes these primitives via the barrel.

Runs in parallel with Plan 02 (infra) and Plan 03 (backend) in Wave 2 — exclusive file ownership: owns everything under `frontend/` EXCEPT `frontend/Dockerfile` and `frontend/nginx.conf` (Plan 02 owns those).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/01-foundation-master-data-auth/01-CONTEXT.md
@.planning/phases/01-foundation-master-data-auth/01-RESEARCH.md
@.planning/phases/01-foundation-master-data-auth/01-01-SUMMARY.md

<interfaces>
<!-- Exposed seams for Plan 07 (auth UI + master browse) -->

// frontend/src/lib/i18n.ts
export const t: (path: string) => string;
// Exposed keys (Plan 07 reads these):
//   app.name, app.tagline, app.taglineEn
//   login.title, login.username, login.password, login.submit, login.wrong
//   nav.master, nav.dashboard, nav.logout
//   master.konkin, master.bidang, master.stream
//   common.loading, common.save, common.cancel, common.empty

// frontend/src/components/skeuomorphic/index.ts (BARREL — W-10)
export { SkLed }     from "./SkLed";
export { SkButton }  from "./SkButton";
export { SkPanel }   from "./SkPanel";
export { SkInput }   from "./SkInput";
export { SkSelect }  from "./SkSelect";
export { SkBadge }   from "./SkBadge";
// Plan 07 imports: import { SkLed, SkButton, SkPanel, SkInput, SkSelect, SkBadge } from "@/components/skeuomorphic";

// SkLed
export interface SkLedProps {
  state: "off" | "on" | "alert";   // "on" = healthy heartbeat at 70 BPM (yellow); "alert" = red alert keyframe
  color?: "green" | "yellow" | "red";
  label?: string;                  // visually-hidden accessible name
}

// SkButton
export interface SkButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  pressed?: boolean;
}

// SkPanel
export interface SkPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  inset?: boolean;
  title?: string;
}

// SkInput  (W-01)
export interface SkInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
  label?: string;
}

// SkSelect (W-01)
export interface SkSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  invalid?: boolean;
  label?: string;
}

// SkBadge  (W-01)
export interface SkBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: "neutral" | "info" | "success" | "warning" | "danger";
}

// frontend/src/lib/api.ts
export const api: AxiosInstance;  // baseURL = '/api/v1', withCredentials: true
// Interceptor: on 401 -> attempt POST /api/v1/auth/refresh once, retry. Implemented here; auth store wired by Plan 07.

// frontend/src/lib/query-client.ts
export const queryClient: QueryClient;  // default staleTime 30s, refetchOnWindowFocus: false
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1 (Wave 0): package.json + Vite + TS config + Tailwind v4 + tokens + dep install + vitest smoke</name>
  <files>
    frontend/package.json,
    frontend/pnpm-lock.yaml,
    frontend/tsconfig.json,
    frontend/tsconfig.app.json,
    frontend/tsconfig.node.json,
    frontend/vite.config.ts,
    frontend/index.html,
    frontend/.eslintrc.cjs,
    frontend/components.json,
    frontend/src/index.css,
    frontend/src/styles/pulse-heartbeat.css,
    frontend/src/test/setup.ts
  </files>
  <action>
    **This is the Wave 0 frontend test bootstrap (CONTEXT.md "Test Infrastructure" + B-06).** Install deps, configure vitest globals types in tsconfig, run an empty-test smoke before Tasks 2/3 reference vitest in their `<automated>` blocks.

    1. `frontend/package.json` — exact RESEARCH.md pins (Standard Stack table). Stack-locked exceptions per RESEARCH.md:
       - React stays at **^18.3.1**
       - react-router-dom pinned **^6.30.0** (Pitfall #5)
       - tailwindcss `^4.3.0` with `@tailwindcss/vite` (Pitfall #6)
       - motion `^12.38.0` (NOT framer-motion — Pitfall #7)
       - tw-animate-css instead of tailwindcss-animate

       ```json
       {
         "name": "pulse-frontend",
         "version": "0.1.0",
         "private": true,
         "type": "module",
         "scripts": {
           "dev": "vite",
           "build": "tsc -b && vite build",
           "preview": "vite preview",
           "test": "vitest",
           "lint": "eslint . --max-warnings=0"
         },
         "dependencies": {
           "react": "^18.3.1",
           "react-dom": "^18.3.1",
           "react-router-dom": "^6.30.0",
           "@tanstack/react-query": "^5.100.9",
           "zustand": "^5.0.13",
           "react-hook-form": "^7.75.0",
           "@hookform/resolvers": "^3.10",
           "zod": "^4.4.3",
           "axios": "^1.16.0",
           "motion": "^12.38.0",
           "sonner": "^2.0.7"
         },
         "devDependencies": {
           "typescript": "~5.9.2",
           "vite": "^7.15.0",
           "@vitejs/plugin-react": "^5.0.0",
           "tailwindcss": "^4.3.0",
           "@tailwindcss/vite": "^4.3.0",
           "tw-animate-css": "^1.4.0",
           "vitest": "^4.1.5",
           "@testing-library/react": "^16.3.2",
           "@testing-library/jest-dom": "^6.6.0",
           "@testing-library/user-event": "^14.5.2",
           "jsdom": "^25.0.0",
           "@types/react": "^18.3.20",
           "@types/react-dom": "^18.3.6",
           "@types/node": "^20.17.0",
           "eslint": "^9",
           "@typescript-eslint/parser": "^8",
           "@typescript-eslint/eslint-plugin": "^8",
           "eslint-plugin-react-hooks": "^5"
         },
         "packageManager": "pnpm@9.15.0"
       }
       ```

    2. `frontend/tsconfig.json` (root) — references the app + node configs.

    3. `frontend/tsconfig.app.json` — **B-05 fix**: includes vitest globals + jest-dom types so `describe`/`it`/`expect`/`toHaveAttribute` resolve under `tsc -b --noEmit`:
       ```json
       {
         "compilerOptions": {
           "target": "ES2022",
           "lib": ["ES2022", "DOM", "DOM.Iterable"],
           "module": "ESNext",
           "moduleResolution": "bundler",
           "jsx": "react-jsx",
           "strict": true,
           "noEmit": true,
           "skipLibCheck": true,
           "isolatedModules": true,
           "verbatimModuleSyntax": true,
           "resolveJsonModule": true,
           "esModuleInterop": true,
           "baseUrl": ".",
           "paths": { "@/*": ["./src/*"] },
           "types": ["vitest/globals", "@testing-library/jest-dom"]
         },
         "include": ["src/**/*"]
       }
       ```

    4. `frontend/tsconfig.node.json` — for vite.config.ts itself.

    5. `frontend/vite.config.ts`:
       ```ts
       import { defineConfig } from "vite";
       import react from "@vitejs/plugin-react";
       import tailwindcss from "@tailwindcss/vite";
       import path from "node:path";

       export default defineConfig({
         plugins: [react(), tailwindcss()],
         resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
         server: { host: "0.0.0.0", port: 80, strictPort: true },
         test: {
           environment: "jsdom",
           globals: true,
           setupFiles: ["./src/test/setup.ts"],
           css: true,
         },
       });
       ```

    6. `frontend/index.html` — `<html lang="id">`; `<title>PULSE — Performance & Unit Live Scoring Engine</title>`; preconnect to Google Fonts; load Bebas Neue, Oswald, Barlow, JetBrains Mono, Share Tech Mono per DEC-003 typography stack. NO `siskonkin` anywhere.

    7. `frontend/components.json` — shadcn config (style "new-york", base color "neutral", css-vars true).

    8. `frontend/src/index.css` — Tailwind v4 + skeuomorphic tokens (DEC-003 full palette + B-03 alert glow token):
       ```css
       @import "tailwindcss";
       @import "tw-animate-css";
       @import "./styles/pulse-heartbeat.css";

       /* PULSE Design Tokens — DEC-003 (skeuomorphic dark theme default, light variant) */
       :root {
         /* Surfaces — control-room dark */
         --sk-surface-0:  #0a0e14;
         --sk-surface-1:  #11161f;
         --sk-surface-2:  #1a2030;
         --sk-surface-3:  #232a3d;
         --sk-bevel-light: rgba(255,255,255,0.06);
         --sk-bevel-dark:  rgba(0,0,0,0.40);

         /* PLN brand */
         --sk-pln-blue:        #1e3a8a;
         --sk-pln-blue-glow:   rgba(30, 58, 138, 0.55);
         --sk-pln-yellow:      #fbbf24;
         --sk-pln-yellow-glow: rgba(251, 191, 36, 0.55);

         /* Level palette — red → emerald (L0..L4) */
         --sk-level-0: #dc2626;  /* red */
         --sk-level-1: #f59e0b;  /* amber */
         --sk-level-2: #facc15;  /* yellow */
         --sk-level-3: #84cc16;  /* lime */
         --sk-level-4: #10b981;  /* emerald */

         /* LED glow — B-03 fix: parameterized + alert variant */
         --sk-led-glow:        var(--sk-pln-yellow-glow);   /* default healthy */
         --sk-led-alert-glow:  rgba(239, 68, 68, 0.65);     /* L0-derived red glow */

         /* LCD */
         --sk-lcd-bg:    #0d1610;
         --sk-lcd-green: #4ade80;
         --sk-lcd-glow:  rgba(74, 222, 128, 0.65);

         /* Text */
         --sk-text-hi:  #e5e7eb;
         --sk-text-mid: #9ca3af;
         --sk-text-lo:  #6b7280;

         /* Typography stack (CONSTR-design-tokens) */
         --sk-font-display: "Bebas Neue","Oswald", system-ui, sans-serif;
         --sk-font-body:    "Barlow", system-ui, sans-serif;
         --sk-font-mono:    "JetBrains Mono", ui-monospace, monospace;
         --sk-font-lcd:     "Share Tech Mono", "JetBrains Mono", monospace;
       }

       /* Tailwind v4: expose tokens to utilities via @theme inline */
       @theme inline {
         --color-surface-0: var(--sk-surface-0);
         --color-surface-1: var(--sk-surface-1);
         --color-surface-2: var(--sk-surface-2);
         --color-surface-3: var(--sk-surface-3);
         --color-pln-blue: var(--sk-pln-blue);
         --color-pln-yellow: var(--sk-pln-yellow);
         --color-lcd-green: var(--sk-lcd-green);
         --color-level-0: var(--sk-level-0);
         --color-level-1: var(--sk-level-1);
         --color-level-2: var(--sk-level-2);
         --color-level-3: var(--sk-level-3);
         --color-level-4: var(--sk-level-4);
         --font-display: var(--sk-font-display);
         --font-body: var(--sk-font-body);
         --font-mono: var(--sk-font-mono);
         --font-lcd: var(--sk-font-lcd);
       }

       html, body, #root { height: 100%; }
       body {
         margin: 0;
         background: var(--sk-surface-0);
         color: var(--sk-text-hi);
         font-family: var(--sk-font-body);
         -webkit-font-smoothing: antialiased;
       }
       ```

    9. `frontend/src/styles/pulse-heartbeat.css` — **B-03 fix: two keyframes, per-state glow color via `--sk-led-glow`**:
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

       .sk-led {
         display: inline-block;
         width: 12px; height: 12px;
         border-radius: 50%;
         background: var(--sk-pln-yellow);
         transform-origin: center;
         will-change: transform, opacity, box-shadow;
       }

       /* Per-state glow custom property — read by SkLed.test.tsx via getComputedStyle. */
       .sk-led[data-state="off"]   { background: var(--sk-text-lo); box-shadow: none; --sk-led-glow: transparent; }
       .sk-led[data-state="on"]    { animation: pulse-heartbeat-healthy 0.857s ease-in-out infinite; --sk-led-glow: var(--sk-pln-yellow-glow); }
       .sk-led[data-state="alert"] { background: var(--sk-level-0); animation: pulse-heartbeat-alert 0.5s ease-in-out infinite; --sk-led-glow: var(--sk-led-alert-glow); }

       @media (prefers-reduced-motion: reduce) {
         .sk-led[data-state="on"], .sk-led[data-state="alert"] { animation: none; }
       }
       ```

    10. `frontend/src/test/setup.ts`:
        ```ts
        import "@testing-library/jest-dom";
        import { afterEach } from "vitest";
        import { cleanup } from "@testing-library/react";
        afterEach(() => cleanup());
        ```

    11. `frontend/.eslintrc.cjs` — minimal config with `react-hooks/recommended` and `@typescript-eslint/recommended`. Set `"react-hooks/exhaustive-deps": "warn"`.

    12. **Wave-0 dep install + smoke** (after files written):
        ```bash
        cd frontend
        pnpm install
        pnpm exec vitest --run --reporter=basic --passWithNoTests
        pnpm exec tsc -b --noEmit
        ```
        - `pnpm install` produces the lockfile and installs.
        - `vitest --passWithNoTests` runs the test runner with zero tests yet — proves vitest resolves with the new tsconfig types and jsdom + setup file work.
        - `tsc -b --noEmit` proves vitest globals + jest-dom types resolve in TypeScript strict mode (B-05).

    Brand check: no `siskonkin` in any new file.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $p = Get-Content 'frontend/package.json' -Raw;
        if ($p -notmatch '\"react\":\\s*\"\\^18') { Write-Output 'React must be 18.x'; exit 1 };
        if ($p -notmatch '\"react-router-dom\":\\s*\"\\^6\\.30') { exit 2 };
        if ($p -notmatch '\"motion\":\\s*\"\\^12') { exit 3 };
        if ($p -notmatch '\"tailwindcss\":\\s*\"\\^4') { exit 4 };
        if ($p -match '\"framer-motion\"') { exit 5 };
        if ($p -match 'tailwindcss-animate') { exit 6 };
        $tsa = Get-Content 'frontend/tsconfig.app.json' -Raw;
        if ($tsa -notmatch 'vitest/globals') { Write-Output 'B-05: missing vitest/globals in tsconfig.app.json'; exit 7 };
        if ($tsa -notmatch '@testing-library/jest-dom') { exit 8 };
        $css = Get-Content 'frontend/src/index.css' -Raw;
        if ($css -notmatch '@theme inline') { exit 9 };
        if ($css -notmatch '--sk-pln-blue:\\s*#1e3a8a')  { exit 10 };
        if ($css -notmatch '--sk-pln-yellow:\\s*#fbbf24'){ exit 11 };
        if ($css -notmatch '--sk-led-alert-glow') { Write-Output 'B-03: missing --sk-led-alert-glow'; exit 12 };
        $hb = Get-Content 'frontend/src/styles/pulse-heartbeat.css' -Raw;
        if ($hb -notmatch '@keyframes pulse-heartbeat-healthy') { exit 13 };
        if ($hb -notmatch '@keyframes pulse-heartbeat-alert')   { exit 14 };
        if ($hb -notmatch 'prefers-reduced-motion')             { exit 15 };
        if ($hb -notmatch '0\\.857s') { exit 16 };
        if ((Select-String -Path 'frontend/index.html','frontend/src/index.css' -SimpleMatch 'siskonkin' -CaseSensitive:$false)) { exit 17 };
        # B-06 Wave-0 smoke: real pnpm install + vitest + tsc
        Push-Location frontend
        pnpm install --frozen-lockfile=false 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Output 'pnpm install failed'; exit 18 };
        pnpm exec vitest --run --reporter=basic --passWithNoTests 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Output 'vitest smoke failed'; exit 19 };
        pnpm exec tsc -b --noEmit 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Output 'tsc -b --noEmit failed (B-05)'; exit 20 };
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    package.json pins match RESEARCH.md stack; tsconfig.app.json declares vitest/globals + jest-dom types (B-05); index.css has full DEC-003 token palette + `--sk-led-alert-glow`; heartbeat CSS has TWO keyframes (healthy/alert) at 70 / 120 BPM (B-03) + reduced-motion gate; `pnpm install` resolves; `vitest --passWithNoTests` and `tsc -b --noEmit` both succeed (B-06 Wave 0 smoke); no `siskonkin` in any file.
  </done>
</task>

<task type="auto">
  <name>Task 2: App entrypoints + MotionConfig + i18n + axios/query</name>
  <files>
    frontend/src/main.tsx,
    frontend/src/App.tsx,
    frontend/src/lib/i18n.ts,
    frontend/src/lib/query-client.ts,
    frontend/src/lib/api.ts
  </files>
  <action>
    1. `frontend/src/main.tsx`:
       ```tsx
       import React from "react";
       import ReactDOM from "react-dom/client";
       import { QueryClientProvider } from "@tanstack/react-query";
       import { BrowserRouter } from "react-router-dom";
       import { Toaster } from "sonner";
       import App from "./App";
       import { queryClient } from "./lib/query-client";
       import "./index.css";

       ReactDOM.createRoot(document.getElementById("root")!).render(
         <React.StrictMode>
           <QueryClientProvider client={queryClient}>
             <BrowserRouter>
               <App />
               <Toaster richColors closeButton />
             </BrowserRouter>
           </QueryClientProvider>
         </React.StrictMode>
       );
       ```

    2. `frontend/src/App.tsx` — minimal route stub; Plan 07 fleshes out routes:
       ```tsx
       import { MotionConfig } from "motion/react";
       import { Routes, Route, Navigate } from "react-router-dom";
       import { t } from "@/lib/i18n";
       import { SkLed } from "@/components/skeuomorphic";

       export default function App() {
         return (
           <MotionConfig reducedMotion="user">
             <Routes>
               {/* Wave 5 placeholder landing — Plan 07 replaces with Login / Dashboard / Master routes */}
               <Route
                 path="/"
                 element={
                   <main style={{ display: "grid", placeItems: "center", height: "100vh", gap: "1rem" }}>
                     <h1 style={{ fontFamily: "var(--sk-font-display)", fontSize: "4rem", margin: 0, letterSpacing: "0.05em" }}>
                       {t("app.name")}
                     </h1>
                     <p style={{ color: "var(--sk-text-mid)" }}>{t("app.tagline")}</p>
                     <SkLed state="on" label="System pulse" />
                   </main>
                 }
               />
               <Route path="*" element={<Navigate to="/" replace />} />
             </Routes>
           </MotionConfig>
         );
       }
       ```

    3. `frontend/src/lib/i18n.ts` — full Phase-1 keyset:
       ```ts
       const id = {
         app: {
           name: "PULSE",
           tagline: "Denyut Kinerja Pembangkit, Real-Time.",
           taglineEn: "The Heartbeat of Power Performance.",
         },
         login: {
           title: "Masuk ke PULSE",
           username: "Pengguna",
           password: "Kata Sandi",
           submit: "Masuk",
           wrong: "Pengguna atau kata sandi salah.",
         },
         nav: { master: "Master Data", dashboard: "Dasbor", logout: "Keluar" },
         master: {
           konkin: "Template Konkin 2026",
           bidang: "Master Bidang",
           stream: "Maturity Level Stream",
         },
         common: {
           loading: "Memuat…",
           save: "Simpan",
           cancel: "Batal",
           empty: "Tidak ada data.",
           error: "Terjadi kesalahan.",
         },
       } as const;

       type Dict = typeof id;
       export const t = (path: string): string =>
         path.split(".").reduce<any>((o, k) => (o ?? {})[k], id) ?? path;

       export type { Dict };
       ```

    4. `frontend/src/lib/query-client.ts`:
       ```ts
       import { QueryClient } from "@tanstack/react-query";
       export const queryClient = new QueryClient({
         defaultOptions: {
           queries: { staleTime: 30_000, refetchOnWindowFocus: false, retry: 1 },
         },
       });
       ```

    5. `frontend/src/lib/api.ts` — axios instance with refresh-on-401 interceptor stub (auth-store import wired by Plan 07):
       ```ts
       import axios, { AxiosError, AxiosRequestConfig } from "axios";

       export const api = axios.create({
         baseURL: "/api/v1",
         withCredentials: true,  // httpOnly cookie auth path
         timeout: 20_000,
       });

       // Refresh-on-401 retry. Plan 07 adds the CSRF echo interceptor.
       let refreshing: Promise<void> | null = null;
       api.interceptors.response.use(
         (r) => r,
         async (err: AxiosError) => {
           const cfg = err.config as AxiosRequestConfig & { _retry?: boolean };
           if (err.response?.status === 401 && cfg && !cfg._retry) {
             cfg._retry = true;
             refreshing ??= api.post("/auth/refresh").then(() => {}).finally(() => { refreshing = null; });
             try { await refreshing; return api(cfg); } catch { /* fall through */ }
           }
           return Promise.reject(err);
         }
       );
       ```
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $app = Get-Content 'frontend/src/App.tsx' -Raw;
        if ($app -notmatch 'MotionConfig')              { exit 1 };
        if ($app -notmatch 'reducedMotion=\"user\"')    { exit 2 };
        if ($app -notmatch 'SkLed')                     { exit 3 };
        if ($app -notmatch '@/components/skeuomorphic') { Write-Output 'must import via barrel'; exit 4 };
        $i18n = Get-Content 'frontend/src/lib/i18n.ts' -Raw;
        if ($i18n -notmatch 'Denyut Kinerja Pembangkit') { exit 5 };
        if ($i18n -notmatch 'name: \"PULSE\"')           { exit 6 };
        $api = Get-Content 'frontend/src/lib/api.ts' -Raw;
        if ($api -notmatch 'withCredentials: true')      { exit 7 };
        if ($api -notmatch '/auth/refresh')              { exit 8 };
        # Type-check (B-05 + B-06 — real pnpm exec)
        Push-Location frontend
        pnpm exec tsc -b --noEmit 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 9 };
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    App wrapped in MotionConfig reducedMotion='user'; placeholder route renders PULSE name + tagline + heartbeat LED via barrel import; i18n exposes app.name and app.tagline; api.ts has refresh-on-401 interceptor; tsc strict-mode build clean.
  </done>
</task>

<task type="auto">
  <name>Task 3: Six skeuomorphic primitives + barrel + Vitest scaffold (executable vitest verify)</name>
  <files>
    frontend/src/components/skeuomorphic/index.ts,
    frontend/src/components/skeuomorphic/SkLed.tsx,
    frontend/src/components/skeuomorphic/SkButton.tsx,
    frontend/src/components/skeuomorphic/SkPanel.tsx,
    frontend/src/components/skeuomorphic/SkInput.tsx,
    frontend/src/components/skeuomorphic/SkSelect.tsx,
    frontend/src/components/skeuomorphic/SkBadge.tsx,
    frontend/src/components/skeuomorphic/SkLed.test.tsx,
    frontend/src/components/skeuomorphic/SkInput.test.tsx,
    frontend/src/styles/tokens.test.ts
  </files>
  <action>
    1. `frontend/src/components/skeuomorphic/SkLed.tsx`:
       ```tsx
       import { CSSProperties } from "react";
       export interface SkLedProps {
         state: "off" | "on" | "alert";
         color?: "yellow" | "green" | "red";
         label?: string;
         style?: CSSProperties;
       }
       export function SkLed({ state, color = "yellow", label, style }: SkLedProps) {
         const bg = color === "green" ? "var(--sk-lcd-green)"
                  : color === "red"    ? "var(--sk-level-0)"
                                       : "var(--sk-pln-yellow)";
         return (
           <span
             className="sk-led"
             data-state={state}
             data-color={color}
             aria-label={label}
             role={label ? "status" : undefined}
             style={{ background: state === "off" ? undefined : bg, ...style }}
           />
         );
       }
       ```

    2. `frontend/src/components/skeuomorphic/SkButton.tsx` — skeuomorphic button (bevel via box-shadow inset, active state shrinks). Variants `primary | secondary | ghost`. Accessible focus ring via outline. `data-sk="button"`.

    3. `frontend/src/components/skeuomorphic/SkPanel.tsx` — bevel-panel wrapper (inset vs raised). `<div role="group">` if `title` provided.

    4. `frontend/src/components/skeuomorphic/SkInput.tsx` — **W-01 fix** (new):
       ```tsx
       import { forwardRef } from "react";
       export interface SkInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
         invalid?: boolean;
         label?: string;
       }
       export const SkInput = forwardRef<HTMLInputElement, SkInputProps>(
         ({ invalid, label, className = "", style, ...rest }, ref) => {
           const cls = "sk-input " + (invalid ? "sk-input--invalid " : "") + className;
           return (
             <input
               ref={ref}
               data-sk="input"
               aria-invalid={invalid || undefined}
               aria-label={label}
               className={cls}
               style={{
                 background: "var(--sk-surface-2)",
                 color: "var(--sk-text-hi)",
                 border: invalid ? "1px solid var(--sk-level-0)" : "1px solid var(--sk-bevel-light)",
                 borderRadius: 4,
                 padding: "0.5rem 0.75rem",
                 fontFamily: "var(--sk-font-mono)",
                 outline: "none",
                 ...style,
               }}
               {...rest}
             />
           );
         }
       );
       SkInput.displayName = "SkInput";
       ```

    5. `frontend/src/components/skeuomorphic/SkSelect.tsx` — **W-01 fix** (new). Native `<select>` styled with the panel surface tokens; arrow caret via background-image; keyboard nav free.
       ```tsx
       import { forwardRef } from "react";
       export interface SkSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
         invalid?: boolean;
         label?: string;
       }
       export const SkSelect = forwardRef<HTMLSelectElement, SkSelectProps>(
         ({ invalid, label, className = "", style, children, ...rest }, ref) => {
           return (
             <select
               ref={ref}
               data-sk="select"
               aria-invalid={invalid || undefined}
               aria-label={label}
               className={"sk-select " + className}
               style={{
                 background: "var(--sk-surface-2)",
                 color: "var(--sk-text-hi)",
                 border: invalid ? "1px solid var(--sk-level-0)" : "1px solid var(--sk-bevel-light)",
                 borderRadius: 4,
                 padding: "0.5rem 0.75rem",
                 fontFamily: "var(--sk-font-body)",
                 ...style,
               }}
               {...rest}
             >
               {children}
             </select>
           );
         }
       );
       SkSelect.displayName = "SkSelect";
       ```

    6. `frontend/src/components/skeuomorphic/SkBadge.tsx` — **W-01 fix** (new). Status pill for role / state labels.
       ```tsx
       export interface SkBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
         tone?: "neutral" | "info" | "success" | "warning" | "danger";
       }
       const TONE: Record<NonNullable<SkBadgeProps["tone"]>, { fg: string; bg: string }> = {
         neutral: { fg: "var(--sk-text-mid)", bg: "var(--sk-surface-2)" },
         info:    { fg: "#dbeafe",            bg: "var(--sk-pln-blue)" },
         success: { fg: "#0a0e14",            bg: "var(--sk-level-4)" },
         warning: { fg: "#1f1300",            bg: "var(--sk-level-2)" },
         danger:  { fg: "#fff",               bg: "var(--sk-level-0)" },
       };
       export function SkBadge({ tone = "neutral", style, children, ...rest }: SkBadgeProps) {
         const c = TONE[tone];
         return (
           <span
             data-sk="badge"
             data-tone={tone}
             style={{
               display: "inline-flex",
               alignItems: "center",
               padding: "0.125rem 0.5rem",
               borderRadius: 999,
               background: c.bg,
               color: c.fg,
               fontFamily: "var(--sk-font-mono)",
               fontSize: "0.75rem",
               letterSpacing: "0.03em",
               ...style,
             }}
             {...rest}
           >
             {children}
           </span>
         );
       }
       ```

    7. `frontend/src/components/skeuomorphic/index.ts` — **W-10 barrel**:
       ```ts
       export { SkLed }    from "./SkLed";
       export type { SkLedProps } from "./SkLed";
       export { SkButton } from "./SkButton";
       export type { SkButtonProps } from "./SkButton";
       export { SkPanel }  from "./SkPanel";
       export type { SkPanelProps } from "./SkPanel";
       export { SkInput }  from "./SkInput";
       export type { SkInputProps } from "./SkInput";
       export { SkSelect } from "./SkSelect";
       export type { SkSelectProps } from "./SkSelect";
       export { SkBadge }  from "./SkBadge";
       export type { SkBadgeProps } from "./SkBadge";
       ```

    8. `frontend/src/components/skeuomorphic/SkLed.test.tsx` — **B-03 contract test**: alert state's computed glow color differs from healthy:
       ```tsx
       import { render, screen } from "@testing-library/react";
       import { SkLed } from "./SkLed";
       import "../../index.css";   // load tokens + heartbeat CSS so getComputedStyle has values

       describe("SkLed (REQ-pulse-heartbeat-animation, B-03)", () => {
         it("renders with data-state attribute that the heartbeat CSS keyframe targets", () => {
           render(<SkLed state="on" label="system pulse" />);
           const led = screen.getByRole("status");
           expect(led).toHaveAttribute("data-state", "on");
           expect(led.className).toContain("sk-led");
         });

         it("alert state uses red color and the alert keyframe", () => {
           render(<SkLed state="alert" color="red" label="alert" />);
           const led = screen.getByRole("status");
           expect(led).toHaveAttribute("data-state", "alert");
           expect(led).toHaveAttribute("data-color", "red");
         });

         it("off state has data-state=off (CSS disables animation via attribute selector)", () => {
           render(<SkLed state="off" label="off" />);
           const led = screen.getByRole("status");
           expect(led).toHaveAttribute("data-state", "off");
         });

         it("B-03: alert state's computed --sk-led-glow differs from healthy state", () => {
           const { rerender } = render(<SkLed state="on" label="led" />);
           const led = screen.getByRole("status");
           const healthyGlow = getComputedStyle(led).getPropertyValue("--sk-led-glow").trim();
           rerender(<SkLed state="alert" label="led" />);
           const alertGlow = getComputedStyle(led).getPropertyValue("--sk-led-glow").trim();
           // Both must be non-empty AND distinct.
           expect(healthyGlow).not.toBe("");
           expect(alertGlow).not.toBe("");
           expect(alertGlow).not.toBe(healthyGlow);
         });
       });
       ```
       (Note: jsdom does not run CSS animations but does compute custom properties from a stylesheet attached via `import "../../index.css"`. If the CSS-loader doesn't compute attribute-selector custom properties under jsdom, fall back to asserting that `--sk-led-glow` is *declared* differently for `[data-state="on"]` vs `[data-state="alert"]` by parsing the CSS source — same approach as `tokens.test.ts`. Pick whichever passes; both are valid B-03 evidence.)

    9. `frontend/src/components/skeuomorphic/SkInput.test.tsx` — **W-01 contract test**:
       ```tsx
       import { render, screen } from "@testing-library/react";
       import { SkInput } from "./SkInput";

       describe("SkInput (W-01)", () => {
         it("renders an input with data-sk=input and the supplied label as aria-label", () => {
           render(<SkInput label="Email" placeholder="email" />);
           const el = screen.getByLabelText("Email");
           expect(el.tagName.toLowerCase()).toBe("input");
           expect(el).toHaveAttribute("data-sk", "input");
         });

         it("invalid sets aria-invalid", () => {
           render(<SkInput label="Field" invalid />);
           const el = screen.getByLabelText("Field");
           expect(el).toHaveAttribute("aria-invalid", "true");
         });
       });
       ```

    10. `frontend/src/styles/tokens.test.ts` — verify token palette + B-03 alert glow custom property:
        ```ts
        import { readFileSync } from "node:fs";
        import { fileURLToPath } from "node:url";
        import { dirname, resolve } from "node:path";

        const __dir = dirname(fileURLToPath(import.meta.url));
        const css = readFileSync(resolve(__dir, "../index.css"), "utf-8");
        const heartbeat = readFileSync(resolve(__dir, "./pulse-heartbeat.css"), "utf-8");

        const REQUIRED_TOKENS = [
          "--sk-surface-0", "--sk-surface-1", "--sk-surface-2", "--sk-surface-3",
          "--sk-pln-blue", "--sk-pln-yellow", "--sk-pln-yellow-glow",
          "--sk-led-glow", "--sk-led-alert-glow",
          "--sk-level-0", "--sk-level-1", "--sk-level-2", "--sk-level-3", "--sk-level-4",
          "--sk-lcd-green", "--sk-lcd-glow",
          "--sk-font-display", "--sk-font-body", "--sk-font-mono", "--sk-font-lcd",
        ];

        describe("Design tokens (REQ-skeuomorphic-design-system, DEC-003)", () => {
          it.each(REQUIRED_TOKENS)("declares %s", (token) => {
            // Strip /* ... */ comments so a doc-only mention can't satisfy the gate.
            const stripped = css.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
            expect(stripped).toMatch(new RegExp(token + "\\s*:"));
          });

          it("uses PULSE brand identifier, not SISKONKIN (REQ-pulse-branding)", () => {
            const stripped = css.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
            expect(stripped.toLowerCase()).not.toMatch(/siskonkin/);
          });

          it("B-03: declares two distinct heartbeat keyframes (healthy + alert) with distinct glow vars", () => {
            expect(heartbeat).toMatch(/@keyframes\s+pulse-heartbeat-healthy/);
            expect(heartbeat).toMatch(/@keyframes\s+pulse-heartbeat-alert/);
            // Verify per-state custom-property assignment (different glow tokens).
            expect(heartbeat).toMatch(/data-state="on"\][\s\S]*?--sk-led-glow:\s*var\(--sk-pln-yellow-glow\)/);
            expect(heartbeat).toMatch(/data-state="alert"\][\s\S]*?--sk-led-glow:\s*var\(--sk-led-alert-glow\)/);
          });
        });
        ```
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        foreach ($f in 'SkLed','SkButton','SkPanel','SkInput','SkSelect','SkBadge') {
          if (-not (Test-Path ('frontend/src/components/skeuomorphic/' + $f + '.tsx'))) { Write-Output ('missing primitive: ' + $f); exit 1 }
        };
        if (-not (Test-Path 'frontend/src/components/skeuomorphic/index.ts')) { Write-Output 'W-10: missing barrel'; exit 2 };
        $barrel = Get-Content 'frontend/src/components/skeuomorphic/index.ts' -Raw;
        foreach ($n in 'SkLed','SkButton','SkPanel','SkInput','SkSelect','SkBadge') {
          if ($barrel -notmatch ('export.*' + $n)) { Write-Output ('barrel missing: ' + $n); exit 3 }
        };
        if (-not (Test-Path 'frontend/src/components/skeuomorphic/SkLed.test.tsx')) { exit 4 };
        if (-not (Test-Path 'frontend/src/components/skeuomorphic/SkInput.test.tsx')) { exit 5 };
        if (-not (Test-Path 'frontend/src/styles/tokens.test.ts')) { exit 6 };
        # B-06: ACTUALLY run vitest (not ast.parse) — real test execution
        Push-Location frontend
        pnpm exec vitest --run --reporter=basic src/components/skeuomorphic src/styles 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Output 'vitest failed'; exit 7 };
        # B-05: tsc must still pass with the new test files in scope
        pnpm exec tsc -b --noEmit 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 8 };
        Pop-Location
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    All six primitives + barrel exist; SkLed.test asserts data-state contract AND B-03 differing glow color; SkInput.test asserts aria-invalid + data-sk; tokens.test verifies every required CSS custom property + B-03 dual keyframes; vitest passes via real `pnpm exec vitest run`; `tsc -b --noEmit` clean (B-05 + B-06).
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Browser → JS bundle | All client code is untrusted (the user controls the browser); secrets must never live here. |
| Frontend → /api/v1 | Cookie-bearing requests (withCredentials) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-04-S-01 | Spoofing | Storing JWT in localStorage (RESEARCH.md anti-pattern) | mitigate | api.ts uses `withCredentials: true` (cookie path); Plan 07 keeps tokens only in Zustand in-memory. localStorage is forbidden. |
| T-04-T-01 | Tampering | dangerouslySetInnerHTML on server data | mitigate | None used here; eslint rule `react/no-danger` set in Plan 07. |
| T-04-I-01 | Information disclosure | i18n string with secret-looking placeholder | mitigate | i18n keys reviewed; no token/secret patterns. |
| T-04-D-01 | DoS | Animation thrashing under reduced motion | mitigate | `@media (prefers-reduced-motion: reduce)` disables both heartbeat keyframes + `MotionConfig reducedMotion="user"`. |
</threat_model>

<verification>
- `pnpm install` resolves; `pnpm exec vitest --run` passes
- `pnpm exec tsc -b --noEmit` passes (B-05)
- Token CSS variables present in index.css and asserted by tokens.test.ts
- Two heartbeat keyframes (healthy + alert) at 70 BPM / 120 BPM with reduced-motion gate (B-03)
- MotionConfig reducedMotion="user" wraps Router
- All six primitives exported from `@/components/skeuomorphic` barrel (W-01 + W-10)
- No `siskonkin` in any file
</verification>

<success_criteria>
- React 18.3.x, react-router-dom ^6.30, motion ^12, tailwindcss ^4 pinned exactly
- Skeuomorphic token palette (DEC-003 full set + B-03 glow vars) in `:root`
- Two Pulse Heartbeat keyframes (healthy/alert) — visible on day one
- i18n lookup map covers Phase-1 string set
- Six skeuomorphic primitives (W-01) + barrel index.ts (W-10)
- Vitest globals + jest-dom types resolved (B-05)
- Wave 0 dep install + vitest smoke passing (B-06)
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-master-data-auth/01-04-SUMMARY.md` listing:
1. Final dependency pin table (read back from `package.json`)
2. tsconfig.app.json compilerOptions.types contents (B-05 evidence)
3. Token palette table (token name → value → DEC-003 mapping, including the new `--sk-led-glow` and `--sk-led-alert-glow`)
4. Two heartbeat keyframe definitions side-by-side (B-03 evidence)
5. Vitest run output (real test count + duration; not ast-only)
6. Six primitive public APIs (for Plan 07 to consume via barrel)
</output>
