import { getDictionary } from "@/lib/i18n/dictionaries";
import { resolveLocale } from "@/lib/i18n/resolve-locale";

export default async function HomePage({ params }: PageProps<"/[lang]">) {
  const { home } = getDictionary(await resolveLocale(params));

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center gap-6 px-4 py-16 sm:px-6">
      <h1 className="font-heading text-4xl font-bold tracking-tight text-balance sm:text-5xl">
        {home.heading}
      </h1>
      <p className="max-w-xl text-lg text-slate-600">{home.lead}</p>
    </main>
  );
}
