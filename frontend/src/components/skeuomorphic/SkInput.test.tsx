import { render, screen } from "@testing-library/react";
import { SkInput } from "./SkInput";

describe("SkInput (W-01)", () => {
  it("renders an input with data-sk=input and the supplied label as aria-label", () => {
    render(<SkInput label="Email" placeholder="email" />);
    const el = screen.getByLabelText("Email");
    expect(el.tagName.toLowerCase()).toBe("input");
    expect(el).toHaveAttribute("data-sk", "input");
  });

  it("invalid sets aria-invalid=true", () => {
    render(<SkInput label="Field" invalid />);
    const el = screen.getByLabelText("Field");
    expect(el).toHaveAttribute("aria-invalid", "true");
  });

  it("forwards refs (react-hook-form compatibility)", () => {
    let captured: HTMLInputElement | null = null;
    render(
      <SkInput
        label="RefField"
        ref={(node) => {
          captured = node;
        }}
      />,
    );
    expect(captured).not.toBeNull();
    expect((captured as unknown as HTMLInputElement).tagName.toLowerCase()).toBe("input");
  });
});
