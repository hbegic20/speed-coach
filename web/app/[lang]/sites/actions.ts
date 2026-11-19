"use server";

import { redirect } from "next/navigation";
import { z } from "zod";
import { TOO_MANY_REQUESTS } from "@/lib/api/client";
import {
  SitesApiError,
  recheckSite,
  trackSite,
  untrackSite,
  type SitesCaller,
} from "@/lib/api/sites";
import { defaultLocale, isLocale, type Locale } from "@/lib/i18n/locales";
import { ensureOwnerToken, readOwnerToken } from "@/lib/owner/token";
import { requestClientIp } from "@/lib/request/client-ip";
import { websiteUrlSchema } from "@/lib/validation/website-url";
import type { AuditFormState } from "../actions";

const UNPROCESSABLE_CONTENT = 422;

const idSchema = z.uuid();

function languageFrom(locale: string): Locale {
  return isLocale(locale) ? locale : defaultLocale;
}

function sitesPath(language: Locale, siteId?: string): string {
  return siteId ? `/${language}/sites?site=${siteId}` : `/${language}/sites`;
}

function rateLimitedPath(language: Locale): string {
  return `/${language}/sites?notice=rate_limited`;
}

function isRateLimited(error: unknown): boolean {
  return error instanceof SitesApiError && error.status === TOO_MANY_REQUESTS;
}

async function callerWith(token: string): Promise<SitesCaller> {
  return { token, clientIp: await requestClientIp() };
}

export async function addSite(
  locale: string,
  _previousState: AuditFormState,
  formData: FormData,
): Promise<AuditFormState> {
  const language = languageFrom(locale);
  const submitted = formData.get("url");
  const url = typeof submitted === "string" ? submitted : "";

  const parsed = websiteUrlSchema.safeParse(url);
  if (!parsed.success) return { error: "invalid_url", url };

  let auditId: string;
  try {
    const caller = await callerWith(await ensureOwnerToken());
    const site = await trackSite(caller, parsed.data);
    auditId = (await recheckSite(caller, site.id, language)).id;
  } catch (error) {
    if (error instanceof SitesApiError && error.status === UNPROCESSABLE_CONTENT) {
      return { error: "invalid_url", url };
    }
    if (isRateLimited(error)) return { error: "rate_limited", url };
    console.error("Could not add the site", error);
    return { error: "unavailable", url };
  }
  redirect(`/${language}/audits/${auditId}`);
}

export async function trackAuditedSite(locale: string, auditId: string, url: string) {
  const language = languageFrom(locale);
  const validAuditId = idSchema.parse(auditId);
  const validUrl = websiteUrlSchema.parse(url);

  const caller = await callerWith(await ensureOwnerToken());
  let siteId: string;
  try {
    siteId = (await trackSite(caller, validUrl, validAuditId)).id;
  } catch (error) {
    if (isRateLimited(error)) redirect(rateLimitedPath(language));
    throw error;
  }
  redirect(sitesPath(language, siteId));
}

export async function recheckTrackedSite(locale: string, siteId: string) {
  const language = languageFrom(locale);
  const token = await readOwnerToken();
  if (!token) redirect(sitesPath(language));

  let auditId: string;
  try {
    auditId = (await recheckSite(await callerWith(token), idSchema.parse(siteId), language)).id;
  } catch (error) {
    if (isRateLimited(error)) redirect(rateLimitedPath(language));
    throw error;
  }
  redirect(`/${language}/audits/${auditId}`);
}

export async function removeTrackedSite(locale: string, siteId: string) {
  const language = languageFrom(locale);
  const token = await readOwnerToken();
  if (token) await untrackSite(await callerWith(token), idSchema.parse(siteId));
  redirect(sitesPath(language));
}
