from datetime import UTC, datetime

from app.models.audit import Audit
from app.models.completed_fix import CompletedFix
from app.schemas.site import FixProgress


def as_utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def _recommended_ids(audit: Audit) -> set[str]:
    return {
        lighthouse_id
        for recommendation in audit.recommendations
        for lighthouse_id in recommendation.lighthouse_ids
    }


def _failing_ids(audit: Audit) -> set[str]:
    return {
        str(finding["lighthouse_id"]) for report in audit.reports for finding in report.findings
    }


def fix_progress(latest: Audit | None, completed_fixes: list[CompletedFix]) -> FixProgress:
    marked = {fix.lighthouse_id for fix in completed_fixes}
    if latest is None:
        return FixProgress(completed=len(marked), total=len(marked), confirmed=0)

    checked_at = as_utc(latest.created_at)
    failing = _failing_ids(latest)
    confirmed = {
        fix.lighthouse_id
        for fix in completed_fixes
        if fix.lighthouse_id not in failing and as_utc(fix.completed_at) < checked_at
    }
    return FixProgress(
        completed=len(marked),
        total=len(_recommended_ids(latest) | marked),
        confirmed=len(confirmed),
    )
