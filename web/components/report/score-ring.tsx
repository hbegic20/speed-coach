import { fill } from "@/lib/i18n/fill";
import { scoreTone, type Tone } from "@/lib/report/tone";
import { TONE_TEXT } from "./tone-styles";

const RADIUS = 34;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

type ScoreRingProps = {
  label: string;
  score: number | null;
  toneLabels: Record<Tone, string>;
  ariaTemplate: string;
  notMeasuredLabel: string;
};

export function ScoreRing({
  label,
  score,
  toneLabels,
  ariaTemplate,
  notMeasuredLabel,
}: ScoreRingProps) {
  const tone = score === null ? null : scoreTone(score);
  const filled = score === null ? 0 : (CIRCUMFERENCE * score) / 100;

  return (
    <div className="flex items-center gap-4.5 rounded-2xl border border-slate-200 bg-white p-5.5">
      <svg
        width="84"
        height="84"
        viewBox="0 0 84 84"
        role="img"
        aria-label={
          score === null ? `${label}: ${notMeasuredLabel}` : fill(ariaTemplate, { label, value: score })
        }
        className={tone ? TONE_TEXT[tone] : "text-slate-400"}
      >
        <circle cx="42" cy="42" r={RADIUS} fill="none" className="stroke-slate-200" strokeWidth="8" />
        <circle
          cx="42"
          cy="42"
          r={RADIUS}
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${filled.toFixed(1)} ${CIRCUMFERENCE.toFixed(1)}`}
          transform="rotate(-90 42 42)"
        />
        <text
          x="42"
          y="49"
          textAnchor="middle"
          className="fill-ink font-heading text-2xl font-bold"
        >
          {score ?? "–"}
        </text>
      </svg>
      <div className="flex flex-col gap-1.5">
        <span className="text-base font-semibold">{label}</span>
        <span className={`text-[13px] font-semibold ${tone ? TONE_TEXT[tone] : "text-slate-600"}`}>
          {tone ? toneLabels[tone] : notMeasuredLabel}
        </span>
      </div>
    </div>
  );
}
