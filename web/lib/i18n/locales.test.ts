import { describe, expect, it } from "vitest";
import { localizedPath, pathnameHasLocale } from "./locales";

describe("pathnameHasLocale", () => {
  it.each(["/bs", "/en", "/en/report/123"])("accepts %s", (pathname) => {
    expect(pathnameHasLocale(pathname)).toBe(true);
  });

  it.each(["/", "/report", "/english", "/de/report"])("rejects %s", (pathname) => {
    expect(pathnameHasLocale(pathname)).toBe(false);
  });
});

describe("localizedPath", () => {
  it.each([
    ["/en/audits/123", "bs", "/bs/audits/123"],
    ["/bs", "en", "/en"],
    ["/", "bs", "/bs"],
    ["/audits/123", "en", "/en/audits/123"],
  ] as const)("maps %s to %s as %s", (pathname, locale, expected) => {
    expect(localizedPath(pathname, locale)).toBe(expected);
  });
});
