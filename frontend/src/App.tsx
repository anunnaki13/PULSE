import { MotionConfig } from "motion/react";
import { Routes, Route, Navigate } from "react-router-dom";
import { t } from "@/lib/i18n";
import { SkLed } from "@/components/skeuomorphic";

/**
 * PULSE root component.
 *
 * MotionConfig reducedMotion="user" wraps the entire tree so every framer-motion
 * (Motion v12) component automatically honors `prefers-reduced-motion`. The CSS
 * heartbeat keyframes in pulse-heartbeat.css have a parallel @media gate.
 *
 * Wave-5 placeholder landing route — Plan 07 replaces this with the full
 * Login / Dashboard / Master Data routes. The placeholder still satisfies
 * ROADMAP success criterion #3 by showing PULSE name, tagline, and the
 * heartbeat LED on day one.
 */
export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      <Routes>
        <Route
          path="/"
          element={
            <main
              style={{
                display: "grid",
                placeItems: "center",
                height: "100vh",
                gap: "1rem",
                padding: "2rem",
                textAlign: "center",
              }}
            >
              <h1
                style={{
                  fontFamily: "var(--sk-font-display)",
                  fontSize: "4rem",
                  margin: 0,
                  letterSpacing: "0.05em",
                  color: "var(--sk-pln-yellow)",
                }}
              >
                {t("app.name")}
              </h1>
              <p style={{ color: "var(--sk-text-mid)", margin: 0 }}>{t("app.tagline")}</p>
              <SkLed state="on" label="System pulse" />
            </main>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </MotionConfig>
  );
}
