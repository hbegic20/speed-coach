from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import get_settings
from app.core.db import create_engine, create_session_factory
from app.core.queue import create_redis_settings
from app.jobs import run_audit


async def startup(context: dict[str, Any]) -> None:
    engine = create_engine(get_settings())
    context["engine"] = engine
    context["session_factory"] = create_session_factory(engine)


async def shutdown(context: dict[str, Any]) -> None:
    engine: AsyncEngine = context["engine"]
    await engine.dispose()


class WorkerSettings:
    functions = (run_audit,)
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = create_redis_settings(get_settings())
