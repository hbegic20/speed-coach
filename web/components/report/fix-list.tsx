import type { Audit, DeviceReport } from "@/lib/api/schemas";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { fill } from "@/lib/i18n/fill";
import type { Locale } from "@/lib/i18n/locales";
import { estimatedSavingMs } from "@/lib/report/audit-view";
import { formatSaving } from "@/lib/report/format";
import { platformName } from "@/lib/report/platform-names";
import { FixCard } from "./fix-card";

type FixListProps = {
  audit: Audit;
  report: DeviceReport;
  locale: Locale;
  labels: Dictionary["report"]["fixes"];
};

function FixNotice({ message }: { message: string }) {
  return (
    <p className="rounded-2xl border border-slate-200 bg-white p-6 text-slate-700">{message}</p>
  );
}

export function FixList({ audit, report, locale, labels }: FixListProps) {
  const platform = platformName(audit.platform);
  const howToLabel = platform ? fill(labels.howTo, { platform }) : labels.howToGeneric;

  return (
    <section aria-labelledby="fixes-heading" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2.5">
        <h2 id="fixes-heading" className="font-heading text-[26px] font-bold">
          {labels.heading}
        </h2>
        {platform && audit.recommendations.length > 0 ? (
          <span className="rounded-full bg-blue-100 px-2.5 py-1 text-xs font-bold text-blue-900">
            {fill(labels.badge, { platform })}
          </span>
        ) : null}
      </div>
      {audit.failure_reason === "recommendations_unavailable" ? (
        <FixNotice message={labels.unavailable} />
      ) : audit.recommendations.length === 0 ? (
        <FixNotice message={labels.none} />
      ) : (
        <>
          {audit.summary ? (
            <p className="max-w-3xl text-lg leading-relaxed text-slate-700">{audit.summary}</p>
          ) : null}
          <ol className="flex flex-col gap-4">
            {audit.recommendations.map((recommendation) => {
              const saving = estimatedSavingMs(recommendation, report);
              return (
                <li key={recommendation.rank}>
                  <FixCard
                    recommendation={recommendation}
                    howToLabel={howToLabel}
                    saving={saving === null ? null : formatSaving(saving, locale)}
                    labels={labels}
                  />
                </li>
              );
            })}
          </ol>
        </>
      )}
    </section>
  );
}
