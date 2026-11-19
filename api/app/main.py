from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.db import create_engine, create_session_factory
from app.core.queue import create_job_queue
from app.routers import audits, health, sites


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_engine(settings)
    job_queue = await create_job_queue(settings)
    app.state.session_factory = create_session_factory(engine)
    app.state.job_queue = job_queue
    yield
    await job_queue.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="SpeedCoach API", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(audits.router)
    app.include_router(sites.router)
    return app


app = create_app()
