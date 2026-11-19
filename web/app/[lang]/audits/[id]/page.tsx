import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { z } from "zod";
import { ReportView } from "@/components/report/report-view";
import { getAudit } from "@/lib/api/audits";
import type { Audit } from "@/lib/api/schemas";
import { getSite } from "@/lib/api/sites";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { resolveLocale } from "@/lib/i18n/resolve-locale";
import { readOwnerToken } from "@/lib/owner/token";
import { parseDevice } from "@/lib/report/audit-view";
import type { FixTracking } from "@/lib/report/fix-status";
import { submitAudit } from "../../actions";

const auditIdSchema = z.uuid();

type AuditPageProps = PageProps<"/[lang]/audits/[id]">;

export async function generateMetadata({ params }: AuditPageProps): Promise<Metadata> {
  const { metadata } = getDictionary(await resolveLocale(params));
  return { title: `${metadata.reportTitle} · ${metadata.title}`, robots: { index: false } };
}

async function loadFixTracking(audit: Audit): Promise<FixTracking | null> {
  if (!audit.tracked_site_id) return null;
  const token = await readOwnerToken();
  if (!token) return null;
  const site = await getSite({ token, clientIp: null }, audit.tracked_site_id);
  return site ? { siteId: site.id, completedFixes: site.completed_fixes } : null;
}

async function AuditReport({ params, searchParams }: AuditPageProps) {
  const locale = await resolveLocale(params);
  const { id } = await params;
  if (!auditIdSchema.safeParse(id).success) notFound();

  const [audit, query] = await Promise.all([getAudit(id), searchParams]);
  if (audit === null) notFound();
  const fixTracking = await loadFixTracking(audit);

  return (
    <ReportView
      audit={audit}
      device={parseDevice(query.device)}
      locale={locale}
      dictionary={getDictionary(locale)}
      rerunAction={submitAudit.bind(null, locale)}
      fixTracking={fixTracking}
    />
  );
}

function ReportSkeleton() {
  return (
    <div aria-busy="true" className="mx-auto flex w-full max-w-6xl flex-col gap-7 px-4 pt-2 sm:px-8">
      <div className="h-11 max-w-xl rounded-[10px] bg-slate-200" />
      <div className="h-12 w-2/3 rounded-lg bg-slate-200" />
      <div className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4">
        {[0, 1, 2, 3].map((index) => (
          <div key={index} className="h-32 rounded-2xl bg-slate-200" />
        ))}
      </div>
    </div>
  );
}

export default function AuditPage(props: AuditPageProps) {
  return (
    <main className="flex-1">
      <Suspense fallback={<ReportSkeleton />}>
        <AuditReport {...props} />
      </Suspense>
    </main>
  );
}
