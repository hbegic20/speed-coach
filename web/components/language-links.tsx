import Link from "next/link";
import { locales, type Locale } from "@/lib/i18n/locales";

export type LanguageLinksProps = {
  currentLocale: Locale;
  label: string;
  languageNames: Record<Locale, string>;
  hrefFor: (locale: Locale) => string;
};

export function LanguageLinks({ currentLocale, label, languageNames, hrefFor }: LanguageLinksProps) {
  return (
    <nav aria-label={label}>
      <ul className="flex overflow-hidden rounded-lg border border-slate-300 text-sm font-semibold">
        {locales.map((locale) => (
          <li key={locale}>
            <Link
              href={hrefFor(locale)}
              hrefLang={locale}
              lang={locale}
              aria-current={locale === currentLocale ? "true" : undefined}
              className="inline-flex min-h-11 min-w-11 items-center justify-center bg-white px-3 text-slate-600 hover:text-ink aria-[current=true]:bg-ink aria-[current=true]:text-white"
            >
              {languageNames[locale]}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
