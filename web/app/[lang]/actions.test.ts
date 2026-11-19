import { afterEach, describe, expect, it, vi } from "vitest";
import { audit } from "@/test/audit-fixture";
import { submitAudit } from "./actions";

const { createAudit, redirect } = vi.hoisted(() => ({
  createAudit: vi.fn(),
  redirect: vi.fn(),
}));

vi.mock("@/lib/api/audits", () => ({ createAudit }));
vi.mock("next/navigation", () => ({ redirect }));

const initialState = { error: null, url: "" };

function formWith(url: string): FormData {
  const formData = new FormData();
  formData.set("url", url);
  return formData;
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("submitAudit", () => {
  it("starts an audit in the page language and opens its report", async () => {
    createAudit.mockResolvedValue({ ok: true, audit: audit() });

    await submitAudit("bs", initialState, formWith("example-restaurant.ba"));

    expect(createAudit).toHaveBeenCalledWith("https://example-restaurant.ba", "bs");
    expect(redirect).toHaveBeenCalledWith(`/bs/audits/${audit().id}`);
  });

  it.each(["", "not a url", "ftp://example.ba", "http://localhost:3000", "https://10.0.0.1"])(
    "rejects %j without calling the API",
    async (url) => {
      const state = await submitAudit("en", initialState, formWith(url));

      expect(state).toEqual({ error: "invalid_url", url });
      expect(createAudit).not.toHaveBeenCalled();
    },
  );

  it("keeps the typed url when the API is unavailable", async () => {
    createAudit.mockResolvedValue({ ok: false, error: "unavailable" });

    const state = await submitAudit("en", initialState, formWith("https://example.ba"));

    expect(state).toEqual({ error: "unavailable", url: "https://example.ba" });
    expect(redirect).not.toHaveBeenCalled();
  });

  it("falls back to the default language for an unknown locale", async () => {
    createAudit.mockResolvedValue({ ok: true, audit: audit() });

    await submitAudit("de", initialState, formWith("https://example.ba"));

    expect(createAudit).toHaveBeenCalledWith("https://example.ba", "bs");
  });
});
