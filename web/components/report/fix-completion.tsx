import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { FixStatus } from "@/lib/report/fix-status";

type FixCompletionProps = {
  status: FixStatus;
  toggle: () => Promise<void>;
  labels: Dictionary["report"]["fixes"]["completion"];
};

const STATUS_BADGE: Record<Exclude<FixStatus, "open">, string> = {
  done: "bg-good-soft text-good",
  stillDetected: "bg-needs-work-soft text-needs-work-strong",
};

export function FixCompletion({ status, toggle, labels }: FixCompletionProps) {
  return (
    <div className="flex flex-col items-start gap-2">
      {status === "open" ? null : (
        <p className={`rounded-full px-2.5 py-1 text-xs font-bold ${STATUS_BADGE[status]}`}>
          {labels[status]}
        </p>
      )}
      <form action={toggle}>
        <button
          type="submit"
          className="inline-flex min-h-11 items-center rounded-lg border border-slate-300 bg-white px-3.5 font-semibold text-ink hover:bg-slate-50"
        >
          {status === "open" ? labels.markDone : labels.undo}
        </button>
      </form>
    </div>
  );
}
