import { forwardRef } from "react";
import type { ButtonHTMLAttributes } from "react";

export interface SkToggleProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "onChange"> {
  checked: boolean;
  label: string;
  onCheckedChange?: (checked: boolean) => void;
}

export const SkToggle = forwardRef<HTMLButtonElement, SkToggleProps>(function SkToggle(
  { checked, label, onCheckedChange, className = "", style, disabled, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      data-sk="toggle"
      data-state={checked ? "on" : "off"}
      className={"sk-toggle " + className}
      onClick={(event) => {
        rest.onClick?.(event);
        if (!event.defaultPrevented && !disabled) onCheckedChange?.(!checked);
      }}
      style={{
        width: 54,
        height: 30,
        borderRadius: 6,
        border: "1px solid var(--sk-bevel-dark)",
        background: checked ? "var(--sk-level-4)" : "var(--sk-surface-3)",
        boxShadow:
          "inset 0 1px 0 var(--sk-bevel-light), inset 0 -2px 5px rgba(74, 92, 112, 0.22)",
        padding: 3,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.55 : 1,
        ...style,
      }}
      {...rest}
    >
      <span
        aria-hidden="true"
        style={{
          display: "block",
          width: 22,
          height: 22,
          borderRadius: 4,
          transform: checked ? "translateX(24px)" : "translateX(0)",
          background: "var(--sk-surface-2)",
          boxShadow: "0 2px 5px rgba(74, 92, 112, 0.28), inset 0 1px 0 var(--sk-bevel-light)",
          transition: "transform 120ms ease-out",
        }}
      />
    </button>
  );
});
