import type { DeviceReport } from "@/lib/api/schemas";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { ScoreRing } from "./score-ring";

type ScoreGridProps = {
  report: DeviceReport;
  labels: Dictionary["report"];
};

export function ScoreGrid({ report, labels }: ScoreGridProps) {
  const scores = [
    { key: "performance", label: labels.categories.performance, score: report.performance_score },
    { key: "accessibility", label: labels.categories.accessibility, score: report.accessibility_score },
    { key: "bestPractices", label: labels.categories.bestPractices, score: report.best_practices_score },
    { key: "seo", label: labels.categories.seo, score: report.seo_score },
  ];

  return (
    <section aria-label={labels.scoresLabel}>
      <ul className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4">
        {scores.map(({ key, label, score }) => (
          <li key={key}>
            <ScoreRing
              label={label}
              score={score}
              toneLabels={labels.tones}
              ariaTemplate={labels.scoreAria}
              notMeasuredLabel={labels.noScore}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}
