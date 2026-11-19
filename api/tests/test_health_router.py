from unittest.mock import AsyncMock

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError


def test_health_returns_ok_when_database_is_reachable(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


def test_health_returns_503_when_database_is_unreachable(
    client: TestClient, db_session: AsyncMock
) -> None:
    db_session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("down"))

    response = client.get("/health")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"status": "unavailable"}
