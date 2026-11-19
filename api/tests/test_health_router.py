from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

from fastapi import FastAPI, status
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session


async def test_health_returns_ok_when_database_is_reachable(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


async def test_health_returns_503_when_database_is_unreachable(
    app: FastAPI, client: AsyncClient
) -> None:
    failing_session = AsyncMock(spec=AsyncSession)
    failing_session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("down"))

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield failing_session

    app.dependency_overrides[get_db_session] = override_db_session

    response = await client.get("/health")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"status": "unavailable"}
