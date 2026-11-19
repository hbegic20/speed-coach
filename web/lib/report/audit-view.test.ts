import { describe, expect, it } from "vitest";
import { audit, deviceReport, recommendation } from "@/test/audit-fixture";
import { estimatedSavingMs, isInProgress, parseDevice, reportForDevice } from "./audit-view";

describe("isInProgress", () => {
  it.each([
    ["queued", true],
    ["running", true],
    ["completed", false],
    ["failed", false],
  ] as const)("treats %s as in progress: %s", (status, expected) => {
    expect(isInProgress(audit({ status }))).toBe(expected);
  });
});

describe("reportForDevice", () => {
  it("returns the requested device", () => {
    expect(reportForDevice(audit(), "desktop")?.performance_score).toBe(88);
  });

  it("falls back to the first report when the device is missing", () => {
    const mobileOnly = audit({ reports: [deviceReport()] });

    expect(reportForDevice(mobileOnly, "desktop")?.device).toBe("mobile");
  });

  it("returns nothing when the audit has no reports", () => {
    expect(reportForDevice(audit({ reports: [] }), "mobile")).toBeUndefined();
  });
});

describe("estimatedSavingMs", () => {
  it("uses the largest saving among the findings a fix resolves", () => {
    const fix = recommendation({
      lighthouse_ids: ["render-blocking-resources", "uses-long-cache-ttl"],
    });

    expect(estimatedSavingMs(fix, deviceReport())).toBe(1200);
  });

  it("returns null when none of the findings has a time saving", () => {
    const fix = recommendation({ lighthouse_ids: ["uses-long-cache-ttl"] });

    expect(estimatedSavingMs(fix, deviceReport())).toBeNull();
  });
});

describe("parseDevice", () => {
  it.each([
    ["desktop", "desktop"],
    ["mobile", "mobile"],
    [undefined, "mobile"],
    ["tablet", "mobile"],
    [["desktop", "mobile"], "mobile"],
  ] as const)("parses %j as %s", (value, device) => {
    expect(parseDevice(value as string | string[] | undefined)).toBe(device);
  });
});
