import type { HTMLAttributes, CSSProperties } from "react";

export interface SkPanelProps extends HTMLAttributes<HTMLDivElement> {
  /** `true` = inset (sunken well); `false`/omitted = raised (control-room panel). */
  inset?: boolean;
  /** Optional panel header — renders a small caption strip above the content. */
  title?: string;
}

/**
 * SkPanel — skeuomorphic bevel-panel wrapper (Phase-1 primitive, W-01).
 *
 * Raised panel: outer light bevel + inner shadow on bottom — reads as a physical
 * control-room module. Inset panel: inverted bevel — reads as a recessed well
 * (used for LCD screens, drawer interiors, etc.).
 *
 * When `title` is provided the panel becomes role=group with aria-label set to
 * the title so screen readers announce the section name.
 */
export function SkPanel({ inset, title, className = "", style, children, ...rest }: SkPanelProps) {
  const raisedShadow =
    "inset 0 1px 0 var(--sk-bevel-light), 0 2px 6px var(--sk-bevel-dark)";
  const insetShadow =
    "inset 0 2px 6px var(--sk-bevel-dark), inset 0 -1px 0 var(--sk-bevel-light)";

  const panelStyle: CSSProperties = {
    background: inset ? "var(--sk-surface-1)" : "var(--sk-surface-2)",
    border: "1px solid var(--sk-bevel-dark)",
    borderRadius: 8,
    padding: "1rem",
    boxShadow: inset ? insetShadow : raisedShadow,
    color: "var(--sk-text-hi)",
    ...style,
  };

  return (
    <div
      data-sk="panel"
      data-inset={inset ? "true" : "false"}
      role={title ? "group" : undefined}
      aria-label={title}
      className={"sk-panel " + className}
      style={panelStyle}
      {...rest}
    >
      {title && (
        <div
          style={{
            fontFamily: "var(--sk-font-display)",
            fontSize: "0.875rem",
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--sk-text-mid)",
            marginBottom: "0.5rem",
            borderBottom: "1px solid var(--sk-bevel-dark)",
            paddingBottom: "0.25rem",
          }}
        >
          {title}
        </div>
      )}
      {children}
    </div>
  );
}
