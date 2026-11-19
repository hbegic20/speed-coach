import { describe, expect, it } from "vitest";
import { metricTone, scoreTone } from "./tone";

describe("scoreTone", () => {
  it.each([
    [100, "good"],
    [90, "good"],
    [89, "needsWork"],
    [50, "needsWork"],
    [49, "poor"],
    [0, "poor"],
  ] as const)("rates a score of %i as %s", (score, tone) => {
    expect(scoreTone(score)).toBe(tone);
  });
});

describe("metricTone", () => {
  it.each([
    ["largestContentfulPaint", 2500, "good"],
    ["largestContentfulPaint", 2501, "needsWork"],
    ["largestContentfulPaint", 4001, "poor"],
    ["totalBlockingTime", 200, "good"],
    ["totalBlockingTime", 600, "needsWork"],
    ["totalBlockingTime", 601, "poor"],
    ["cumulativeLayoutShift", 0.1, "good"],
    ["cumulativeLayoutShift", 0.21, "needsWork"],
    ["cumulativeLayoutShift", 0.3, "poor"],
  ] as const)("rates %s of %d as %s", (metric, value, tone) => {
    expect(metricTone(metric, value)).toBe(tone);
  });
});
