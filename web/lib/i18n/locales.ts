export const locales = ["bs", "en"] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "bs";

export function isLocale(value: string): value is Locale {
  return locales.some((locale) => locale === value);
}

export function pathnameHasLocale(pathname: string): boolean {
  const [, firstSegment = ""] = pathname.split("/");
  return isLocale(firstSegment);
}
