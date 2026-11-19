import type { Dictionary } from "@/lib/i18n/dictionaries";

type SiteFooterProps = {
  dictionary: Dictionary;
};

export function SiteFooter({ dictionary }: SiteFooterProps) {
  return (
    <footer className="border-t border-slate-200 px-4 py-6 text-center text-sm text-slate-600 sm:px-8">
      {dictionary.footer.builtBy} ·{" "}
      <a
        href="https://github.com/hbegic20"
        className="inline-flex min-h-11 items-center text-accent underline-offset-2 hover:underline"
      >
        GitHub
      </a>
    </footer>
  );
}
