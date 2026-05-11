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
 * Plan 07 will add:
 * - Request interceptor that echoes the CSRF cookie value into X-CSRF-Token (B-07).
 * - Zustand auth store wired here to clear in-memory user state when refresh fails.
 */

export const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
  timeout: 20_000,
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
