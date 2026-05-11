/**
 * REQ-route-guards (frontend half) — spec-name verification.
 *
 * Covers every relevant transition for the six spec roles:
 *   - unauthenticated     → /login
 *   - admin_unit on /master/* → renders Outlet (admin gate pass)
 *   - super_admin on /master/* → renders Outlet (admin gate pass)
 *   - pic_bidang on /master/*  → /dashboard (admin gate redirect)
 *   - manajer_unit on /master/* → /dashboard (admin gate redirect)
 *
 * B-01/B-02: every Role string used here is one of the six spec names. No
 * capitalized aliases.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { useAuthStore } from "@/lib/auth-store";
import type { Role, UserPublic } from "@/types";

function makeUser(roles: Role[]): UserPublic {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    email: "test@pulse.local",
    full_name: "Test",
    is_active: true,
    bidang_id: null,
    roles,
  };
}

function renderAt(initialEntry: string, allow?: Role[]) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/login" element={<div data-testid="login-screen">LOGIN</div>} />
        <Route path="/dashboard" element={<div data-testid="dashboard-screen">DASHBOARD</div>} />
        <Route element={<ProtectedRoute allow={allow} />}>
          <Route path="/master" element={<div data-testid="master-screen">MASTER</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute (REQ-route-guards, B-01/B-02)", () => {
  beforeEach(() => {
    // Reset store between tests so prior auth state doesn't leak.
    useAuthStore.setState({ user: null, accessToken: null, isAuthenticated: false });
  });

  it("redirects unauthenticated user to /login", () => {
    renderAt("/master");
    expect(screen.getByTestId("login-screen")).toBeInTheDocument();
  });

  it("admin_unit reaches /master/* (admin gate pass)", () => {
    useAuthStore.setState({
      user: makeUser(["admin_unit"]),
      accessToken: "stub",
      isAuthenticated: true,
    });
    renderAt("/master", ["super_admin", "admin_unit"]);
    expect(screen.getByTestId("master-screen")).toBeInTheDocument();
  });

  it("super_admin reaches /master/* (admin gate pass)", () => {
    useAuthStore.setState({
      user: makeUser(["super_admin"]),
      accessToken: "stub",
      isAuthenticated: true,
    });
    renderAt("/master", ["super_admin", "admin_unit"]);
    expect(screen.getByTestId("master-screen")).toBeInTheDocument();
  });

  it("pic_bidang on /master/* → redirected to /dashboard", () => {
    useAuthStore.setState({
      user: makeUser(["pic_bidang"]),
      accessToken: "stub",
      isAuthenticated: true,
    });
    renderAt("/master", ["super_admin", "admin_unit"]);
    expect(screen.getByTestId("dashboard-screen")).toBeInTheDocument();
  });

  it("manajer_unit on /master/* → redirected to /dashboard", () => {
    useAuthStore.setState({
      user: makeUser(["manajer_unit"]),
      accessToken: "stub",
      isAuthenticated: true,
    });
    renderAt("/master", ["super_admin", "admin_unit"]);
    expect(screen.getByTestId("dashboard-screen")).toBeInTheDocument();
  });

  it("asesor on /master/* → redirected to /dashboard", () => {
    useAuthStore.setState({
      user: makeUser(["asesor"]),
      accessToken: "stub",
      isAuthenticated: true,
    });
    renderAt("/master", ["super_admin", "admin_unit"]);
    expect(screen.getByTestId("dashboard-screen")).toBeInTheDocument();
  });

  it("viewer on /master/* → redirected to /dashboard", () => {
    useAuthStore.setState({
      user: makeUser(["viewer"]),
      accessToken: "stub",
      isAuthenticated: true,
    });
    renderAt("/master", ["super_admin", "admin_unit"]);
    expect(screen.getByTestId("dashboard-screen")).toBeInTheDocument();
  });
});
