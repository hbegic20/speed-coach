"use server";

import { redirect } from "next/navigation";
import { createAudit } from "@/lib/api/audits";
import { defaultLocale, isLocale } from "@/lib/i18n/locales";
import { requestClientIp } from "@/lib/request/client-ip";
import { websiteUrlSchema } from "@/lib/validation/website-url";

export type AuditFormError = "invalid_url" | "rate_limited" | "unavailable";

export type AuditFormState = {
  error: AuditFormError | null;
  url: string;
};

export async function submitAudit(
  locale: string,
  _previousState: AuditFormState,
  formData: FormData,
): Promise<AuditFormState> {
  const language = isLocale(locale) ? locale : defaultLocale;
  const submitted = formData.get("url");
  const url = typeof submitted === "string" ? submitted : "";

  const parsed = websiteUrlSchema.safeParse(url);
  if (!parsed.success) return { error: "invalid_url", url };

  const result = await createAudit(parsed.data, language, await requestClientIp());
  if (!result.ok) return { error: result.error, url };

  redirect(`/${language}/audits/${result.audit.id}`);
}
