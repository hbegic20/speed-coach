import type { Locale } from "@/lib/i18n/locales";

const NUMBER_LOCALES: Record<Locale, string> = { bs: "bs-BA", en: "en-GB" };
const MILLISECONDS_PER_SECOND = 1000;

function formatNumber(value: number, locale: Locale, fractionDigits: number): string {
  return new Intl.NumberFormat(NUMBER_LOCALES[locale], {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

export function formatDuration(milliseconds: number, locale: Locale): string {
  if (milliseconds < MILLISECONDS_PER_SECOND) {
    return `${formatNumber(Math.round(milliseconds), locale, 0)} ms`;
  }
  return `${formatNumber(milliseconds / MILLISECONDS_PER_SECOND, locale, 1)} s`;
}

export function formatLayoutShift(value: number, locale: Locale): string {
  return formatNumber(value, locale, 2);
}

export function formatSaving(milliseconds: number, locale: Locale): string {
  return `−${formatDuration(milliseconds, locale)}`;
}

export function formatCheckedAt(isoTimestamp: string, locale: Locale): string {
  return new Intl.DateTimeFormat(NUMBER_LOCALES[locale], {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Sarajevo",
  }).format(new Date(isoTimestamp));
}

export function displayHost(url: string): string {
  const { hostname, pathname } = new URL(url);
  const path = pathname === "/" ? "" : pathname;
  return `${hostname.replace(/^www\./, "")}${path}`;
}

export function formatCheckDate(isoTimestamp: string, locale: Locale): string {
  return new Intl.DateTimeFormat(NUMBER_LOCALES[locale], {
    day: "numeric",
    month: "short",
    timeZone: "Europe/Sarajevo",
  }).format(new Date(isoTimestamp));
}
