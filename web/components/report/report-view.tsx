import type { AuditFormState } from "@/app/[lang]/actions";
import { AuditForm } from "@/components/audit-form";
import { TrackSiteButton } from "@/components/sites/track-site-button";
import type { Audit, Device } from "@/lib/api/schemas";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { fill } from "@/lib/i18n/fill";
import type { Locale } from "@/lib/i18n/locales";
import { reportForDevice } from "@/lib/report/audit-view";
import { displayHost, formatCheckedAt } from "@/lib/report/format";
import type { FixTracking } from "@/lib/report/fix-status";
import { platformName } from "@/lib/report/platform-names";
import { FailurePanel, ProgressPanel } from "./audit-status-panel";
import { DeviceToggle } from "./device-toggle";
import { FixList } from "./fix-list";
import { ScoreGrid } from "./score-grid";
import { VitalsCard } from "./vitals-card";

type ReportViewProps = {
  audit: Audit;
  device: Device;
  locale: Locale;
  dictionary: Dictionary;
  rerunAction: (state: AuditFormState, formData: FormData) => Promise<AuditFormState>;
  fixTracking: FixTracking | null;
};

export function ReportView({
  audit,
  device,
  locale,
  dictionary,
  rerunAction,
  fixTracking,
}: ReportViewProps) {
  const labels = dictionary.report;
  const report = reportForDevice(audit, device);
  const platform = platformName(audit.platform);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-7 px-4 pt-2 pb-16 sm:px-8">
      <AuditForm
        action={rerunAction}
        labels={{ ...dictionary.form, submit: dictionary.form.rerun }}
        variant="compact"
        initialUrl={audit.url}
      />

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex min-w-0 flex-col gap-2">
          <p className="text-[13px] font-semibold tracking-[0.8px] text-slate-600 uppercase">
            {fill(labels.checkedAt, { date: formatCheckedAt(audit.updated_at, locale) })}
          </p>
          <h1 className="font-heading text-[28px] font-bold tracking-tight break-words sm:text-[40px] sm:tracking-[-0.8px]">
            {displayHost(audit.url)}
          </h1>
          {platform ? (
            <p className="self-start rounded-full bg-violet-100 px-2.5 py-1 text-[13px] font-semibold text-violet-900">
              {fill(labels.platform, { platform })}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          {report ? (
            <DeviceToggle
              current={report.device}
              basePath={`/${locale}/audits/${audit.id}`}
              groupLabel={labels.deviceGroup}
              deviceLabels={labels.devices}
            />
          ) : null}
          <TrackSiteButton
            locale={locale}
            auditId={audit.id}
            url={audit.url}
            label={dictionary.sites.trackButton}
          />
        </div>
      </div>

      {audit.status === "queued" || audit.status === "running" ? (
        <ProgressPanel status={audit.status} labels={labels.progress} />
      ) : null}
      {audit.status === "failed" && !report ? (
        <FailurePanel reason={audit.failure_reason} labels={labels.failures} />
      ) : null}
      {report && audit.status !== "queued" && audit.status !== "running" ? (
        <>
          <ScoreGrid report={report} labels={labels} />
          <VitalsCard report={report} locale={locale} labels={labels} />
          <FixList
            audit={audit}
            report={report}
            locale={locale}
            tracking={fixTracking}
            labels={labels.fixes}
          />
        </>
      ) : null}
    </div>
  );
}
