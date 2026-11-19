import type { Metadata } from "next";
import Link from "next/link";
import { unstable_rethrow } from "next/navigation";
import { Suspense } from "react";
import { AuditForm } from "@/components/audit-form";
import { SitePicker } from "@/components/sites/site-picker";
import { SitesTable } from "@/components/sites/sites-table";
import { StatCards } from "@/components/sites/stat-cards";
import { TrendChart } from "@/components/sites/trend-chart";
import { listSites, type SiteList } from "@/lib/api/sites";
import type { Site } from "@/lib/api/schemas";
import { getDictionary, type Dictionary } from "@/lib/i18n/dictionaries";
import { fill } from "@/lib/i18n/fill";
import type { Locale } from "@/lib/i18n/locales";
import { resolveLocale } from "@/lib/i18n/resolve-locale";
import { readOwnerToken } from "@/lib/owner/token";
import { displayHost } from "@/lib/report/format";
import { selectedSite } from "@/lib/report/site-history";
import { addSite, type DashboardNotice } from "./actions";

type SitesPageProps = PageProps<"/[lang]/sites">;

export async function generateMetadata({ params }: SitesPageProps): Promise<Metadata> {
  const { metadata, sites } = getDictionary(await resolveLocale(params));
  return { title: `${sites.metadataTitle} · ${metadata.title}`, robots: { index: false } };
}

async function loadSites(): Promise<SiteList | null> {
  const token = await readOwnerToken();
  if (!token) return { sites: [], siteLimit: null };
  try {
    return await listSites({ token, clientIp: null });
  } catch (error) {
    unstable_rethrow(error);
    console.error("Could not load tracked sites", error);
    return null;
  }
}

function EmptyState({ locale, labels }: { locale: Locale; labels: Dictionary["sites"] }) {
  return (
    <section className="flex flex-col items-start gap-3 rounded-2xl border border-slate-200 bg-white p-6">
      <h2 className="font-heading text-[22px] font-bold">{labels.empty.heading}</h2>
      <p className="max-w-2xl text-slate-600">{labels.empty.body}</p>
      <Link href={`/${locale}`} className="inline-flex min-h-11 items-center font-semibold text-accent">
        {labels.addSite}
      </Link>
    </section>
  );
}

function SitesOverview({
  sites,
  siteLimit,
  selectedId,
  locale,
  dictionary,
}: {
  sites: Site[];
  siteLimit: number | null;
  selectedId: string | string[] | undefined;
  locale: Locale;
  dictionary: Dictionary;
}) {
  const labels = dictionary.sites;
  const chartSite = selectedSite(sites, selectedId);

  return (
    <>
      <StatCards sites={sites} siteLimit={siteLimit} labels={labels} />
      {chartSite ? (
        <section
          aria-labelledby="trend-heading"
          className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-col gap-1">
              <h2 id="trend-heading" className="font-heading text-[22px] font-bold">
                {fill(labels.chart.heading, { site: displayHost(chartSite.url) })}
              </h2>
              <p className="text-sm text-slate-600">{labels.chart.subheading}</p>
            </div>
            {sites.length > 1 ? (
              <SitePicker
                sites={sites}
                selectedId={chartSite.id}
                action={`/${locale}/sites`}
                label={labels.chart.siteLabel}
                submitLabel={labels.chart.show}
              />
            ) : null}
          </div>
          <TrendChart site={chartSite} locale={locale} labels={labels.chart} />
        </section>
      ) : null}
      <SitesTable sites={sites} locale={locale} dictionary={dictionary} />
    </>
  );
}

function AddSiteArea({
  siteCount,
  siteLimit,
  locale,
  dictionary,
}: {
  siteCount: number;
  siteLimit: number | null;
  locale: Locale;
  dictionary: Dictionary;
}) {
  if (siteLimit !== null && siteCount >= siteLimit) {
    return (
      <p className="rounded-2xl border border-slate-200 bg-white p-4 text-slate-700">
        {fill(dictionary.sites.limitReached, { limit: siteLimit })}
      </p>
    );
  }
  return (
    <AuditForm
      action={addSite.bind(null, locale)}
      labels={{ ...dictionary.form, submit: dictionary.sites.addSite }}
      variant="compact"
    />
  );
}

const DASHBOARD_NOTICES: readonly DashboardNotice[] = ["rate_limited"];

function dashboardNotice(value: string | string[] | undefined): DashboardNotice | null {
  return DASHBOARD_NOTICES.find((notice) => notice === value) ?? null;
}

async function SitesDashboard({ params, searchParams }: SitesPageProps) {
  const locale = await resolveLocale(params);
  const dictionary = getDictionary(locale);
  const [siteList, query] = await Promise.all([loadSites(), searchParams]);

  if (siteList === null) {
    return (
      <p role="alert" className="rounded-2xl border border-slate-200 bg-white p-6 text-slate-700">
        {dictionary.sites.unavailable}
      </p>
    );
  }
  const notice = dashboardNotice(query.notice);
  const { sites, siteLimit } = siteList;
  return (
    <>
      <AddSiteArea
        siteCount={sites.length}
        siteLimit={siteLimit}
        locale={locale}
        dictionary={dictionary}
      />
      {notice ? (
        <p
          role="alert"
          className="rounded-2xl border border-needs-work-soft bg-white p-4 font-medium text-needs-work-strong"
        >
          {dictionary.form.errors[notice]}
        </p>
      ) : null}
      {sites.length === 0 ? (
        <EmptyState locale={locale} labels={dictionary.sites} />
      ) : (
        <SitesOverview
          sites={sites}
          siteLimit={siteLimit}
          selectedId={query.site}
          locale={locale}
          dictionary={dictionary}
        />
      )}
    </>
  );
}

async function SitesHeading({ params }: Pick<SitesPageProps, "params">) {
  const { sites } = getDictionary(await resolveLocale(params));
  return (
    <div className="flex flex-col gap-1">
      <h1 className="font-heading text-[34px] font-bold tracking-[-0.6px]">{sites.heading}</h1>
      <p className="text-sm text-slate-600">{sites.subheading}</p>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div aria-busy="true" className="flex flex-col gap-6">
      <div className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
        <div className="h-28 rounded-[14px] bg-slate-200" />
        <div className="h-28 rounded-[14px] bg-slate-200" />
      </div>
      <div className="h-80 rounded-2xl bg-slate-200" />
    </div>
  );
}

export default function SitesPage(props: SitesPageProps) {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 pt-2 pb-16 sm:px-8">
      <SitesHeading params={props.params} />
      <Suspense fallback={<DashboardSkeleton />}>
        <SitesDashboard {...props} />
      </Suspense>
    </main>
  );
}
