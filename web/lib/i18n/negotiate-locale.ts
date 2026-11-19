import { defaultLocale, isLocale, type Locale } from "./locales";

type LanguagePreference = {
  language: string;
  quality: number;
};

function parsePreference(entry: string): LanguagePreference {
  const [tag = "", ...parameters] = entry.trim().split(";");
  const qualityParameter = parameters.find((parameter) => parameter.trim().startsWith("q="));
  const quality = qualityParameter ? Number(qualityParameter.trim().slice(2)) : 1;
  const [language = ""] = tag.toLowerCase().split("-");
  return { language, quality: Number.isFinite(quality) ? quality : 0 };
}

export function negotiateLocale(acceptLanguage: string | null): Locale {
  if (!acceptLanguage) return defaultLocale;

  const preferred = acceptLanguage
    .split(",")
    .map(parsePreference)
    .filter((preference) => preference.quality > 0)
    .sort((first, second) => second.quality - first.quality)
    .map((preference) => preference.language)
    .find(isLocale);

  return preferred ?? defaultLocale;
}
