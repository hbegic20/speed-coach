import uuid
from datetime import UTC, datetime, timedelta

from app.models.audit import Audit, AuditStatus, Language
from app.models.completed_fix import CompletedFix
from app.models.device_report import Device, DeviceReport
from app.models.recommendation import Effort, Impact, Recommendation
from app.services.fix_progress import fix_progress
from tests.fakes import sample_report

CHECKED_AT = datetime(2026, 11, 23, 6, 0, tzinfo=UTC)


def latest_check(recommended: list[list[str]], failing: list[str]) -> Audit:
    report = sample_report(Device.MOBILE).model_dump()
    template = report["findings"][0]
    report["findings"] = [{**template, "lighthouse_id": lighthouse_id} for lighthouse_id in failing]
    audit = Audit(
        id=uuid.uuid4(),
        url="https://example.com/",
        language=Language.ENGLISH,
        status=AuditStatus.COMPLETED,
        created_at=CHECKED_AT,
    )
    audit.reports = [DeviceReport(**report)]
    audit.recommendations = [
        Recommendation(
            rank=rank,
            title="Fix",
            explanation="Why",
            steps=["Step"],
            impact=Impact.HIGH,
            effort=Effort.LOW,
            devices=["mobile"],
            lighthouse_ids=lighthouse_ids,
        )
        for rank, lighthouse_ids in enumerate(recommended, start=1)
    ]
    return audit


def marked(lighthouse_id: str, *, hours_before_check: float) -> CompletedFix:
    return CompletedFix(
        lighthouse_id=lighthouse_id,
        completed_at=CHECKED_AT - timedelta(hours=hours_before_check),
    )


def test_counts_every_recommended_problem_and_every_mark() -> None:
    latest = latest_check(
        recommended=[["render-blocking-resources", "unused-css"], ["uses-long-cache-ttl"]],
        failing=["render-blocking-resources", "unused-css", "uses-long-cache-ttl"],
    )

    progress = fix_progress(latest, [marked("unused-css", hours_before_check=-1)])

    assert (progress.completed, progress.total, progress.confirmed) == (1, 3, 0)


def test_confirms_marks_that_a_later_check_no_longer_finds() -> None:
    latest = latest_check(recommended=[["uses-long-cache-ttl"]], failing=["uses-long-cache-ttl"])

    progress = fix_progress(latest, [marked("render-blocking-resources", hours_before_check=48)])

    assert (progress.completed, progress.total, progress.confirmed) == (1, 2, 1)


def test_does_not_confirm_problems_the_latest_check_still_finds() -> None:
    latest = latest_check(
        recommended=[["render-blocking-resources"]], failing=["render-blocking-resources"]
    )

    progress = fix_progress(latest, [marked("render-blocking-resources", hours_before_check=48)])

    assert progress.confirmed == 0


def test_does_not_confirm_marks_made_after_the_latest_check() -> None:
    latest = latest_check(recommended=[], failing=[])

    progress = fix_progress(latest, [marked("render-blocking-resources", hours_before_check=-2)])

    assert progress.confirmed == 0


def test_handles_timestamps_without_a_timezone() -> None:
    latest = latest_check(recommended=[], failing=[])
    naive_mark = CompletedFix(
        lighthouse_id="unused-css",
        completed_at=(CHECKED_AT - timedelta(days=1)).replace(tzinfo=None),
    )

    assert fix_progress(latest, [naive_mark]).confirmed == 1


def test_counts_only_marks_without_a_finished_check() -> None:
    progress = fix_progress(None, [marked("unused-css", hours_before_check=1)])

    assert (progress.completed, progress.total, progress.confirmed) == (1, 1, 0)
