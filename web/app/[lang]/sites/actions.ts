"use server";

import { redirect } from "next/navigation";
import { z } from "zod";
import { TOO_MANY_REQUESTS } from "@/lib/api/client";
import {
  SitesApiError,
  recheckSite,
  setCompletedFixes,
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
const CONFLICT = 409;

export type DashboardNotice = "rate_limited" | "site_limit_reached";

const idSchema = z.uuid();
const lighthouseIdsSchema = z.array(z.string().regex(/^[a-z0-9-]{1,128}$/)).min(1).max(20);

function languageFrom(locale: string): Locale {
  return isLocale(locale) ? locale : defaultLocale;
}

function sitesPath(language: Locale, siteId?: string): string {
  return siteId ? `/${language}/sites?site=${siteId}` : `/${language}/sites`;
}

function noticePath(language: Locale, notice: DashboardNotice): string {
  return `/${language}/sites?notice=${notice}`;
}

function hasStatus(error: unknown, status: number): boolean {
  return error instanceof SitesApiError && error.status === status;
}

function noticeFor(error: unknown): DashboardNotice | null {
  if (hasStatus(error, TOO_MANY_REQUESTS)) return "rate_limited";
  if (hasStatus(error, CONFLICT)) return "site_limit_reached";
  return null;
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
    if (hasStatus(error, UNPROCESSABLE_CONTENT)) return { error: "invalid_url", url };
    const notice = noticeFor(error);
    if (notice) return { error: notice, url };
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
    const notice = noticeFor(error);
    if (notice) redirect(noticePath(language, notice));
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
    if (hasStatus(error, TOO_MANY_REQUESTS)) redirect(noticePath(language, "rate_limited"));
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

export async function setFixCompletion(
  locale: string,
  siteId: string,
  auditId: string,
  device: string,
  lighthouseIds: string[],
  completed: boolean,
) {
  const language = languageFrom(locale);
  const validAuditId = idSchema.parse(auditId);
  const reportPath = `/${language}/audits/${validAuditId}${device === "desktop" ? "?device=desktop" : ""}`;
  const token = await readOwnerToken();
  if (!token) redirect(reportPath);

  await setCompletedFixes(
    await callerWith(token),
    idSchema.parse(siteId),
    lighthouseIdsSchema.parse(lighthouseIds),
    completed,
  );
  redirect(reportPath);
}
