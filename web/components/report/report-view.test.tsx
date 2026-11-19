import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { audit, deviceReport } from "@/test/audit-fixture";
import type { Audit, Device } from "@/lib/api/schemas";
import type { Locale } from "@/lib/i18n/locales";
import { ReportView } from "./report-view";

const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

async function rerunAction() {
  return { error: null, url: "" };
}

function renderReport(
  shown: Audit,
  { device = "mobile", locale = "en" }: { device?: Device; locale?: Locale } = {},
) {
  render(
    <ReportView
      audit={shown}
      device={device}
      locale={locale}
      dictionary={getDictionary(locale)}
      rerunAction={rerunAction}
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
});
