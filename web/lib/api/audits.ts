import type { Locale } from "@/lib/i18n/locales";
import { apiUrl } from "./client";
import { auditSchema, type Audit } from "./schemas";

export type CreateAuditResult =
  | { ok: true; audit: Audit }
  | { ok: false; error: "invalid_url" | "unavailable" };

const UNPROCESSABLE_CONTENT = 422;
const NOT_FOUND = 404;

export async function createAudit(url: string, language: Locale): Promise<CreateAuditResult> {
  let response: Response;
  try {
    response = await fetch(apiUrl("/audits"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, language }),
      cache: "no-store",
    });
  } catch (error) {
    console.error("Could not reach the SpeedCoach API", error);
    return { ok: false, error: "unavailable" };
  }

  if (response.status === UNPROCESSABLE_CONTENT) return { ok: false, error: "invalid_url" };
  if (!response.ok) {
    console.error("SpeedCoach API rejected the audit", response.status);
    return { ok: false, error: "unavailable" };
  }
  const parsed = auditSchema.safeParse(await response.json());
  if (!parsed.success) {
    console.error("SpeedCoach API returned an unexpected audit", parsed.error);
    return { ok: false, error: "unavailable" };
  }
  return { ok: true, audit: parsed.data };
}

export async function getAudit(id: string): Promise<Audit | null> {
  const response = await fetch(apiUrl(`/audits/${encodeURIComponent(id)}`), {
    cache: "no-store",
  });
  if (response.status === NOT_FOUND) return null;
  if (!response.ok) throw new Error(`SpeedCoach API responded ${response.status}`);
  return auditSchema.parse(await response.json());
}
