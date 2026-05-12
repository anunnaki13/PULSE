import { SkButton } from "./SkButton";
import { SkLed } from "./SkLed";

export interface SkLevelSelectorProps {
  value: number;
  onChange: (value: number) => void;
  label?: string;
  disabled?: boolean;
}

const levels = [0, 1, 2, 3, 4];

export function SkLevelSelector({ value, onChange, label = "Level maturity", disabled }: SkLevelSelectorProps) {
  return (
    <div data-sk="level-selector" aria-label={label} style={{ display: "grid", gap: "0.5rem" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "0.35rem" }}>
        {levels.map((level) => (
          <SkLed
            key={level}
            state={value === level ? "on" : "off"}
            label={`Level ${level}`}
            color={level >= 3 ? "green" : level === 2 ? "yellow" : "red"}
            style={{ justifySelf: "center" }}
          />
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, minmax(46px, 1fr))", gap: "0.35rem" }}>
        {levels.map((level) => (
          <SkButton
            key={level}
            variant={value === level ? "primary" : "secondary"}
            pressed={value === level}
            disabled={disabled}
            onClick={() => onChange(level)}
            style={{ paddingInline: "0.5rem" }}
          >
            L{level}
          </SkButton>
        ))}
      </div>
    </div>
  );
}
