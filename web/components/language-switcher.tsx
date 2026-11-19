"use client";

import { usePathname } from "next/navigation";
import { localizedPath } from "@/lib/i18n/locales";
import { LanguageLinks, type LanguageLinksProps } from "./language-links";

export function LanguageSwitcher(props: Omit<LanguageLinksProps, "hrefFor">) {
  const pathname = usePathname();
  return <LanguageLinks {...props} hrefFor={(locale) => localizedPath(pathname, locale)} />;
}
