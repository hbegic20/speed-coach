import secrets

from fastapi import status
from httpx import AsyncClient

from app.core.client_identity import CLIENT_IP_HEADER, PROXY_SECRET_HEADER
from app.core.config import Settings
from tests.conftest import TEST_PROXY_SECRET

AUDIT = {"url": "https://example.com", "language": "en"}


def visitor(ip: str) -> dict[str, str]:
    return {CLIENT_IP_HEADER: ip, PROXY_SECRET_HEADER: TEST_PROXY_SECRET}


async def test_audit_creation_is_limited_per_visitor(
    client: AsyncClient, settings: Settings
) -> None:
    for _ in range(settings.audit_burst_limit):
        response = await client.post("/audits", json=AUDIT, headers=visitor("203.0.113.7"))
        assert response.status_code == status.HTTP_202_ACCEPTED

    blocked = await client.post("/audits", json=AUDIT, headers=visitor("203.0.113.7"))

    assert blocked.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert blocked.json() == {"detail": "rate_limited"}
    assert blocked.headers["Retry-After"] == str(settings.audit_burst_window_seconds)
    other_visitor = await client.post("/audits", json=AUDIT, headers=visitor("198.51.100.4"))
    assert other_visitor.status_code == status.HTTP_202_ACCEPTED


async def test_rechecks_share_the_audit_limit(client: AsyncClient, settings: Settings) -> None:
    owner = {"Authorization": f"Bearer {secrets.token_urlsafe(32)}", **visitor("203.0.113.9")}
    site = (await client.post("/sites", json={"url": "https://example.com"}, headers=owner)).json()
    for _ in range(settings.audit_burst_limit):
        await client.post("/audits", json=AUDIT, headers=visitor("203.0.113.9"))

    response = await client.post(
        f"/sites/{site['id']}/audits", json={"language": "en"}, headers=owner
    )

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def new_owner(ip: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {secrets.token_urlsafe(32)}", **visitor(ip)}


async def test_site_tracking_is_limited_per_visitor(
    client: AsyncClient, settings: Settings
) -> None:
    for index in range(settings.site_hourly_limit):
        response = await client.post(
            "/sites",
            json={"url": f"https://site-{index}.example.com"},
            headers=new_owner("203.0.113.11"),
        )
        assert response.status_code == status.HTTP_201_CREATED

    blocked = await client.post(
        "/sites", json={"url": "https://one-more.example.com"}, headers=new_owner("203.0.113.11")
    )

    assert blocked.status_code == status.HTTP_429_TOO_MANY_REQUESTS
