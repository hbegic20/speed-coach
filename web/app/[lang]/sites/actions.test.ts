import { afterEach, describe, expect, it, vi } from "vitest";
import { audit, site } from "@/test/audit-fixture";
import { addSite, recheckTrackedSite, removeTrackedSite, trackAuditedSite } from "./actions";

const TOKEN = "b".repeat(43);
const CLIENT_IP = "203.0.113.7";
const CALLER = { token: TOKEN, clientIp: CLIENT_IP };

const mocks = vi.hoisted(() => ({
  redirect: vi.fn(),
  ensureOwnerToken: vi.fn(),
  readOwnerToken: vi.fn(),
  trackSite: vi.fn(),
  recheckSite: vi.fn(),
  untrackSite: vi.fn(),
}));

vi.mock("next/navigation", () => ({ redirect: mocks.redirect }));
vi.mock("@/lib/owner/token", () => ({
  ensureOwnerToken: mocks.ensureOwnerToken,
  readOwnerToken: mocks.readOwnerToken,
}));
vi.mock("@/lib/request/client-ip", () => ({ requestClientIp: async () => CLIENT_IP }));
vi.mock("@/lib/api/sites", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api/sites")>()),
  trackSite: mocks.trackSite,
  recheckSite: mocks.recheckSite,
  untrackSite: mocks.untrackSite,
}));

const initialState = { error: null, url: "" };

function formWith(url: string): FormData {
  const formData = new FormData();
  formData.set("url", url);
  return formData;
}

afterEach(() => {
  vi.resetAllMocks();
});

describe("addSite", () => {
  it("tracks the site, starts its first check and opens the report", async () => {
    mocks.ensureOwnerToken.mockResolvedValue(TOKEN);
    mocks.trackSite.mockResolvedValue(site());
    mocks.recheckSite.mockResolvedValue(audit());

    await addSite("bs", initialState, formWith("example-restaurant.ba"));

    expect(mocks.trackSite).toHaveBeenCalledWith(CALLER, "https://example-restaurant.ba");
    expect(mocks.recheckSite).toHaveBeenCalledWith(CALLER, site().id, "bs");
    expect(mocks.redirect).toHaveBeenCalledWith(`/bs/audits/${audit().id}`);
  });

  it("rejects invalid urls before creating an owner", async () => {
    const state = await addSite("en", initialState, formWith("localhost"));

    expect(state).toEqual({ error: "invalid_url", url: "localhost" });
    expect(mocks.ensureOwnerToken).not.toHaveBeenCalled();
  });

  it("reports when the API is unavailable", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    mocks.ensureOwnerToken.mockResolvedValue(TOKEN);
    mocks.trackSite.mockRejectedValue(new TypeError("fetch failed"));

    const state = await addSite("en", initialState, formWith("https://example.ba"));

    expect(state).toEqual({ error: "unavailable", url: "https://example.ba" });
  });
});

describe("rate limiting", () => {
  it("tells the visitor to wait when adding sites too quickly", async () => {
    const { SitesApiError } = await import("@/lib/api/sites");
    mocks.ensureOwnerToken.mockResolvedValue(TOKEN);
    mocks.trackSite.mockRejectedValue(new SitesApiError(429));

    const state = await addSite("en", initialState, formWith("https://example.ba"));

    expect(state).toEqual({ error: "rate_limited", url: "https://example.ba" });
  });

  it("sends a rate-limited re-check back to the dashboard with a notice", async () => {
    const { SitesApiError } = await import("@/lib/api/sites");
    mocks.readOwnerToken.mockResolvedValue(TOKEN);
    mocks.recheckSite.mockRejectedValue(new SitesApiError(429));
    mocks.redirect.mockImplementation((path: string) => {
      throw new Error(`redirect:${path}`);
    });

    await expect(recheckTrackedSite("bs", site().id)).rejects.toThrow(
      "redirect:/bs/sites?notice=rate_limited",
    );
  });
});

describe("trackAuditedSite", () => {
  it("tracks the reported site with its audit and opens the dashboard", async () => {
    mocks.ensureOwnerToken.mockResolvedValue(TOKEN);
    mocks.trackSite.mockResolvedValue(site());

    await trackAuditedSite("en", audit().id, audit().url);

    expect(mocks.trackSite).toHaveBeenCalledWith(CALLER, audit().url, audit().id);
    expect(mocks.redirect).toHaveBeenCalledWith(`/en/sites?site=${site().id}`);
  });

  it("rejects a tampered audit id", async () => {
    await expect(trackAuditedSite("en", "not-an-id", audit().url)).rejects.toThrow();
    expect(mocks.trackSite).not.toHaveBeenCalled();
  });
});

describe("recheckTrackedSite and removeTrackedSite", () => {
  it("re-checks in the page language and opens the new report", async () => {
    mocks.readOwnerToken.mockResolvedValue(TOKEN);
    mocks.recheckSite.mockResolvedValue(audit({ status: "queued" }));

    await recheckTrackedSite("bs", site().id);

    expect(mocks.recheckSite).toHaveBeenCalledWith(CALLER, site().id, "bs");
    expect(mocks.redirect).toHaveBeenCalledWith(`/bs/audits/${audit().id}`);
  });

  it("stops tracking and returns to the dashboard", async () => {
    mocks.readOwnerToken.mockResolvedValue(TOKEN);

    await removeTrackedSite("en", site().id);

    expect(mocks.untrackSite).toHaveBeenCalledWith(CALLER, site().id);
    expect(mocks.redirect).toHaveBeenCalledWith("/en/sites");
  });
});
