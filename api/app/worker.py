from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import get_settings
from app.core.db import create_engine, create_session_factory
from app.core.queue import create_redis_settings
from app.jobs import run_audit


async def startup(context: dict[str, Any]) -> None:
    settings = get_settings()
    engine = create_engine(settings)
    context["settings"] = settings
    context["engine"] = engine
    context["session_factory"] = create_session_factory(engine)
    context["http_client"] = httpx.AsyncClient(timeout=settings.pagespeed_timeout_seconds)


async def shutdown(context: dict[str, Any]) -> None:
    engine: AsyncEngine = context["engine"]
    http_client: httpx.AsyncClient = context["http_client"]
    await http_client.aclose()
    await engine.dispose()


class WorkerSettings:
    functions = (run_audit,)
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = create_redis_settings(get_settings())
