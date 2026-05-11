import type { HTMLAttributes } from "react";

export interface SkBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  /** Semantic tone — drives bg/fg color from the level palette. */
  tone?: "neutral" | "info" | "success" | "warning" | "danger";
}

/**
 * SkBadge — skeuomorphic status / role pill (Phase-1 primitive, W-01).
 *
 * Used for the six role labels (super_admin, admin_unit, pic_bidang, asesor,
 * manajer_unit, viewer) on the user list, plus stream-status labels on the
 * master-data browse screens. Tones map to the DEC-003 level palette so the
 * meaning stays consistent with NKO indicator colors elsewhere.
 */
const TONE: Record<NonNullable<SkBadgeProps["tone"]>, { fg: string; bg: string }> = {
  neutral: { fg: "var(--sk-text-mid)", bg: "var(--sk-surface-2)" },
  info: { fg: "#dbeafe", bg: "var(--sk-pln-blue)" },
  success: { fg: "#0a0e14", bg: "var(--sk-level-4)" },
  warning: { fg: "#1f1300", bg: "var(--sk-level-2)" },
  danger: { fg: "#ffffff", bg: "var(--sk-level-0)" },
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
