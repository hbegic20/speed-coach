import type { Locale } from "../locales";
import { bs } from "./bs";
import { en, type Dictionary } from "./en";

const dictionaries: Record<Locale, Dictionary> = { bs, en };

export function getDictionary(locale: Locale): Dictionary {
  return dictionaries[locale];
}

export type { Dictionary };
