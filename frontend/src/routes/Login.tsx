/**
 * PULSE Login screen (REQ-pulse-branding + REQ-pulse-heartbeat-animation +
 * REQ-route-guards entry point).
 *
 * W-01 contract: form controls use ONLY skeuomorphic primitives via the
 * `@/components/skeuomorphic` barrel (W-10). No raw `<input>` / `<select>` /
 * `<button>` tags allowed on this page. Semantic tags (`<form>`, `<header>`,
 * `<label>`, `<span>`, `<p>`, `<h1>`, `<main>`) are still permitted — the
 * ban applies specifically to form-control HTML primitives that have a Sk*
 * equivalent.
 *
 * The "Pulse Heartbeat" LED (`SkLed state="on"`) animates at ~70 BPM via the
 * `pulse-heartbeat-healthy` keyframe defined in `pulse-heartbeat.css`. The
 * tagline "Denyut Kinerja Pembangkit, Real-Time." comes from the
 * `app.tagline` i18n key (BI default per CONSTR-i18n-default).
 */
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { useAuthStore } from "@/lib/auth-store";
import { t } from "@/lib/i18n";
import { SkLed, SkButton, SkPanel, SkInput } from "@/components/skeuomorphic";

const LoginSchema = z.object({
  email: z
    .string()
    .min(1, "Email wajib diisi")
    // Backend uses regex (not pydantic EmailStr — accepts .local TLDs); mirror the
    // shape check client-side for fast feedback. Server is still the source of truth.
    .regex(/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/, "Format email tidak valid"),
  password: z.string().min(1, "Kata sandi wajib diisi"),
});
type LoginForm = z.infer<typeof LoginSchema>;

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((s) => s.login);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(LoginSchema) });

  const onSubmit = async (data: LoginForm) => {
    try {
      await login(data.email, data.password);
      // Preserve deep link if the user was bounced here by the auth gate.
      const fromLocation = (location.state as { from?: { pathname?: string } } | null)?.from;
      const to = fromLocation?.pathname ?? "/dashboard";
      navigate(to, { replace: true });
    } catch {
      toast.error(t("login.wrong"));
    }
  };

  return (
    <main
      style={{
        display: "grid",
        placeItems: "center",
        minHeight: "100vh",
        background: "var(--sk-surface-0)",
        padding: "2rem",
      }}
    >
      <SkPanel
        title={t("login.title")}
        style={{ width: "min(420px, 100%)", padding: "2rem" }}
      >
        <header
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            marginBottom: "0.5rem",
          }}
        >
          {/* B-03 + REQ-pulse-heartbeat-animation: the [data-state="on"] LED
              pulses at 70 BPM via pulse-heartbeat-healthy keyframe. */}
          <SkLed state="on" label={t("app.name") + " heartbeat"} />
          <h1
            style={{
              fontFamily: "var(--sk-font-display)",
              fontSize: "3rem",
              margin: 0,
              letterSpacing: "0.05em",
              color: "var(--sk-pln-yellow)",
            }}
          >
            {t("app.name")}
          </h1>
        </header>

        {/* REQ-pulse-branding success criterion #3: tagline visible on day one. */}
        <p style={{ color: "var(--sk-text-mid)", marginTop: 0, marginBottom: "1.5rem" }}>
          {t("app.tagline")}
        </p>

        <form onSubmit={handleSubmit(onSubmit)} style={{ display: "grid", gap: "0.75rem" }}>
          <label style={{ display: "grid", gap: "0.25rem" }}>
            <span style={{ color: "var(--sk-text-mid)", fontSize: "0.875rem" }}>
              {t("login.username")}
            </span>
            {/* W-01: SkInput, not raw <input>. */}
            <SkInput
              type="email"
              autoComplete="email"
              invalid={!!errors.email}
              {...register("email")}
            />
            {errors.email && (
              <span role="alert" style={{ color: "var(--sk-level-0)", fontSize: "0.75rem" }}>
                {errors.email.message}
              </span>
            )}
          </label>

          <label style={{ display: "grid", gap: "0.25rem" }}>
            <span style={{ color: "var(--sk-text-mid)", fontSize: "0.875rem" }}>
              {t("login.password")}
            </span>
            {/* W-01: SkInput, not raw <input>. */}
            <SkInput
              type="password"
              autoComplete="current-password"
              invalid={!!errors.password}
              {...register("password")}
            />
            {errors.password && (
              <span role="alert" style={{ color: "var(--sk-level-0)", fontSize: "0.75rem" }}>
                {errors.password.message}
              </span>
            )}
          </label>

          {/* W-01: SkButton, not raw <button>. */}
          <SkButton
            type="submit"
            variant="primary"
            disabled={isSubmitting}
            style={{ marginTop: "0.5rem" }}
          >
            {isSubmitting ? t("common.loading") : t("login.submit")}
          </SkButton>
        </form>
      </SkPanel>
    </main>
  );
}
