import axios from "axios";
import type { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from "axios";

/**
 * PULSE axios instance.
 *
 * Auth model (per CONTEXT.md §Auth + threat T-04-S-01):
 * - withCredentials: true → cookies (httpOnly access + refresh) carried automatically.
 * - JWT tokens NEVER stored in localStorage (anti-pattern per RESEARCH.md).
 * - On 401, attempt POST /auth/refresh exactly once per failed request, then retry.
 *   The refresh promise is shared so concurrent 401s coalesce into a single refresh call.
 *
 * B-07 fix (Plan 07): request interceptor reads the `csrf_token` cookie (set
 * NOT-httpOnly by the backend specifically so the SPA can read it) and echoes
 * it as the `X-CSRF-Token` header on every mutating verb (POST/PUT/PATCH/
 * DELETE). The backend `require_csrf` dep does a constant-time compare of
 * cookie ⇔ header. Bearer-only callers (tests, server-to-server) skip CSRF
 * server-side via `require_csrf`'s standard rule, so the missing header is
 * not a problem in those flows.
 */

export const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
  timeout: 20_000,
});

/**
 * Read a cookie value by name. Returns null if missing.
 * Used by the CSRF interceptor to echo `csrf_token` → `X-CSRF-Token`.
 */
function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") + "=([^;]*)"),
  );
  return match ? decodeURIComponent(match[1]) : null;
}

// B-07: echo CSRF token on every mutating verb. Bearer-only callers are
// transparent because they don't have a csrf_token cookie set; the
// server-side `require_csrf` allow-passes them by sniffing the Authorization
// header.
api.interceptors.request.use((cfg) => {
  const method = (cfg.method ?? "").toLowerCase();
  if (method === "post" || method === "put" || method === "patch" || method === "delete") {
    const csrf = getCookie("csrf_token");
    if (csrf) {
      // AxiosHeaders or plain object — set() exists on both since axios 1.x.
      if (cfg.headers && typeof (cfg.headers as { set?: unknown }).set === "function") {
        (cfg.headers as { set: (k: string, v: string) => void }).set("X-CSRF-Token", csrf);
      } else {
        (cfg.headers as Record<string, string>) = {
          ...(cfg.headers as Record<string, string>),
          "X-CSRF-Token": csrf,
        };
      }
    }
  }
  return cfg;
});

// Singleton refresh promise so N concurrent 401s share ONE /auth/refresh call.
let refreshing: Promise<void> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (err: AxiosError) => {
    const cfg = err.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined;

    // Refresh-on-401 path: at most one retry per original request.
    if (err.response?.status === 401 && cfg && !cfg._retry) {
      cfg._retry = true;

      if (refreshing === null) {
        refreshing = api
          .post("/auth/refresh")
          .then(() => {
            /* swallow body — Set-Cookie does the work */
          })
          .finally(() => {
            refreshing = null;
          });
      }

      try {
        await refreshing;
        // Replay the original request with the (now refreshed) cookie.
        return api(cfg as InternalAxiosRequestConfig);
      } catch {
        // Refresh itself failed → propagate the original 401 unchanged.
      }
    }

    return Promise.reject(err);
  },
);
