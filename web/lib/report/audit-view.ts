import type { Audit, Device, DeviceReport, Recommendation } from "@/lib/api/schemas";

export function isInProgress(audit: Audit): boolean {
  return audit.status === "queued" || audit.status === "running";
}

export function reportForDevice(audit: Audit, device: Device): DeviceReport | undefined {
  return audit.reports.find((report) => report.device === device) ?? audit.reports[0];
}

export function estimatedSavingMs(
  recommendation: Recommendation,
  report: DeviceReport,
): number | null {
  const savings = report.findings
    .filter((finding) => recommendation.lighthouse_ids.includes(finding.lighthouse_id))
    .map((finding) => finding.savings_ms ?? 0)
    .filter((saving) => saving > 0);
  return savings.length > 0 ? Math.max(...savings) : null;
}

export function parseDevice(value: string | string[] | undefined): Device {
  return value === "desktop" ? "desktop" : "mobile";
}
