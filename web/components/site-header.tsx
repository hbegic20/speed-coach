import Link from "next/link";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { Locale } from "@/lib/i18n/locales";
import { LanguageSwitcher } from "./language-switcher";

type SiteHeaderProps = {
  locale: Locale;
  dictionary: Dictionary;
};

export function SiteHeader({ locale, dictionary }: SiteHeaderProps) {
  return (
    <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
      <Link
        href={`/${locale}`}
        aria-label={dictionary.header.homeLink}
        className="inline-flex min-h-11 items-center font-heading text-lg font-bold tracking-tight"
      >
        SpeedCoach
      </Link>
      <LanguageSwitcher
        currentLocale={locale}
        label={dictionary.header.languageNavigation}
        languageNames={dictionary.languageNames}
      />
    </header>
  );
}
