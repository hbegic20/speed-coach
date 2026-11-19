import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { audit, site } from "@/test/audit-fixture";
import {
  SitesApiError,
  getSite,
  listSites,
  recheckSite,
  setCompletedFixes,
  trackSite,
  untrackSite,
} from "./sites";

const API_URL = "http://api.test";
const CALLER = { token: "a".repeat(43), clientIp: "203.0.113.7" };

function respondWith(status: number, body?: unknown) {
  return vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValue(
      new Response(body === undefined ? null : JSON.stringify(body), { status }),
    );
}

function lastRequest(fetchMock: ReturnType<typeof respondWith>) {
  const [url, init] = fetchMock.mock.calls.at(-1) ?? [];
  return { url, init, headers: new Headers(init?.headers) };
}

beforeEach(() => {
  vi.stubEnv("API_URL", API_URL);
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});

describe("sites API client", () => {
  it("lists sites with the owner token", async () => {
    const fetchMock = respondWith(200, { sites: [site()], site_limit: 3 });

    expect(await listSites(CALLER)).toEqual({ sites: [site()], siteLimit: 3 });
    const { url, headers } = lastRequest(fetchMock);
    expect(url).toBe(`${API_URL}/sites`);
    expect(headers.get("Authorization")).toBe(`Bearer ${CALLER.token}`);
  });

  it("treats an unknown owner as having no sites", async () => {
    respondWith(401, { detail: "owner_token_invalid" });

    expect(await listSites(CALLER)).toEqual({ sites: [], siteLimit: null });
  });

  it("raises other API failures", async () => {
    respondWith(500, {});

    await expect(listSites(CALLER)).rejects.toBeInstanceOf(SitesApiError);
  });

  it("tracks a site together with the audit it came from", async () => {
    const fetchMock = respondWith(201, site());

    await trackSite(CALLER, "https://example-restaurant.ba", audit().id);

    const { init } = lastRequest(fetchMock);
    expect(init?.method).toBe("POST");
    expect(JSON.parse(String(init?.body))).toEqual({
      url: "https://example-restaurant.ba",
      audit_id: audit().id,
    });
  });

  it("re-checks a site in the requested language", async () => {
    const fetchMock = respondWith(202, audit({ status: "queued" }));

    const queued = await recheckSite(CALLER, site().id, "bs");

    expect(queued.status).toBe("queued");
    const { url, init } = lastRequest(fetchMock);
    expect(url).toBe(`${API_URL}/sites/${site().id}/audits`);
    expect(JSON.parse(String(init?.body))).toEqual({ language: "bs" });
  });

  it("loads one owned site and treats a stranger's site as missing", async () => {
    respondWith(200, site());
    expect(await getSite(CALLER, site().id)).toEqual(site());

    respondWith(404, { detail: "site_not_found" });
    expect(await getSite(CALLER, site().id)).toBeNull();
  });

  it("marks fixes as done", async () => {
    const fetchMock = respondWith(204);

    await setCompletedFixes(CALLER, site().id, ["unused-css"], true);

    const { url, init } = lastRequest(fetchMock);
    expect(url).toBe(`${API_URL}/sites/${site().id}/completed-fixes`);
    expect(init?.method).toBe("PUT");
    expect(JSON.parse(String(init?.body))).toEqual({
      lighthouse_ids: ["unused-css"],
      completed: true,
    });
  });

  it("stops tracking a site", async () => {
    const fetchMock = respondWith(204);

    await untrackSite(CALLER, site().id);

    const { url, init } = lastRequest(fetchMock);
    expect(url).toBe(`${API_URL}/sites/${site().id}`);
    expect(init?.method).toBe("DELETE");
  });
});
