import Link from "next/link";
import { Suspense } from "react";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { Locale } from "@/lib/i18n/locales";
import { LanguageLinks } from "./language-links";
import { LanguageSwitcher } from "./language-switcher";
import { LogoMark } from "./logo-mark";

type SiteHeaderProps = {
  locale: Locale;
  dictionary: Dictionary;
};

export function SiteHeader({ locale, dictionary }: SiteHeaderProps) {
  const languageProps = {
    currentLocale: locale,
    label: dictionary.header.languageNavigation,
    languageNames: dictionary.languageNames,
  };

  return (
    <header className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-8 sm:py-6">
      <Link
        href={`/${locale}`}
        aria-label={dictionary.header.homeLink}
        className="inline-flex min-h-11 items-center gap-2.5"
      >
        <LogoMark size={32} />
        <span className="font-heading text-[22px] font-bold">SpeedCoach</span>
      </Link>
      <div className="flex flex-wrap items-center gap-6 text-[15px]">
        <Link
          href={`/${locale}#how`}
          className="inline-flex min-h-11 items-center text-slate-700 hover:text-ink"
        >
          {dictionary.header.howItWorks}
        </Link>
        <Link
          href={`/${locale}/sites`}
          className="inline-flex min-h-11 items-center text-slate-700 hover:text-ink"
        >
          {dictionary.sites.navLink}
        </Link>
        <Suspense
          fallback={
            <LanguageLinks
              {...languageProps}
              hrefFor={(targetLocale) => `/${targetLocale}`}
            />
          }
        >
          <LanguageSwitcher {...languageProps} />
        </Suspense>
      </div>
    </header>
  );
}
