import type { Locale } from "@/lib/i18n/locales";
import { apiUrl } from "./client";
import { auditSchema, siteSchema, sitesSchema, type Audit, type Site } from "./schemas";

const UNAUTHORIZED = 401;

export class SitesApiError extends Error {
  constructor(readonly status: number) {
    super(`SpeedCoach API responded ${status}`);
  }
}

async function request(token: string, path: string, init: RequestInit = {}): Promise<Response> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      ...init.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });
  if (!response.ok) throw new SitesApiError(response.status);
  return response;
}

export async function listSites(token: string): Promise<Site[]> {
  try {
    return sitesSchema.parse(await (await request(token, "/sites")).json());
  } catch (error) {
    if (error instanceof SitesApiError && error.status === UNAUTHORIZED) return [];
    throw error;
  }
}

export async function trackSite(token: string, url: string, auditId?: string): Promise<Site> {
  const response = await request(token, "/sites", {
    method: "POST",
    body: JSON.stringify({ url, audit_id: auditId ?? null }),
  });
  return siteSchema.parse(await response.json());
}

export async function recheckSite(token: string, siteId: string, language: Locale): Promise<Audit> {
  const response = await request(token, `/sites/${encodeURIComponent(siteId)}/audits`, {
    method: "POST",
    body: JSON.stringify({ language }),
  });
  return auditSchema.parse(await response.json());
}

export async function untrackSite(token: string, siteId: string): Promise<void> {
  await request(token, `/sites/${encodeURIComponent(siteId)}`, { method: "DELETE" });
}
