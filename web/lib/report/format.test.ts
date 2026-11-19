import { describe, expect, it } from "vitest";
import { displayHost, formatDuration, formatLayoutShift, formatSaving } from "./format";

describe("formatDuration", () => {
  it("shows short durations in milliseconds", () => {
    expect(formatDuration(180.4, "en")).toBe("180 ms");
  });

  it("shows longer durations in seconds with the locale's decimal mark", () => {
    expect(formatDuration(4800, "en")).toBe("4.8 s");
    expect(formatDuration(4800, "bs")).toBe("4,8 s");
  });
});

describe("formatLayoutShift", () => {
  it("uses two decimals in the locale's format", () => {
    expect(formatLayoutShift(0.2134, "en")).toBe("0.21");
    expect(formatLayoutShift(0.2134, "bs")).toBe("0,21");
  });
});

describe("formatSaving", () => {
  it("prefixes savings with a minus sign", () => {
    expect(formatSaving(1800, "bs")).toBe("−1,8 s");
  });
});

describe("displayHost", () => {
  it("drops the scheme, www and a bare trailing slash", () => {
    expect(displayHost("https://www.example-restaurant.ba/")).toBe("example-restaurant.ba");
  });

  it("keeps a meaningful path", () => {
    expect(displayHost("https://shop.example.ba/products/bag")).toBe(
      "shop.example.ba/products/bag",
    );
  });
});
