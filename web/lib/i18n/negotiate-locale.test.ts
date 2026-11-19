import { describe, expect, it } from "vitest";
import { negotiateLocale } from "./negotiate-locale";

describe("negotiateLocale", () => {
  it("falls back to Bosnian when no header is sent", () => {
    expect(negotiateLocale(null)).toBe("bs");
  });

  it("picks English for an English browser", () => {
    expect(negotiateLocale("en-US,en;q=0.9")).toBe("en");
  });

  it("matches a regional Bosnian tag", () => {
    expect(negotiateLocale("bs-BA")).toBe("bs");
  });

  it("respects quality ordering", () => {
    expect(negotiateLocale("bs;q=0.5,en;q=0.8")).toBe("en");
  });

  it("skips unsupported languages and falls back to the next supported one", () => {
    expect(negotiateLocale("de-DE,de;q=0.9,en;q=0.7")).toBe("en");
  });

  it("ignores languages the browser rejects with zero quality", () => {
    expect(negotiateLocale("en;q=0")).toBe("bs");
  });

  it("falls back to Bosnian when nothing is supported", () => {
    expect(negotiateLocale("fr,de")).toBe("bs");
  });
});
