import Link from "next/link";
import { recheckTrackedSite, removeTrackedSite } from "@/app/[lang]/sites/actions";
import type { Site } from "@/lib/api/schemas";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { Locale } from "@/lib/i18n/locales";
import { displayHost, formatCheckDate } from "@/lib/report/format";
import { platformName } from "@/lib/report/platform-names";
import { latestCheck, reportAuditId, scoreChange } from "@/lib/report/site-history";
import { scoreTone } from "@/lib/report/tone";
import { TONE_TEXT } from "@/components/report/tone-styles";
import { ChangeIndicator } from "./change-indicator";

type SitesTableProps = {
  sites: Site[];
  locale: Locale;
  dictionary: Dictionary;
};

const CELL = "px-5 py-4";
const ACTION_BUTTON =
  "inline-flex min-h-11 items-center rounded-lg px-3 font-semibold hover:bg-slate-100";

function isChecking(site: Site): boolean {
  const status = site.latest_audit?.status;
  return status === "queued" || status === "running";
}

export function SitesTable({ sites, locale, dictionary }: SitesTableProps) {
  const labels = dictionary.sites.table;

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-[15px]">
          <caption className="sr-only">{labels.caption}</caption>
          <thead>
            <tr className="bg-slate-50 text-left text-[13px] text-slate-600">
              <th scope="col" className={`${CELL} font-semibold`}>{labels.site}</th>
              <th scope="col" className={`${CELL} font-semibold`}>{labels.platform}</th>
              <th scope="col" className={`${CELL} font-semibold`}>{labels.performance}</th>
              <th scope="col" className={`${CELL} font-semibold`}>{labels.change}</th>
              <th scope="col" className={`${CELL} font-semibold`}>{labels.lastCheck}</th>
              <th scope="col" className={`${CELL} font-semibold`}>
                <span className="sr-only">{labels.actions}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {sites.map((site) => {
              const latest = latestCheck(site);
              const auditId = reportAuditId(site);
              const tone = latest ? scoreTone(latest.mobile_performance_score) : null;
              const host = displayHost(site.url);
              return (
                <tr key={site.id} className="border-t border-slate-200">
                  <th scope="row" className={`${CELL} text-left font-semibold`}>{host}</th>
                  <td className={`${CELL} text-slate-600`}>
                    {platformName(latest?.platform ?? null) ?? labels.unknownPlatform}
                  </td>
                  <td className={CELL}>
                    {latest && tone ? (
                      <span className={TONE_TEXT[tone]}>
                        <span className="font-heading text-lg font-bold">
                          {latest.mobile_performance_score}
                        </span>{" "}
                        <span className="text-[13px] font-semibold">
                          {dictionary.report.tones[tone]}
                        </span>
                      </span>
                    ) : (
                      <span className="text-slate-600">{labels.notChecked}</span>
                    )}
                  </td>
                  <td className={CELL}>
                    <ChangeIndicator change={scoreChange(site)} labels={dictionary.sites.change} />
                  </td>
                  <td className={`${CELL} text-slate-600`}>
                    {isChecking(site)
                      ? labels.running
                      : latest
                        ? formatCheckDate(latest.checked_at, locale)
                        : labels.notChecked}
                  </td>
                  <td className={`${CELL} text-right`}>
                    <div className="flex flex-wrap justify-end gap-1">
                      {auditId ? (
                        <Link
                          href={`/${locale}/audits/${auditId}`}
                          aria-label={`${labels.viewReport}: ${host}`}
                          className={`${ACTION_BUTTON} text-accent`}
                        >
                          {labels.viewReport}
                        </Link>
                      ) : null}
                      <form action={recheckTrackedSite.bind(null, locale, site.id)}>
                        <button
                          type="submit"
                          aria-label={`${labels.recheck}: ${host}`}
                          className={`${ACTION_BUTTON} text-ink`}
                        >
                          {labels.recheck}
                        </button>
                      </form>
                      <form action={removeTrackedSite.bind(null, locale, site.id)}>
                        <button
                          type="submit"
                          aria-label={`${labels.remove}: ${host}`}
                          className={`${ACTION_BUTTON} text-poor`}
                        >
                          {labels.remove}
                        </button>
                      </form>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
