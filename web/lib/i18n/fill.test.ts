import { describe, expect, it } from "vitest";
import { fill } from "./fill";

describe("fill", () => {
  it("replaces named placeholders", () => {
    expect(fill("{label} score {value} of 100", { label: "SEO", value: 91 })).toBe(
      "SEO score 91 of 100",
    );
  });

  it("leaves unknown placeholders untouched", () => {
    expect(fill("Checked {date}", {})).toBe("Checked {date}");
  });
});
