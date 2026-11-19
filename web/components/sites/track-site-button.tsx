import { trackAuditedSite } from "@/app/[lang]/sites/actions";
import type { Locale } from "@/lib/i18n/locales";

type TrackSiteButtonProps = {
  locale: Locale;
  auditId: string;
  url: string;
  label: string;
};

export function TrackSiteButton({ locale, auditId, url, label }: TrackSiteButtonProps) {
  return (
    <form action={trackAuditedSite.bind(null, locale, auditId, url)}>
      <button
        type="submit"
        className="inline-flex min-h-11 items-center rounded-[10px] bg-ink px-4 font-semibold text-white hover:bg-slate-800"
      >
        {label}
      </button>
    </form>
  );
}
