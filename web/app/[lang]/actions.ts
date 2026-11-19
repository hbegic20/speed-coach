"use server";

import { redirect } from "next/navigation";
import { z } from "zod";
import { createAudit } from "@/lib/api/audits";
import { defaultLocale, isLocale } from "@/lib/i18n/locales";
import { normalizeUrlInput } from "@/lib/report/normalize-url";

export type AuditFormError = "invalid_url" | "unavailable";

export type AuditFormState = {
  error: AuditFormError | null;
  url: string;
};

const MAX_URL_LENGTH = 2048;

const websiteUrlSchema = z
  .string()
  .max(MAX_URL_LENGTH)
  .transform(normalizeUrlInput)
  .pipe(z.url({ protocol: /^https?$/, hostname: z.regexes.domain }));

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

  const result = await createAudit(parsed.data, language);
  if (!result.ok) return { error: result.error, url };

  redirect(`/${language}/audits/${result.audit.id}`);
}
