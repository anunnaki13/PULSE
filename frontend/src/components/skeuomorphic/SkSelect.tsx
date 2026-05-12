import { forwardRef } from "react";
import type { SelectHTMLAttributes } from "react";

export interface SkSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  /** Marks the field as invalid — renders a red border + sets aria-invalid="true". */
  invalid?: boolean;
  /** Accessible label; sets aria-label so screen readers identify the control. */
  label?: string;
}

/**
 * SkSelect — skeuomorphic native-select wrapper (Phase-1 primitive, W-01).
 *
 * Native `<select>` keeps free keyboard navigation (arrow keys, type-to-select,
 * Escape to close) and platform-native option lists. We style the trigger to
 * match SkInput's recessed-into-panel look; the option list is browser-controlled.
 *
 * forwardRef lets react-hook-form register the control directly.
 */
export const SkSelect = forwardRef<HTMLSelectElement, SkSelectProps>(function SkSelect(
  { invalid, label, className = "", style, children, ...rest },
  ref,
) {
  return (
    <select
      ref={ref}
      data-sk="select"
      aria-invalid={invalid || undefined}
      aria-label={label}
      className={"sk-select " + className}
      style={{
        background: "var(--sk-surface-2)",
        color: "var(--sk-text-hi)",
        border: invalid ? "1px solid var(--sk-level-0)" : "1px solid rgba(96, 112, 134, 0.28)",
        borderRadius: 6,
        padding: "0.5rem 0.75rem",
        fontFamily: "var(--sk-font-body)",
        outline: "none",
        boxShadow: "inset 0 2px 5px rgba(74, 92, 112, 0.12), inset 0 -1px 0 rgba(255,255,255,0.75)",
        ...style,
      }}
      {...rest}
    >
      {children}
    </select>
  );
});
