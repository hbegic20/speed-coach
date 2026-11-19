import type { Locale } from "@/lib/i18n/locales";
import { apiUrl, proxyHeaders } from "./client";
import { auditSchema, siteSchema, sitesSchema, type Audit, type Site } from "./schemas";

const UNAUTHORIZED = 401;

export type SitesCaller = {
  token: string;
  clientIp: string | null;
};

export class SitesApiError extends Error {
  constructor(readonly status: number) {
    super(`SpeedCoach API responded ${status}`);
  }
}

async function request(
  caller: SitesCaller,
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      ...init.headers,
      ...proxyHeaders(caller.clientIp),
      Authorization: `Bearer ${caller.token}`,
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });
  if (!response.ok) throw new SitesApiError(response.status);
  return response;
}

export async function listSites(caller: SitesCaller): Promise<Site[]> {
  try {
    return sitesSchema.parse(await (await request(caller, "/sites")).json());
  } catch (error) {
    if (error instanceof SitesApiError && error.status === UNAUTHORIZED) return [];
    throw error;
  }
}

export async function trackSite(caller: SitesCaller, url: string, auditId?: string): Promise<Site> {
  const response = await request(caller, "/sites", {
    method: "POST",
    body: JSON.stringify({ url, audit_id: auditId ?? null }),
  });
  return siteSchema.parse(await response.json());
}

export async function recheckSite(
  caller: SitesCaller,
  siteId: string,
  language: Locale,
): Promise<Audit> {
  const response = await request(caller, `/sites/${encodeURIComponent(siteId)}/audits`, {
    method: "POST",
    body: JSON.stringify({ language }),
  });
  return auditSchema.parse(await response.json());
}

export async function untrackSite(caller: SitesCaller, siteId: string): Promise<void> {
  await request(caller, `/sites/${encodeURIComponent(siteId)}`, { method: "DELETE" });
}
