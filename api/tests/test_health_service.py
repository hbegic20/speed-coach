from unittest.mock import AsyncMock

from sqlalchemy.exc import OperationalError

from app.services.health import database_is_reachable


async def test_reports_reachable_when_query_succeeds(db_session: AsyncMock) -> None:
    assert await database_is_reachable(db_session) is True


async def test_reports_unreachable_when_database_errors(db_session: AsyncMock) -> None:
    db_session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("down"))

    assert await database_is_reachable(db_session) is False


async def test_reports_unreachable_when_connection_is_refused(db_session: AsyncMock) -> None:
    db_session.execute.side_effect = ConnectionRefusedError()

    assert await database_is_reachable(db_session) is False
