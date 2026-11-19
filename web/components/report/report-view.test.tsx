import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { audit, deviceReport, recommendation } from "@/test/audit-fixture";
import type { Audit, CompletedFix, Device } from "@/lib/api/schemas";
import type { FixTracking } from "@/lib/report/fix-status";
import type { Locale } from "@/lib/i18n/locales";
import { ReportView } from "./report-view";

const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

async function rerunAction() {
  return { error: null, url: "" };
}

const SITE_ID = "3e2d1c0b-9a8f-4e7d-8c6b-5a4f3e2d1c0b";

function tracking(completedFixes: CompletedFix[] = []): FixTracking {
  return { siteId: SITE_ID, completedFixes };
}

function renderReport(
  shown: Audit,
  {
    device = "mobile",
    locale = "en",
    fixTracking = null,
  }: { device?: Device; locale?: Locale; fixTracking?: FixTracking | null } = {},
) {
  render(
    <ReportView
      audit={shown}
      device={device}
      locale={locale}
      dictionary={getDictionary(locale)}
      rerunAction={rerunAction}
      fixTracking={fixTracking}
    />,
  );
}

describe("ReportView", () => {
  it("shows the site, detected platform and every score", () => {
    renderReport(audit());

    expect(screen.getByRole("heading", { level: 1, name: "example-restaurant.ba" })).toBeDefined();
    expect(screen.getByText("Detected: WordPress")).toBeDefined();
    const scores = screen.getByRole("region", { name: "Scores" });
    expect(within(scores).getByRole("img", { name: "Performance score 42 of 100" })).toBeDefined();
    expect(within(scores).getByRole("img", { name: "SEO score 91 of 100" })).toBeDefined();
    expect(within(scores).getByText("Poor")).toBeDefined();
  });

  it("shows the desktop measurements when desktop is selected", () => {
    renderReport(audit(), { device: "desktop" });

    expect(screen.getByRole("img", { name: "Performance score 88 of 100" })).toBeDefined();
    expect(screen.getByRole("link", { name: "Desktop" }).getAttribute("aria-current")).toBe("page");
  });

  it("links the device toggle to each stored result", () => {
    renderReport(audit());

    const toggle = screen.getByRole("navigation", { name: "Device" });
    expect(within(toggle).getByRole("link", { name: "Mobile" }).getAttribute("href")).toBe(
      `/en/audits/${audit().id}`,
    );
    expect(within(toggle).getByRole("link", { name: "Desktop" }).getAttribute("href")).toBe(
      `/en/audits/${audit().id}?device=desktop`,
    );
  });

  it("rates the lab vitals with a text label", () => {
    renderReport(audit());

    const vitals = screen.getByRole("region", { name: "Core Web Vitals" });
    const lcp = within(vitals).getByRole("heading", { name: "Largest Contentful Paint" });
    expect(lcp.parentElement?.textContent).toContain("Poor");
    expect(vitals.textContent).toContain("4.8 s");
    expect(vitals.textContent).toContain("180 ms");
    expect(vitals.textContent).toContain("0.21");
  });

  it("lists ranked fixes with platform steps and estimated savings", () => {
    renderReport(audit());

    const fixes = screen.getByRole("region", { name: "Your top fixes" });
    const items = within(fixes).getAllByRole("article");
    expect(items).toHaveLength(2);
    const first = within(items[0] as HTMLElement);
    expect(first.getByRole("heading", { name: "1. Load scripts after the page appears" })).toBeDefined();
    expect(first.getByText("High impact")).toBeDefined();
    expect(first.getByText("How to fix in WordPress")).toBeDefined();
    expect(first.getAllByRole("listitem")).toHaveLength(2);
    expect(first.getByText("−1.2 s")).toBeDefined();
    expect(within(items[1] as HTMLElement).queryByText("Est. saving")).toBeNull();
  });

  it("offers to track the site", () => {
    renderReport(audit());

    expect(screen.getByRole("button", { name: "Track this site" })).toBeDefined();
  });

  it("uses generic fix instructions when the platform is unknown", () => {
    renderReport(audit({ platform: "unknown" }));

    expect(screen.queryByText(/Detected:/)).toBeNull();
    expect(screen.getAllByText("How to fix")).toHaveLength(2);
  });

  it("shows progress and keeps refreshing while the audit runs", () => {
    vi.useFakeTimers();
    renderReport(audit({ status: "running", reports: [], recommendations: [] }));

    expect(screen.getByRole("status").textContent).toBe("Running the audit");
    expect(screen.queryByRole("region", { name: "Scores" })).toBeNull();
    vi.advanceTimersByTime(6000);
    expect(refresh).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });

  it("explains why an audit failed before any measurement", () => {
    renderReport(
      audit({
        status: "failed",
        failure_reason: "site_unreachable",
        reports: [],
        recommendations: [],
      }),
    );

    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("We couldn't finish this check");
    expect(alert.textContent).toContain("Google couldn't load this page");
  });

  it("keeps the measurements when only the fix suggestions failed", () => {
    renderReport(
      audit({ status: "failed", failure_reason: "recommendations_unavailable", recommendations: [] }),
    );

    expect(screen.getByRole("region", { name: "Scores" })).toBeDefined();
    expect(screen.getByText(/Fix suggestions aren't available right now/)).toBeDefined();
  });

  it("celebrates a site with nothing to fix", () => {
    renderReport(
      audit({ summary: null, recommendations: [], reports: [deviceReport({ findings: [] })] }),
    );

    expect(screen.getByText(/Nothing important to fix/)).toBeDefined();
  });

  it("renders in Bosnian", () => {
    renderReport(audit({ language: "bs" }), { locale: "bs" });

    expect(screen.getByRole("region", { name: "Ocjene" })).toBeDefined();
    expect(screen.getByText("Prepoznato: WordPress")).toBeDefined();
    expect(screen.getAllByText("Kako popraviti na platformi WordPress")).toHaveLength(2);
    expect(screen.getByText("−1,2 s")).toBeDefined();
  });

  it("offers no fix tracking on reports of untracked sites", () => {
    renderReport(audit());

    expect(screen.queryByRole("button", { name: "Mark as done" })).toBeNull();
  });

  it("lets the site owner mark each fix as done", () => {
    renderReport(audit({ tracked_site_id: SITE_ID }), { fixTracking: tracking() });

    expect(screen.getAllByRole("button", { name: "Mark as done" })).toHaveLength(2);
  });

  it("shows fixes marked after this check as done, with undo", () => {
    const marked = { lighthouse_id: "render-blocking-resources", completed_at: "2026-11-20T08:00:00Z" };
    renderReport(audit({ tracked_site_id: SITE_ID }), { fixTracking: tracking([marked]) });

    const [first, second] = screen.getAllByRole("article");
    expect(within(first as HTMLElement).getByText("Done · re-check to confirm")).toBeDefined();
    expect(within(first as HTMLElement).getByRole("button", { name: "Undo" })).toBeDefined();
    expect(within(second as HTMLElement).getByRole("button", { name: "Mark as done" })).toBeDefined();
  });

  it("flags fixes that this check still detects", () => {
    const markedEarlier = {
      lighthouse_id: "render-blocking-resources",
      completed_at: "2026-11-01T08:00:00Z",
    };
    renderReport(audit({ tracked_site_id: SITE_ID }), { fixTracking: tracking([markedEarlier]) });

    const [first] = screen.getAllByRole("article");
    expect(within(first as HTMLElement).getByText("Still detected in this check")).toBeDefined();
  });

  it("does not offer marking for older fixes without lighthouse problems", () => {
    const older = audit({
      tracked_site_id: SITE_ID,
      recommendations: [recommendation({ lighthouse_ids: [] })],
    });
    renderReport(older, { fixTracking: tracking() });

    expect(screen.queryByRole("button", { name: "Mark as done" })).toBeNull();
  });
});
