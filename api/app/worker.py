from typing import Any
from zoneinfo import ZoneInfo

import httpx
from arq import cron
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import get_settings
from app.core.db import create_engine, create_session_factory
from app.core.queue import create_redis_settings
from app.jobs import run_audit
from app.services.page_fetch import PageFetcher


async def startup(context: dict[str, Any]) -> None:
    settings = get_settings()
    engine = create_engine(settings)
    context["settings"] = settings
    context["engine"] = engine
    context["session_factory"] = create_session_factory(engine)
    context["http_client"] = httpx.AsyncClient(timeout=settings.pagespeed_timeout_seconds)
    context["page_fetcher"] = PageFetcher(timeout_seconds=settings.page_fetch_timeout_seconds)


async def shutdown(context: dict[str, Any]) -> None:
    engine: AsyncEngine = context["engine"]
    http_client: httpx.AsyncClient = context["http_client"]
    await http_client.aclose()
    await engine.dispose()


SCHEDULED_CHECKS_JOB = "app.jobs.run_scheduled_checks"
SCHEDULE_TIMEZONE = ZoneInfo("Europe/Sarajevo")
WEEKLY_CHECK_HOUR = 6


class WorkerSettings:
    functions = (run_audit,)
    cron_jobs = (
        cron(SCHEDULED_CHECKS_JOB, weekday="mon", hour=WEEKLY_CHECK_HOUR, minute=0, unique=True),
    )
    timezone = SCHEDULE_TIMEZONE
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = create_redis_settings(get_settings())
