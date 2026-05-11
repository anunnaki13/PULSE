import type { CSSProperties } from "react";

export interface SkLedProps {
  /** "off" = no glow, "on" = healthy heartbeat (yellow, 70 BPM), "alert" = red alert (120 BPM). */
  state: "off" | "on" | "alert";
  /** Override the LED body color. Default = "yellow" (PLN brand). */
  color?: "yellow" | "green" | "red";
  /** Visually-hidden accessible name; sets aria-label + role=status when provided. */
  label?: string;
  /** Optional style merge — useful for layout positioning. */
  style?: CSSProperties;
}

/**
 * SkLed — skeuomorphic indicator LED (Phase-1 primitive, W-01).
 *
 * State drives the heartbeat CSS via the [data-state="..."] attribute selectors
 * defined in src/styles/pulse-heartbeat.css. Each state also sets a distinct
 * --sk-led-glow custom property so getComputedStyle yields per-state glow color
 * (B-03 contract).
 *
 * Reduced-motion gate: the @media (prefers-reduced-motion: reduce) rule in
 * pulse-heartbeat.css disables the animation regardless of state.
 */
export function SkLed({ state, color = "yellow", label, style }: SkLedProps) {
  // Body color follows the `color` prop; the keyframe glow is parameterized
  // independently via --sk-led-glow so alert glow stays red even if color=yellow.
  const bg =
    state === "off"
      ? undefined // CSS rule for [data-state="off"] sets background to text-lo.
      : color === "green"
        ? "var(--sk-lcd-green)"
        : color === "red"
          ? "var(--sk-level-0)"
          : "var(--sk-pln-yellow)";

  return (
    <span
      className="sk-led"
      data-state={state}
      data-color={color}
      aria-label={label}
      role={label ? "status" : undefined}
      style={bg ? { background: bg, ...style } : style}
    />
  );
}
