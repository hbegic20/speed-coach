import type { Site } from "@/lib/api/schemas";
import { displayHost } from "@/lib/report/format";

type SitePickerProps = {
  sites: Site[];
  selectedId: string;
  action: string;
  label: string;
  submitLabel: string;
};

export function SitePicker({ sites, selectedId, action, label, submitLabel }: SitePickerProps) {
  return (
    <form method="get" action={action} className="flex flex-wrap items-center gap-2">
      <label htmlFor="site-picker" className="text-sm font-semibold">
        {label}
      </label>
      <select
        id="site-picker"
        name="site"
        defaultValue={selectedId}
        className="h-11 rounded-lg border border-slate-300 bg-white px-2.5 text-sm"
      >
        {sites.map((site) => (
          <option key={site.id} value={site.id}>
            {displayHost(site.url)}
          </option>
        ))}
      </select>
      <button
        type="submit"
        className="h-11 rounded-lg border border-slate-300 bg-white px-3.5 text-sm font-semibold hover:bg-slate-50"
      >
        {submitLabel}
      </button>
    </form>
  );
}
