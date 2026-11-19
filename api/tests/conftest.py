from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.dependencies import get_db_session, get_job_queue
from app.core.rate_limits import get_rate_limiter
from app.main import create_app
from app.models import Base
from app.services.rate_limit import RateLimiter
from tests.fakes import InMemoryCounterStore, RecordingQueue

SessionFactory = async_sessionmaker[AsyncSession]


@pytest.fixture
async def session_factory() -> AsyncIterator[SessionFactory]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def session(session_factory: SessionFactory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest.fixture
def job_queue() -> RecordingQueue:
    return RecordingQueue()


TEST_PROXY_SECRET = "test-proxy-secret"


@pytest.fixture
def settings() -> Settings:
    return Settings.model_validate(
        {
            "database_url": "postgresql+asyncpg://user:password@localhost/speedcoach",
            "redis_url": "redis://localhost:6379/0",
            "pagespeed_api_key": "test-pagespeed-key",
            "gemini_api_key": "test-gemini-key",
            "web_proxy_secret": TEST_PROXY_SECRET,
        }
    )


@pytest.fixture
def counter_store() -> InMemoryCounterStore:
    return InMemoryCounterStore()


@pytest.fixture
def app(
    session_factory: SessionFactory,
    job_queue: RecordingQueue,
    settings: Settings,
    counter_store: InMemoryCounterStore,
) -> FastAPI:
    app = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_job_queue] = lambda: job_queue
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_rate_limiter] = lambda: RateLimiter(counter_store)
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
