import type { Site } from "@/lib/api/schemas";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { fill } from "@/lib/i18n/fill";
import type { Locale } from "@/lib/i18n/locales";
import { displayHost, formatCheckDate } from "@/lib/report/format";
import { chartPoints, scoredChecks, type ChartArea } from "@/lib/report/site-history";
import { scoreTone } from "@/lib/report/tone";
import { TONE_TEXT } from "@/components/report/tone-styles";

const WIDTH = 960;
const HEIGHT = 280;
const AREA: ChartArea = { left: 48, right: 930, top: 24, bottom: 244 };
const GRID_SCORES = [100, 75, 50, 25, 0];

type TrendChartProps = {
  site: Site;
  locale: Locale;
  labels: Dictionary["sites"]["chart"];
};

function scoreY(score: number): number {
  return AREA.bottom - (score / 100) * (AREA.bottom - AREA.top);
}

export function TrendChart({ site, locale, labels }: TrendChartProps) {
  const checks = scoredChecks(site);
  const points = chartPoints(checks, AREA);
  const first = checks[0];
  const latest = checks.at(-1);

  if (!first || !latest) return <p className="text-slate-600">{labels.empty}</p>;

  const summary =
    checks.length === 1
      ? fill(labels.single, { score: latest.mobile_performance_score })
      : fill(labels.summary, {
          first: first.mobile_performance_score,
          latest: latest.mobile_performance_score,
          count: checks.length,
        });
  const labelEvery = Math.max(1, Math.ceil(points.length / 8));

  return (
    <figure className="flex flex-col gap-3">
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="h-auto w-full"
        role="img"
        aria-label={summary}
      >
        {GRID_SCORES.map((score) => (
          <g key={score}>
            <line
              x1={AREA.left}
              x2={AREA.right}
              y1={scoreY(score)}
              y2={scoreY(score)}
              className={score === 0 ? "stroke-slate-300" : "stroke-slate-100"}
            />
            <text
              x={AREA.left - 10}
              y={scoreY(score) + 4}
              textAnchor="end"
              className="fill-slate-600 text-xs"
            >
              {score}
            </text>
          </g>
        ))}
        {points.length > 1 ? (
          <polyline
            fill="none"
            className="stroke-accent"
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
            points={points.map(({ x, y }) => `${x},${y}`).join(" ")}
          />
        ) : null}
        {points.map((point, index) => (
          <g key={`${point.checkedAt}-${index}`}>
            <circle cx={point.x} cy={point.y} r="5" className="fill-white stroke-accent" strokeWidth="3" />
            {index === 0 || index === points.length - 1 ? (
              <text
                x={point.x}
                y={point.y - 14}
                textAnchor="middle"
                className={`font-heading text-base font-bold ${TONE_TEXT[scoreTone(point.score)]} fill-current`}
              >
                {point.score}
              </text>
            ) : null}
            {index % labelEvery === 0 || index === points.length - 1 ? (
              <text x={point.x} y={HEIGHT - 10} textAnchor="middle" className="fill-slate-600 text-xs">
                {formatCheckDate(point.checkedAt, locale)}
              </text>
            ) : null}
          </g>
        ))}
      </svg>
      <figcaption className="text-sm text-slate-600">{summary}</figcaption>
      <table className="sr-only">
        <caption>
          {labels.tableCaption}: {displayHost(site.url)}
        </caption>
        <thead>
          <tr>
            <th scope="col">{labels.date}</th>
            <th scope="col">{labels.score}</th>
          </tr>
        </thead>
        <tbody>
          {checks.map((check) => (
            <tr key={check.audit_id}>
              <td>{formatCheckDate(check.checked_at, locale)}</td>
              <td>{check.mobile_performance_score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
