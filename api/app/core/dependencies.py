from collections.abc import AsyncIterator
from typing import Annotated

from arq.connections import ArqRedis
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield session


def get_job_queue(request: Request) -> ArqRedis:
    job_queue: ArqRedis = request.app.state.job_queue
    return job_queue


DbSession = Annotated[AsyncSession, Depends(get_db_session)]
JobQueue = Annotated[ArqRedis, Depends(get_job_queue)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]
