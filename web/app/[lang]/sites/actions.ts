"use server";

import { redirect } from "next/navigation";
import { z } from "zod";
import { SitesApiError, recheckSite, trackSite, untrackSite } from "@/lib/api/sites";
import { defaultLocale, isLocale, type Locale } from "@/lib/i18n/locales";
import { ensureOwnerToken, readOwnerToken } from "@/lib/owner/token";
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
    const token = await ensureOwnerToken();
    const site = await trackSite(token, parsed.data);
    auditId = (await recheckSite(token, site.id, language)).id;
  } catch (error) {
    if (error instanceof SitesApiError && error.status === UNPROCESSABLE_CONTENT) {
      return { error: "invalid_url", url };
    }
    console.error("Could not add the site", error);
    return { error: "unavailable", url };
  }
  redirect(`/${language}/audits/${auditId}`);
}

export async function trackAuditedSite(locale: string, auditId: string, url: string) {
  const language = languageFrom(locale);
  const validAuditId = idSchema.parse(auditId);
  const validUrl = websiteUrlSchema.parse(url);

  const token = await ensureOwnerToken();
  const site = await trackSite(token, validUrl, validAuditId);
  redirect(sitesPath(language, site.id));
}

export async function recheckTrackedSite(locale: string, siteId: string) {
  const language = languageFrom(locale);
  const token = await readOwnerToken();
  if (!token) redirect(sitesPath(language));

  const audit = await recheckSite(token, idSchema.parse(siteId), language);
  redirect(`/${language}/audits/${audit.id}`);
}

export async function removeTrackedSite(locale: string, siteId: string) {
  const language = languageFrom(locale);
  const token = await readOwnerToken();
  if (token) await untrackSite(token, idSchema.parse(siteId));
  redirect(sitesPath(language));
}
