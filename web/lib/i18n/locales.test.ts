import { describe, expect, it } from "vitest";
import { pathnameHasLocale } from "./locales";

describe("pathnameHasLocale", () => {
  it.each(["/bs", "/en", "/en/report/123"])("accepts %s", (pathname) => {
    expect(pathnameHasLocale(pathname)).toBe(true);
  });

  it.each(["/", "/report", "/english", "/de/report"])("rejects %s", (pathname) => {
    expect(pathnameHasLocale(pathname)).toBe(false);
  });
});
