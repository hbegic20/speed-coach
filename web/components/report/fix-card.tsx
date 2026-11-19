import type { ReactNode } from "react";
import type { Recommendation } from "@/lib/api/schemas";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { IMPACT_BADGE } from "./tone-styles";

type FixCardProps = {
  recommendation: Recommendation;
  howToLabel: string;
  saving: string | null;
  completion: ReactNode;
  labels: Dictionary["report"]["fixes"];
};

export function FixCard({
  recommendation,
  howToLabel,
  saving,
  completion,
  labels,
}: FixCardProps) {
  const titleId = `fix-${recommendation.rank}`;

  return (
    <article
      aria-labelledby={titleId}
      className="flex flex-wrap gap-5 rounded-2xl border border-slate-200 bg-white px-6 py-5.5"
    >
      <span
        aria-hidden="true"
        className="flex size-11 flex-none items-center justify-center rounded-xl bg-ink font-heading text-lg font-bold text-white"
      >
        {recommendation.rank}
      </span>
      <div className="flex min-w-0 flex-[999_1_420px] flex-col gap-2.5">
        <div className="flex flex-wrap items-center gap-2.5">
          <h3 id={titleId} className="text-lg font-semibold">
            <span className="sr-only">{recommendation.rank}.</span> {recommendation.title}
          </h3>
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${IMPACT_BADGE[recommendation.impact]}`}
          >
            {labels.impact[recommendation.impact]}
          </span>
        </div>
        <p className="leading-relaxed text-slate-700">{recommendation.explanation}</p>
        <div className="rounded-[10px] border border-slate-200 bg-slate-50 px-3.5 py-3 text-sm leading-normal">
          <p className="font-semibold">{howToLabel}</p>
          <ol className="mt-1.5 list-decimal space-y-1 pl-5">
            {recommendation.steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      </div>
      {saving || completion ? (
        <div className="flex flex-[1_1_160px] flex-col items-start gap-3">
          {saving ? (
            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold tracking-wide text-slate-600 uppercase">
                {labels.saving}
              </span>
              <span className="font-heading text-[28px] font-bold text-good">{saving}</span>
            </div>
          ) : null}
          {completion}
        </div>
      ) : null}
    </article>
  );
}
