import type { Dictionary } from "@/lib/i18n/dictionaries";
import { fill } from "@/lib/i18n/fill";

type ChangeIndicatorProps = {
  change: number | null;
  labels: Dictionary["sites"]["change"];
};

export function ChangeIndicator({ change, labels }: ChangeIndicatorProps) {
  if (change === null) return <span className="text-slate-600">{labels.none}</span>;
  if (change === 0) return <span className="font-semibold text-slate-700">{labels.flat}</span>;

  const rising = change > 0;
  const points = Math.abs(change);
  return (
    <span className={`font-semibold ${rising ? "text-good" : "text-poor"}`}>
      <span aria-hidden="true">
        {rising ? "▲" : "▼"} {points}
      </span>
      <span className="sr-only">{fill(rising ? labels.up : labels.down, { points })}</span>
    </span>
  );
}
