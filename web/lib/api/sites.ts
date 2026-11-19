import type { Locale } from "@/lib/i18n/locales";
import { apiUrl, proxyHeaders } from "./client";
import { auditSchema, siteListSchema, siteSchema, type Audit, type Site } from "./schemas";

const UNAUTHORIZED = 401;
const NOT_FOUND = 404;

export type SiteList = {
  sites: Site[];
  siteLimit: number | null;
};

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

export async function listSites(caller: SitesCaller): Promise<SiteList> {
  try {
    const body = siteListSchema.parse(await (await request(caller, "/sites")).json());
    return { sites: body.sites, siteLimit: body.site_limit };
  } catch (error) {
    if (error instanceof SitesApiError && error.status === UNAUTHORIZED) {
      return { sites: [], siteLimit: null };
    }
    throw error;
  }
}

export async function getSite(caller: SitesCaller, siteId: string): Promise<Site | null> {
  try {
    const response = await request(caller, `/sites/${encodeURIComponent(siteId)}`);
    return siteSchema.parse(await response.json());
  } catch (error) {
    if (error instanceof SitesApiError && [UNAUTHORIZED, NOT_FOUND].includes(error.status)) {
      return null;
    }
    throw error;
  }
}

export async function setCompletedFixes(
  caller: SitesCaller,
  siteId: string,
  lighthouseIds: string[],
  completed: boolean,
): Promise<void> {
  await request(caller, `/sites/${encodeURIComponent(siteId)}/completed-fixes`, {
    method: "PUT",
    body: JSON.stringify({ lighthouse_ids: lighthouseIds, completed }),
  });
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
