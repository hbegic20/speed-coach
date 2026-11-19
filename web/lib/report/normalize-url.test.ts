import { describe, expect, it } from "vitest";
import { normalizeUrlInput } from "./normalize-url";

describe("normalizeUrlInput", () => {
  it("adds https to a bare domain", () => {
    expect(normalizeUrlInput("  example.ba/menu ")).toBe("https://example.ba/menu");
  });

  it("keeps an explicit scheme", () => {
    expect(normalizeUrlInput("http://example.ba")).toBe("http://example.ba");
  });

  it("leaves other schemes for validation to reject", () => {
    expect(normalizeUrlInput("ftp://example.ba")).toBe("ftp://example.ba");
  });

  it("leaves empty input empty", () => {
    expect(normalizeUrlInput("   ")).toBe("");
  });
});
