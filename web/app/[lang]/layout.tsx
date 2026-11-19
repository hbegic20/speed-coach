import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import { SiteHeader } from "@/components/site-header";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { locales } from "@/lib/i18n/locales";
import { resolveLocale } from "@/lib/i18n/resolve-locale";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin", "latin-ext"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin", "latin-ext"],
  display: "swap",
});

export function generateStaticParams() {
  return locales.map((lang) => ({ lang }));
}

export async function generateMetadata({ params }: LayoutProps<"/[lang]">): Promise<Metadata> {
  const { metadata } = getDictionary(await resolveLocale(params));
  return { title: metadata.title, description: metadata.description };
}

export default async function RootLayout({ children, params }: LayoutProps<"/[lang]">) {
  const locale = await resolveLocale(params);
  const dictionary = getDictionary(locale);

  return (
    <html lang={locale} className={`${inter.variable} ${spaceGrotesk.variable} h-full`}>
      <body className="flex min-h-full flex-col">
        <SiteHeader locale={locale} dictionary={dictionary} />
        {children}
      </body>
    </html>
  );
}
