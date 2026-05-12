/**
 * PULSE skeuomorphic primitive barrel (W-10).
 *
 * Plan 07 (Login + master screens) consumes these via:
 *   import { SkLed, SkButton, SkPanel, SkInput, SkSelect, SkBadge } from "@/components/skeuomorphic";
 *
 * Phase-1 set (W-01): six primitives. Deferred per CONTEXT.md §Design System:
 *   - SkScreenLcd, SkDial, SkGauge → Phase 3 (dashboards)
 *   - SkSlider, SkToggle           → Phase 2 (assessment forms)
 */
export { SkLed } from "./SkLed";
export type { SkLedProps } from "./SkLed";

export { SkButton } from "./SkButton";
export type { SkButtonProps } from "./SkButton";

export { SkPanel } from "./SkPanel";
export type { SkPanelProps } from "./SkPanel";

export { SkInput } from "./SkInput";
export type { SkInputProps } from "./SkInput";

export { SkSelect } from "./SkSelect";
export type { SkSelectProps } from "./SkSelect";

export { SkBadge } from "./SkBadge";
export type { SkBadgeProps } from "./SkBadge";

export { SkSlider } from "./SkSlider";
export type { SkSliderProps } from "./SkSlider";

export { SkToggle } from "./SkToggle";
export type { SkToggleProps } from "./SkToggle";

export { SkLevelSelector } from "./SkLevelSelector";
export type { SkLevelSelectorProps } from "./SkLevelSelector";
