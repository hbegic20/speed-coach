export type Tone = "good" | "needsWork" | "poor";

type Thresholds = { good: number; needsWork: number };

const SCORE_THRESHOLDS: Thresholds = { good: 90, needsWork: 50 };

export const METRIC_THRESHOLDS = {
  largestContentfulPaint: { good: 2500, needsWork: 4000 },
  totalBlockingTime: { good: 200, needsWork: 600 },
  cumulativeLayoutShift: { good: 0.1, needsWork: 0.25 },
} satisfies Record<string, Thresholds>;

export type Metric = keyof typeof METRIC_THRESHOLDS;

export function scoreTone(score: number): Tone {
  if (score >= SCORE_THRESHOLDS.good) return "good";
  if (score >= SCORE_THRESHOLDS.needsWork) return "needsWork";
  return "poor";
}

export function metricTone(metric: Metric, value: number): Tone {
  const thresholds = METRIC_THRESHOLDS[metric];
  if (value <= thresholds.good) return "good";
  if (value <= thresholds.needsWork) return "needsWork";
  return "poor";
}
