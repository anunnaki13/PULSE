import { forwardRef } from "react";
import type { InputHTMLAttributes } from "react";

export interface SkSliderProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
}

export const SkSlider = forwardRef<HTMLInputElement, SkSliderProps>(function SkSlider(
  { label, className = "", style, min = 0, max = 100, step = 1, ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      type="range"
      aria-label={label}
      min={min}
      max={max}
      step={step}
      data-sk="slider"
      className={"sk-slider " + className}
      style={{
        width: "100%",
        accentColor: "var(--sk-pln-blue)",
        ...style,
      }}
      {...rest}
    />
  );
});
