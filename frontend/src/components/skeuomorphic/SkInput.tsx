import { forwardRef } from "react";
import type { InputHTMLAttributes } from "react";

export interface SkInputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Marks the field as invalid — renders a red border + sets aria-invalid="true". */
  invalid?: boolean;
  /** Accessible label; sets aria-label so screen readers identify the field. */
  label?: string;
}

/**
 * SkInput — skeuomorphic text input (Phase-1 primitive, W-01).
 *
 * Recessed look: surface-2 background + dark border for the "carved-into-panel"
 * feel. Mono font echoes the control-room aesthetic. forwardRef enables
 * react-hook-form's `register(...)` to attach the ref.
 *
 * When `invalid` is set, the border switches to level-0 red and aria-invalid
 * goes to "true" so assistive tech announces the validation state.
 */
export const SkInput = forwardRef<HTMLInputElement, SkInputProps>(function SkInput(
  { invalid, label, className = "", style, ...rest },
  ref,
) {
  const cls = "sk-input " + (invalid ? "sk-input--invalid " : "") + className;
  return (
    <input
      ref={ref}
      data-sk="input"
      aria-invalid={invalid || undefined}
      aria-label={label}
      className={cls}
      style={{
        background: "var(--sk-surface-2)",
        color: "var(--sk-text-hi)",
        border: invalid ? "1px solid var(--sk-level-0)" : "1px solid var(--sk-bevel-light)",
        borderRadius: 4,
        padding: "0.5rem 0.75rem",
        fontFamily: "var(--sk-font-mono)",
        outline: "none",
        ...style,
      }}
      {...rest}
    />
  );
});
