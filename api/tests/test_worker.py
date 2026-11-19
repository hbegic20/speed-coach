import importlib
from collections.abc import Iterator
from datetime import datetime
from types import ModuleType

import pytest
from arq.cron import next_cron

from app.core.config import get_settings
from app.jobs import run_scheduled_checks


@pytest.fixture
def worker_module(monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@localhost/speedcoach")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("PAGESPEED_API_KEY", "test-pagespeed-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    get_settings.cache_clear()
    module = importlib.import_module("app.worker")
    yield module
    get_settings.cache_clear()


def test_weekly_job_points_at_the_scheduled_checks_function(worker_module: ModuleType) -> None:
    [job] = worker_module.WorkerSettings.cron_jobs

    assert job.coroutine is run_scheduled_checks
    assert job.unique is True


def test_weekly_job_runs_on_monday_morning_in_sarajevo(worker_module: ModuleType) -> None:
    settings = worker_module.WorkerSettings
    [job] = settings.cron_jobs
    thursday = datetime(2026, 11, 19, 14, 30, tzinfo=settings.timezone)

    next_run = next_cron(
        thursday,
        weekday=job.weekday,
        hour=job.hour,
        minute=job.minute,
        second=job.second,
        microsecond=job.microsecond,
    )

    assert (next_run.year, next_run.month, next_run.day) == (2026, 11, 23)
    assert next_run.strftime("%A %H:%M") == "Monday 06:00"
    assert next_run.tzname() == "CET"
