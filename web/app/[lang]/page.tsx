import { AuditForm } from "@/components/audit-form";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { resolveLocale } from "@/lib/i18n/resolve-locale";
import { submitAudit } from "./actions";

export default async function HomePage({ params }: PageProps<"/[lang]">) {
  const locale = await resolveLocale(params);
  const { home, form } = getDictionary(locale);

  return (
    <main className="flex-1">
      <section className="mx-auto flex max-w-6xl flex-col items-center gap-7 px-4 pt-12 pb-10 text-center sm:px-8 sm:pt-18">
        <span className="rounded-full bg-blue-100 px-3 py-1.5 text-[13px] font-semibold text-blue-900">
          {home.badge}
        </span>
        <h1 className="max-w-4xl font-heading text-4xl leading-[1.05] font-bold tracking-tight text-balance sm:text-6xl sm:tracking-[-1.5px]">
          {home.heading}
        </h1>
        <p className="max-w-2xl text-lg leading-relaxed text-slate-600 sm:text-[19px]">
          {home.lead}
        </p>
        <AuditForm action={submitAudit.bind(null, locale)} labels={form} variant="hero" />
        <p className="text-sm text-slate-600">{home.note}</p>
      </section>

      <section
        id="how"
        aria-labelledby="how-heading"
        className="mx-auto max-w-6xl scroll-mt-6 px-4 pt-10 pb-20 sm:px-8"
      >
        <h2 id="how-heading" className="sr-only">
          {home.howItWorksHeading}
        </h2>
        <ol className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-5">
          {home.steps.map((step, index) => (
            <li
              key={step.title}
              className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-7"
            >
              <span
                aria-hidden="true"
                className="flex size-10 items-center justify-center rounded-[10px] bg-blue-100 font-heading font-bold text-blue-900"
              >
                {index + 1}
              </span>
              <h3 className="font-heading text-[22px] font-bold">{step.title}</h3>
              <p className="leading-relaxed text-slate-600">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
