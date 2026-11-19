import { describe, expect, it } from "vitest";
import { site, siteCheck } from "@/test/audit-fixture";
import {
  averageChange,
  averageLatestScore,
  chartPoints,
  latestCheck,
  reportAuditId,
  scoreChange,
  scoredChecks,
  selectedSite,
} from "./site-history";

const AREA = { left: 0, right: 100, top: 0, bottom: 200 };

describe("scoreChange", () => {
  it("compares the latest mobile score with the first", () => {
    expect(scoreChange(site())).toBe(39);
  });

  it("needs at least two scored checks", () => {
    expect(scoreChange(site({ checks: [siteCheck()] }))).toBeNull();
    expect(
      scoreChange(site({ checks: [siteCheck(), siteCheck({ mobile_performance_score: null })] })),
    ).toBeNull();
  });
});

describe("latestCheck and scoredChecks", () => {
  it("skip checks without a mobile score", () => {
    const withGap = site({
      checks: [siteCheck(), siteCheck({ audit_id: "x", mobile_performance_score: null })],
    });

    expect(scoredChecks(withGap)).toHaveLength(1);
    expect(latestCheck(withGap)?.mobile_performance_score).toBe(42);
  });
});

describe("averages", () => {
  it("average the latest scores and changes across sites", () => {
    const other = site({
      id: "other",
      checks: [siteCheck({ mobile_performance_score: 90 }), siteCheck({ mobile_performance_score: 70 })],
    });

    expect(averageLatestScore([site(), other])).toBe(76);
    expect(averageChange([site(), other])).toBe(10);
  });

  it("return null without data", () => {
    expect(averageLatestScore([site({ checks: [] })])).toBeNull();
    expect(averageChange([])).toBeNull();
  });
});

describe("reportAuditId", () => {
  it("prefers the latest finished check", () => {
    expect(reportAuditId(site())).toBe("7a6b5c4d-3e2f-4a1b-9c8d-7e6f5a4b3c2d");
  });

  it("falls back to the running audit for a site without finished checks", () => {
    const fresh = site({
      checks: [],
      latest_audit: { audit_id: "running-audit", status: "running" },
    });

    expect(reportAuditId(fresh)).toBe("running-audit");
  });

  it("is null for a site that was never checked", () => {
    expect(reportAuditId(site({ checks: [], latest_audit: null }))).toBeNull();
  });
});

describe("selectedSite", () => {
  it("finds the requested site and falls back to the first", () => {
    const second = site({ id: "second" });

    expect(selectedSite([site(), second], "second")).toBe(second);
    expect(selectedSite([site(), second], "missing")?.id).toBe(site().id);
  });
});

describe("chartPoints", () => {
  it("spreads checks evenly and maps scores to height", () => {
    const points = chartPoints(scoredChecks(site()), AREA);

    expect(points.map(({ x, y }) => [x, y])).toEqual([
      [0, 116],
      [100, 38],
    ]);
  });

  it("centers a single check", () => {
    const [point] = chartPoints(scoredChecks(site({ checks: [siteCheck()] })), AREA);

    expect(point?.x).toBe(50);
  });
});
