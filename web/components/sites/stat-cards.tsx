import type { ReactNode } from "react";
import type { Site } from "@/lib/api/schemas";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { averageChange, averageLatestScore } from "@/lib/report/site-history";
import { ChangeIndicator } from "./change-indicator";

type StatCardsProps = {
  sites: Site[];
  labels: Dictionary["sites"];
};

type StatCardProps = {
  label: string;
  value: string;
  note: ReactNode;
};

function StatCard({ label, value, note }: StatCardProps) {
  return (
    <div className="flex flex-col gap-1.5 rounded-[14px] border border-slate-200 bg-white p-4.5">
      <dt className="text-[13px] font-semibold text-slate-600">{label}</dt>
      <dd className="font-heading text-[32px] font-bold">{value}</dd>
      <dd className="text-[13px] text-slate-600">{note}</dd>
    </div>
  );
}

function SinceFirstCheck({ change, labels }: { change: number; labels: Dictionary["sites"] }) {
  const [before = "", after = ""] = labels.stats.sinceFirst.split("{change}");
  return (
    <>
      {before}
      <ChangeIndicator change={change} labels={labels.change} />
      {after}
    </>
  );
}

export function StatCards({ sites, labels }: StatCardsProps) {
  const averageScore = averageLatestScore(sites);
  const change = averageChange(sites);

  return (
    <dl className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
      <StatCard
        label={labels.stats.averageScore}
        value={averageScore === null ? "–" : String(averageScore)}
        note={
          change === null ? labels.change.none : <SinceFirstCheck change={change} labels={labels} />
        }
      />
      <StatCard
        label={labels.stats.sitesTracked}
        value={String(sites.length)}
        note={labels.stats.sitesTrackedNote}
      />
    </dl>
  );
}
