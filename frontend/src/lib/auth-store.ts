/**
 * PULSE Zustand auth store.
 *
 * Threat T-07-S-01 (Spoofing — Token in localStorage): tokens are kept in
 * memory only. The `access_token` cookie carries the bearer for browser
 * requests (set httpOnly by the backend); this store mirrors the user and
 * the token string in memory ONLY for the duration of the SPA session.
 * Refresh-on-page-load is handled via `hydrateFromCookie()` which calls
 * `/auth/me` on app boot — the httpOnly cookies do the work, no localStorage.
 *
 * NEVER add `persist(...)` middleware to this store. NEVER read/write
 * `localStorage` or `sessionStorage` for tokens. The verifier asserts these
 * strings are absent from this file.
 */
import { create } from "zustand";
import type { UserPublic } from "@/types";
import { api } from "./api";

interface AuthState {
  user: UserPublic | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  /** Set the session from an external source (e.g. login response). */
  setSession(user: UserPublic, accessToken: string): void;
  /** POST /auth/login + populate session on 200. Throws on 401. */
  login(email: string, password: string): Promise<void>;
  /** POST /auth/logout (best-effort) + clear in-memory session. */
  logout(): Promise<void>;
  /**
   * GET /auth/me on app boot. If the httpOnly access_token cookie is still
   * valid, this populates `user` and flips `isAuthenticated` to true.
   * Silent on 401 — user just stays logged out.
   */
  hydrateFromCookie(): Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,

  setSession: (user, accessToken) =>
    set({ user, accessToken, isAuthenticated: true }),

  async login(email, password) {
    const { data } = await api.post("/auth/login", { email, password });
    // Backend returns { access_token, refresh_token, user }. We keep the
    // access_token in memory for Bearer-mode header echoes (used by tests),
    // but the httpOnly cookie is the authoritative auth carrier.
    set({
      user: data.user as UserPublic,
      accessToken: data.access_token as string,
      isAuthenticated: true,
    });
    api.defaults.headers.common.Authorization = `Bearer ${data.access_token}`;
  },

  async logout() {
    try {
      await api.post("/auth/logout");
    } catch {
      // Best-effort: server may already have revoked or the cookies expired.
      // Either way, scrub local state.
    }
    delete api.defaults.headers.common.Authorization;
    set({ user: null, accessToken: null, isAuthenticated: false });
  },

  async hydrateFromCookie() {
    try {
      const { data } = await api.get("/auth/me");
      set({ user: data as UserPublic, isAuthenticated: true });
    } catch {
      // Not authenticated — stay logged out. Login flow takes care of the rest.
    }
  },
}));
