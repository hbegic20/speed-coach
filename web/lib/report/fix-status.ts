import type { CompletedFix, Recommendation } from "@/lib/api/schemas";

export type FixStatus = "open" | "done" | "stillDetected";

export type FixTracking = {
  siteId: string;
  completedFixes: CompletedFix[];
};

export function canMarkFix(recommendation: Recommendation): boolean {
  return recommendation.lighthouse_ids.length > 0;
}

export function fixStatus(
  recommendation: Recommendation,
  checkedAt: string,
  completedFixes: CompletedFix[],
): FixStatus {
  const completedAt = new Map(
    completedFixes.map((fix) => [fix.lighthouse_id, Date.parse(fix.completed_at)]),
  );
  const marks = recommendation.lighthouse_ids.map((id) => completedAt.get(id));
  if (marks.length === 0 || marks.some((mark) => mark === undefined)) return "open";

  const checkTime = Date.parse(checkedAt);
  return marks.every((mark) => mark !== undefined && mark > checkTime) ? "done" : "stillDetected";
}
