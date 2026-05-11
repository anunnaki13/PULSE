import { forwardRef } from "react";
import type { ButtonHTMLAttributes, CSSProperties } from "react";

export interface SkButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** "primary" = PLN-yellow CTA, "secondary" = surface-3 quiet, "ghost" = transparent. */
  variant?: "primary" | "secondary" | "ghost";
  /** Force the pressed/active visual; useful for toggle-style buttons. */
  pressed?: boolean;
}

/**
 * SkButton — skeuomorphic tactile button (Phase-1 primitive, W-01).
 *
 * Bevel effect uses box-shadow inset (top-light + bottom-shadow) so the button
 * reads as a physical key. Pressed/:active state inverts the bevel and shrinks
 * 1px, mimicking a depressed switch. Accessible focus ring via outline so the
 * tactile shadow stack stays intact during keyboard nav.
 */
export const SkButton = forwardRef<HTMLButtonElement, SkButtonProps>(function SkButton(
  { variant = "primary", pressed, className = "", style, type = "button", children, ...rest },
  ref,
) {
  // Palette-by-variant: primary uses PLN brand yellow; secondary stays in surface
  // tokens; ghost has zero background until hover/active.
  const palette: Record<NonNullable<SkButtonProps["variant"]>, { bg: string; fg: string }> = {
    primary: { bg: "var(--sk-pln-yellow)", fg: "#0a0e14" },
    secondary: { bg: "var(--sk-surface-3)", fg: "var(--sk-text-hi)" },
    ghost: { bg: "transparent", fg: "var(--sk-text-hi)" },
  };
  const tone = palette[variant];

  // Bevel shadow stack: top-inner light + bottom-inner dark = raised key. When
  // pressed, swap the stack to push the bevel inward (sunk key).
  const raisedShadow =
    "inset 0 1px 0 var(--sk-bevel-light), inset 0 -2px 4px var(--sk-bevel-dark), 0 1px 2px rgba(0,0,0,0.35)";
  const sunkShadow =
    "inset 0 -1px 0 var(--sk-bevel-light), inset 0 2px 6px var(--sk-bevel-dark)";

  const visualStyle: CSSProperties = {
    background: tone.bg,
    color: tone.fg,
    border: "1px solid var(--sk-bevel-dark)",
    borderRadius: 6,
    padding: "0.5rem 1rem",
    fontFamily: "var(--sk-font-body)",
    fontWeight: 600,
    letterSpacing: "0.02em",
    cursor: "pointer",
    transform: pressed ? "translateY(1px)" : undefined,
    boxShadow: pressed ? sunkShadow : raisedShadow,
    transition: "transform 80ms ease-out, box-shadow 80ms ease-out",
    outlineOffset: 2,
    ...style,
  };

  return (
    <button
      ref={ref}
      type={type}
      data-sk="button"
      data-variant={variant}
      aria-pressed={pressed}
      className={"sk-button " + className}
      style={visualStyle}
      {...rest}
    >
      {children}
    </button>
  );
});
