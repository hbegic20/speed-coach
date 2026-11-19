from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.health import database_is_reachable


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


async def test_reports_reachable_when_query_succeeds(mock_session: AsyncMock) -> None:
    assert await database_is_reachable(mock_session) is True


async def test_reports_unreachable_when_database_errors(mock_session: AsyncMock) -> None:
    mock_session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("down"))

    assert await database_is_reachable(mock_session) is False


async def test_reports_unreachable_when_connection_is_refused(mock_session: AsyncMock) -> None:
    mock_session.execute.side_effect = ConnectionRefusedError()

    assert await database_is_reachable(mock_session) is False
