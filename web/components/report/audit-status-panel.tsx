import type { Audit, FailureReason } from "@/lib/api/schemas";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { AutoRefresh } from "./auto-refresh";

const REFRESH_INTERVAL_MS = 3000;

type ProgressPanelProps = {
  status: Extract<Audit["status"], "queued" | "running">;
  labels: Dictionary["report"]["progress"];
};

export function ProgressPanel({ status, labels }: ProgressPanelProps) {
  return (
    <section
      aria-labelledby="progress-heading"
      className="flex flex-col items-start gap-4 rounded-2xl border border-slate-200 bg-white p-6 sm:flex-row sm:items-center"
    >
      <span
        aria-hidden="true"
        className="size-10 flex-none animate-spin rounded-full border-4 border-blue-100 border-t-accent motion-reduce:animate-none"
      />
      <div className="flex flex-col gap-1.5">
        <h2 id="progress-heading" className="font-heading text-[22px] font-bold">
          {labels.heading}
        </h2>
        <p role="status" className="font-semibold text-accent">
          {labels[status]}
        </p>
        <p className="max-w-2xl text-slate-600">{labels.body}</p>
      </div>
      <AutoRefresh intervalMs={REFRESH_INTERVAL_MS} />
    </section>
  );
}

type FailurePanelProps = {
  reason: FailureReason | null;
  labels: Dictionary["report"]["failures"];
};

export function FailurePanel({ reason, labels }: FailurePanelProps) {
  return (
    <section
      role="alert"
      aria-labelledby="failure-heading"
      className="flex flex-col gap-2 rounded-2xl border border-poor-soft bg-white p-6"
    >
      <h2 id="failure-heading" className="font-heading text-[22px] font-bold text-poor">
        {labels.heading}
      </h2>
      <p className="text-slate-700">{labels[reason ?? "internal_error"]}</p>
    </section>
  );
}
