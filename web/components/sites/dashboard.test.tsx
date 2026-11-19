import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { site, siteCheck } from "@/test/audit-fixture";
import { ChangeIndicator } from "./change-indicator";
import { SitesTable } from "./sites-table";
import { StatCards } from "./stat-cards";
import { TrendChart } from "./trend-chart";

const dictionary = getDictionary("en");

describe("ChangeIndicator", () => {
  it.each([
    [39, "Up by 39"],
    [-12, "Down by 12"],
    [0, "No change"],
    [null, "Not enough checks"],
  ])("describes a change of %s as %s", (change, text) => {
    render(<ChangeIndicator change={change} labels={dictionary.sites.change} />);

    expect(screen.getByText(text)).toBeDefined();
  });
});

describe("StatCards", () => {
  it("shows the average mobile score and its change since the first check", () => {
    render(<StatCards sites={[site()]} siteLimit={3} labels={dictionary.sites} />);

    const average = screen.getByText("Avg. mobile performance").closest("div");
    expect(average?.textContent).toContain("81");
    expect(average?.textContent).toContain("Up by 39");
    expect(average?.textContent).toContain("since first check");
    expect(screen.getByText("Sites tracked").closest("div")?.textContent).toContain("1 of 3");
  });
});

describe("StatCards issues fixed", () => {
  it("adds up fix progress across sites", () => {
    const first = site({ fix_progress: { completed: 2, total: 5, confirmed: 1 } });
    const second = site({ id: "second", fix_progress: { completed: 1, total: 3, confirmed: 1 } });
    render(<StatCards sites={[first, second]} siteLimit={3} labels={dictionary.sites} />);

    const card = screen.getByText("Issues fixed").closest("div");
    expect(card?.textContent).toContain("3 / 8");
    expect(card?.textContent).toContain("Confirmed by the latest check: 2");
  });

  it("explains how to start when nothing is tracked yet", () => {
    const fresh = site({ fix_progress: { completed: 0, total: 0, confirmed: 0 } });
    render(<StatCards sites={[fresh]} siteLimit={3} labels={dictionary.sites} />);

    expect(screen.getByText("Mark fixes as done on a report")).toBeDefined();
  });
});

describe("StatCards without a known limit", () => {
  it("shows only the count", () => {
    render(<StatCards sites={[site()]} siteLimit={null} labels={dictionary.sites} />);

    const tracked = screen.getByText("Sites tracked").closest("div");
    expect(tracked?.textContent).toContain("1");
    expect(tracked?.textContent).not.toContain(" of ");
  });
});

describe("TrendChart", () => {
  it("summarizes the trend and lists every check for screen readers", () => {
    render(<TrendChart site={site()} locale="en" labels={dictionary.sites.chart} />);

    expect(
      screen.getByRole("img", { name: "Mobile performance went from 42 to 81 (checks: 2)" }),
    ).toBeDefined();
    const table = screen.getByRole("table", { name: /Check history/ });
    expect(within(table).getAllByRole("row")).toHaveLength(3);
  });

  it("explains an empty history", () => {
    render(<TrendChart site={site({ checks: [] })} locale="en" labels={dictionary.sites.chart} />);

    expect(screen.getByText(/No finished checks yet/)).toBeDefined();
  });

  it("handles a single check", () => {
    render(
      <TrendChart site={site({ checks: [siteCheck()] })} locale="en" labels={dictionary.sites.chart} />,
    );

    expect(screen.getByRole("img", { name: "One check so far: mobile performance 42" })).toBeDefined();
  });
});

describe("SitesTable", () => {
  it("lists each site with its score, change and actions", () => {
    render(<SitesTable sites={[site()]} locale="en" dictionary={dictionary} />);

    const row = screen.getByRole("row", { name: /example-restaurant\.ba/ });
    const cells = within(row);
    expect(cells.getByRole("rowheader").textContent).toBe("example-restaurant.ba");
    expect(cells.getByText("WordPress")).toBeDefined();
    expect(row.textContent).toContain("81");
    expect(row.textContent).toContain("Needs work");
    expect(cells.getByText("Up by 39")).toBeDefined();
    expect(
      cells.getByRole("link", { name: "View report: example-restaurant.ba" }).getAttribute("href"),
    ).toBe("/en/audits/7a6b5c4d-3e2f-4a1b-9c8d-7e6f5a4b3c2d");
    expect(cells.getByRole("button", { name: "Re-check: example-restaurant.ba" })).toBeDefined();
    expect(cells.getByRole("button", { name: "Stop tracking: example-restaurant.ba" })).toBeDefined();
  });

  it("shows a running check instead of a date", () => {
    const checking = site({
      latest_audit: { audit_id: "7a6b5c4d-3e2f-4a1b-9c8d-7e6f5a4b3c2d", status: "running" },
    });
    render(<SitesTable sites={[checking]} locale="en" dictionary={dictionary} />);

    expect(screen.getByText("Check in progress")).toBeDefined();
  });

  it("handles a site that was never checked", () => {
    const fresh = site({ checks: [], latest_audit: null });
    render(<SitesTable sites={[fresh]} locale="en" dictionary={dictionary} />);

    expect(screen.getAllByText("Not checked yet")).toHaveLength(2);
    expect(screen.queryByRole("link", { name: /View report/ })).toBeNull();
  });
});
