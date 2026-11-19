import Link from "next/link";
import { lang } from "next/root-params";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { defaultLocale, isLocale } from "@/lib/i18n/locales";

export default async function NotFound() {
  const requested = await lang();
  const locale = isLocale(requested) ? requested : defaultLocale;
  const { notFound } = getDictionary(locale);

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-start gap-4 px-4 py-16 sm:px-8">
      <h1 className="font-heading text-4xl font-bold">{notFound.heading}</h1>
      <p className="text-lg text-slate-600">{notFound.body}</p>
      <Link
        href={`/${locale}`}
        className="inline-flex min-h-11 items-center rounded-[10px] bg-accent px-5 font-semibold text-white hover:bg-blue-800"
      >
        {notFound.action}
      </Link>
    </main>
  );
}
