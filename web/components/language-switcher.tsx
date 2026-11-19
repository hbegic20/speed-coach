import Link from "next/link";
import { locales, type Locale } from "@/lib/i18n/locales";

type LanguageSwitcherProps = {
  currentLocale: Locale;
  label: string;
  languageNames: Record<Locale, string>;
};

export function LanguageSwitcher({ currentLocale, label, languageNames }: LanguageSwitcherProps) {
  return (
    <nav aria-label={label}>
      <ul className="flex gap-1">
        {locales.map((locale) => (
          <li key={locale}>
            <Link
              href={`/${locale}`}
              hrefLang={locale}
              lang={locale}
              aria-current={locale === currentLocale ? "true" : undefined}
              className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-md px-3 text-sm font-medium text-slate-600 hover:text-ink aria-[current=true]:bg-white aria-[current=true]:text-ink aria-[current=true]:shadow-sm"
            >
              {languageNames[locale]}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
