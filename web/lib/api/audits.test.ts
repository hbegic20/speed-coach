import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { audit } from "@/test/audit-fixture";
import { createAudit, getAudit } from "./audits";

const API_URL = "http://api.test";

function respondWith(status: number, body: unknown) {
  return vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValue(new Response(JSON.stringify(body), { status }));
}

beforeEach(() => {
  vi.stubEnv("API_URL", API_URL);
  vi.spyOn(console, "error").mockImplementation(() => undefined);
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});

describe("createAudit", () => {
  it("posts the url and language and returns the queued audit", async () => {
    const queued = audit({ status: "queued", reports: [], recommendations: [] });
    const fetchMock = respondWith(202, queued);

    const result = await createAudit("https://example.ba/", "bs");

    expect(result).toEqual({ ok: true, audit: queued });
    const [url, init] = fetchMock.mock.calls[0] ?? [];
    expect(url).toBe(`${API_URL}/audits`);
    expect(init?.method).toBe("POST");
    expect(JSON.parse(String(init?.body))).toEqual({ url: "https://example.ba/", language: "bs" });
  });

  it("reports an invalid url when the API rejects it", async () => {
    respondWith(422, { detail: [] });

    expect(await createAudit("http://10.0.0.1", "en")).toEqual({
      ok: false,
      error: "invalid_url",
    });
  });

  it("reports unavailable when the API is down", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("fetch failed"));

    expect(await createAudit("https://example.ba/", "en")).toEqual({
      ok: false,
      error: "unavailable",
    });
  });

  it("reports unavailable when the queue is down", async () => {
    respondWith(503, { detail: "audit_queue_unavailable" });

    expect(await createAudit("https://example.ba/", "en")).toEqual({
      ok: false,
      error: "unavailable",
    });
  });

  it("reports unavailable when the API returns an unexpected body", async () => {
    respondWith(202, { id: "not-a-uuid" });

    expect(await createAudit("https://example.ba/", "en")).toEqual({
      ok: false,
      error: "unavailable",
    });
  });
});

describe("getAudit", () => {
  it("returns the validated audit", async () => {
    respondWith(200, audit());

    expect(await getAudit(audit().id)).toEqual(audit());
  });

  it("returns null for an unknown audit", async () => {
    respondWith(404, { detail: "audit_not_found" });

    expect(await getAudit(audit().id)).toBeNull();
  });

  it("throws when the API fails", async () => {
    respondWith(500, {});

    await expect(getAudit(audit().id)).rejects.toThrow("SpeedCoach API responded 500");
  });

  it("throws when the audit does not match the schema", async () => {
    respondWith(200, { ...audit(), status: "exploded" });

    await expect(getAudit(audit().id)).rejects.toThrow();
  });
});
