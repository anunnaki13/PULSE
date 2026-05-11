import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

// __dirname shim for ESM contexts (vitest runs the suite under ESM).
const __dir = dirname(fileURLToPath(import.meta.url));
const css = readFileSync(resolve(__dir, "../index.css"), "utf-8");
const heartbeat = readFileSync(resolve(__dir, "./pulse-heartbeat.css"), "utf-8");

// All DEC-003 + B-03 tokens that the design system contract requires.
const REQUIRED_TOKENS = [
  "--sk-surface-0",
  "--sk-surface-1",
  "--sk-surface-2",
  "--sk-surface-3",
  "--sk-pln-blue",
  "--sk-pln-yellow",
  "--sk-pln-yellow-glow",
  "--sk-led-glow",
  "--sk-led-alert-glow",
  "--sk-level-0",
  "--sk-level-1",
  "--sk-level-2",
  "--sk-level-3",
  "--sk-level-4",
  "--sk-lcd-green",
  "--sk-lcd-glow",
  "--sk-font-display",
  "--sk-font-body",
  "--sk-font-mono",
  "--sk-font-lcd",
];

// Strip /* block */ and // line comments so a doc-only mention can't satisfy
// the gate. We require a real declaration `--foo: ...;`.
const stripComments = (source: string) =>
  source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");

describe("Design tokens (REQ-skeuomorphic-design-system, DEC-003)", () => {
  it.each(REQUIRED_TOKENS)("declares %s in :root", (token) => {
    const stripped = stripComments(css);
    // Escape the leading `--` for the regex; assert "TOKEN:" appears.
    expect(stripped).toMatch(new RegExp(token.replace(/-/g, "\\-") + "\\s*:"));
  });

  it("uses PULSE brand identifier, not the legacy pre-rebrand token (REQ-pulse-branding)", () => {
    // Case-insensitive scan; the rebrand audit gate from Plan 01-01 also covers
    // this file at the repo level. Note: we don't write the legacy token in
    // any production source file — checking the stripped CSS doesn't accidentally
    // re-introduce it via this test either.
    const stripped = stripComments(css).toLowerCase();
    expect(stripped).not.toMatch(/sis[k]onkin/);
  });

  it("B-03: declares two distinct heartbeat keyframes (healthy + alert) with distinct glow vars", () => {
    expect(heartbeat).toMatch(/@keyframes\s+pulse-heartbeat-healthy/);
    expect(heartbeat).toMatch(/@keyframes\s+pulse-heartbeat-alert/);
    // Per-state custom-property assignment: each must reference a distinct token.
    expect(heartbeat).toMatch(
      /data-state="on"\][\s\S]*?--sk-led-glow:\s*var\(--sk-pln-yellow-glow\)/,
    );
    expect(heartbeat).toMatch(
      /data-state="alert"\][\s\S]*?--sk-led-glow:\s*var\(--sk-led-alert-glow\)/,
    );
  });

  it("B-03: heartbeat alert keyframe references --sk-led-alert-glow (not the healthy glow var)", () => {
    // Inside the alert @keyframes block, box-shadow must reference --sk-led-alert-glow
    // — not --sk-pln-yellow-glow — so the computed glow color truly differs.
    const alertBlock = heartbeat.match(/@keyframes\s+pulse-heartbeat-alert\s*\{[\s\S]*?\}\s*\}/);
    expect(alertBlock).not.toBeNull();
    expect(alertBlock?.[0]).toMatch(/--sk-led-alert-glow/);
    expect(alertBlock?.[0]).not.toMatch(/--sk-pln-yellow-glow/);
  });

  it("declares the reduced-motion gate that disables both keyframes", () => {
    expect(heartbeat).toMatch(/@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)/);
    expect(heartbeat).toMatch(/\.sk-led\[data-state="on"\]/);
    expect(heartbeat).toMatch(/\.sk-led\[data-state="alert"\]/);
    expect(heartbeat).toMatch(/animation:\s*none/);
  });
});
