import type { DeviceReport } from "@/lib/api/schemas";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { Locale } from "@/lib/i18n/locales";
import { formatDuration, formatLayoutShift } from "@/lib/report/format";
import { metricTone, type Metric } from "@/lib/report/tone";
import { TONE_BADGE, TONE_TEXT } from "./tone-styles";

type VitalsCardProps = {
  report: DeviceReport;
  locale: Locale;
  labels: Dictionary["report"];
};

type Vital = {
  metric: Metric;
  value: number | null;
  formatted: string | null;
};

function vitalsFor(report: DeviceReport, locale: Locale): Vital[] {
  const durationVital = (metric: Metric, value: number | null): Vital => ({
    metric,
    value,
    formatted: value === null ? null : formatDuration(value, locale),
  });
  return [
    durationVital("largestContentfulPaint", report.largest_contentful_paint_ms),
    durationVital("totalBlockingTime", report.total_blocking_time_ms),
    {
      metric: "cumulativeLayoutShift",
      value: report.cumulative_layout_shift,
      formatted:
        report.cumulative_layout_shift === null
          ? null
          : formatLayoutShift(report.cumulative_layout_shift, locale),
    },
  ];
}

export function VitalsCard({ report, locale, labels }: VitalsCardProps) {
  return (
    <section
      aria-labelledby="vitals-heading"
      className="flex flex-col gap-4.5 rounded-2xl border border-slate-200 bg-white p-6"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="vitals-heading" className="font-heading text-[22px] font-bold">
          {labels.vitals.heading}
        </h2>
        <p className="text-sm text-slate-600">{labels.vitals.subheading}</p>
      </div>
      <ul className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4">
        {vitalsFor(report, locale).map(({ metric, value, formatted }) => {
          const tone = value === null ? null : metricTone(metric, value);
          const copy = labels.vitals[metric];
          return (
            <li
              key={metric}
              className="flex flex-col gap-2.5 rounded-xl border border-slate-200 p-4.5"
            >
              <div className="flex items-center justify-between gap-2">
                <h3 className="font-semibold">{copy.name}</h3>
                {tone ? (
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-bold ${TONE_BADGE[tone]}`}
                  >
                    {labels.tones[tone]}
                  </span>
                ) : null}
              </div>
              <p
                className={`font-heading text-[34px] font-bold ${tone ? TONE_TEXT[tone] : "text-slate-600"}`}
              >
                {formatted ?? labels.vitals.notMeasured}
              </p>
              <p className="text-sm leading-normal text-slate-600">{copy.plain}</p>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
