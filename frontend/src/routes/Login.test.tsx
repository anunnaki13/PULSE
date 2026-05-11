/**
 * REQ-pulse-branding + REQ-pulse-heartbeat-animation + W-01 contract test.
 *
 * Covers:
 *   - "PULSE" brand string visible
 *   - BI tagline visible ("Denyut Kinerja Pembangkit, Real-Time.")
 *   - Heartbeat LED rendered with [data-state="on"]
 *   - W-01: every <input> on this page has data-sk="input" (i.e. came from
 *     SkInput, not raw <input>); every <button> has data-sk="button" (i.e.
 *     came from SkButton, not raw <button>).
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Login from "@/routes/Login";
import { useAuthStore } from "@/lib/auth-store";

function TestWrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/login"]}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Login screen (REQ-pulse-branding, REQ-pulse-heartbeat-animation, W-01)", () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, accessToken: null, isAuthenticated: false });
  });

  it("renders the PULSE brand string", () => {
    render(<Login />, { wrapper: TestWrapper });
    // BI title and brand wordmark both appear; assert the brand is present.
    expect(screen.getAllByText("PULSE").length).toBeGreaterThan(0);
  });

  it("renders the BI tagline 'Denyut Kinerja Pembangkit, Real-Time.'", () => {
    render(<Login />, { wrapper: TestWrapper });
    expect(screen.getByText("Denyut Kinerja Pembangkit, Real-Time.")).toBeInTheDocument();
  });

  it("renders an LED with [data-state='on'] (heartbeat)", () => {
    const { container } = render(<Login />, { wrapper: TestWrapper });
    const led = container.querySelector('[data-state="on"]');
    expect(led).not.toBeNull();
  });

  it("W-01: every <input> on Login comes from SkInput (has data-sk='input')", () => {
    const { container } = render(<Login />, { wrapper: TestWrapper });
    const inputs = container.querySelectorAll("input");
    expect(inputs.length).toBeGreaterThan(0);
    inputs.forEach((el) => {
      expect(el).toHaveAttribute("data-sk", "input");
    });
  });

  it("W-01: every <button> on Login comes from SkButton (has data-sk='button')", () => {
    const { container } = render(<Login />, { wrapper: TestWrapper });
    const buttons = container.querySelectorAll("button");
    expect(buttons.length).toBeGreaterThan(0);
    buttons.forEach((el) => {
      expect(el).toHaveAttribute("data-sk", "button");
    });
  });

  it("W-01: no raw <select> rendered on Login", () => {
    const { container } = render(<Login />, { wrapper: TestWrapper });
    expect(container.querySelectorAll("select").length).toBe(0);
  });
});
