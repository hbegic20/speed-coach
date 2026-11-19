import type { Site, SiteCheck } from "@/lib/api/schemas";

export type ScoredCheck = SiteCheck & { mobile_performance_score: number };

export function scoredChecks(site: Site): ScoredCheck[] {
  return site.checks.filter(
    (check): check is ScoredCheck => check.mobile_performance_score !== null,
  );
}

export function latestCheck(site: Site): ScoredCheck | undefined {
  return scoredChecks(site).at(-1);
}

export function scoreChange(site: Site): number | null {
  const checks = scoredChecks(site);
  const first = checks[0];
  const latest = checks.at(-1);
  if (!first || !latest || checks.length < 2) return null;
  return latest.mobile_performance_score - first.mobile_performance_score;
}

function average(values: number[]): number | null {
  if (values.length === 0) return null;
  return Math.round(values.reduce((sum, value) => sum + value, 0) / values.length);
}

export function averageLatestScore(sites: Site[]): number | null {
  return average(
    sites.flatMap((site) => {
      const latest = latestCheck(site);
      return latest ? [latest.mobile_performance_score] : [];
    }),
  );
}

export function averageChange(sites: Site[]): number | null {
  return average(
    sites.flatMap((site) => {
      const change = scoreChange(site);
      return change === null ? [] : [change];
    }),
  );
}

export function reportAuditId(site: Site): string | null {
  return latestCheck(site)?.audit_id ?? site.latest_audit?.audit_id ?? null;
}

export function selectedSite(sites: Site[], siteId: string | string[] | undefined): Site | undefined {
  return sites.find((site) => site.id === siteId) ?? sites[0];
}

export type ChartPoint = { x: number; y: number; score: number; checkedAt: string };

export type ChartArea = { left: number; right: number; top: number; bottom: number };

export function chartPoints(checks: ScoredCheck[], area: ChartArea): ChartPoint[] {
  const span = area.right - area.left;
  const step = checks.length > 1 ? span / (checks.length - 1) : 0;
  return checks.map((check, index) => ({
    x: checks.length > 1 ? area.left + index * step : area.left + span / 2,
    y: area.bottom - (check.mobile_performance_score / 100) * (area.bottom - area.top),
    score: check.mobile_performance_score,
    checkedAt: check.checked_at,
  }));
}
