import secrets
import uuid

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.dependencies import get_job_queue
from app.models.device_report import Device
from app.services.audits import RUN_AUDIT_JOB, process_audit
from tests.fakes import RecordingQueue, UnavailableQueue, sample_report, stub_services

SessionFactory = async_sessionmaker[AsyncSession]
SITE = {"url": "https://example.com"}
MOBILE_SCORE = 41
DESKTOP_SCORE = 88


def owner_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {secrets.token_urlsafe(32)}"}


@pytest.fixture
def owner() -> dict[str, str]:
    return owner_headers()


async def completed_audit(client: AsyncClient, session_factory: SessionFactory) -> str:
    submitted = (
        await client.post("/audits", json={"url": "https://example.com", "language": "en"})
    ).json()
    reports = [
        sample_report(Device.MOBILE, MOBILE_SCORE),
        sample_report(Device.DESKTOP, DESKTOP_SCORE),
    ]
    async with session_factory() as session:
        await process_audit(session, uuid.UUID(submitted["id"]), stub_services(reports))
    return str(submitted["id"])


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer short"}, {"Authorization": "Basic dXNlcjpwYXNz"}],
)
async def test_sites_require_a_valid_owner_token(
    client: AsyncClient, headers: dict[str, str]
) -> None:
    response = await client.get("/sites", headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "owner_token_invalid"}


async def test_track_site_returns_an_empty_history(
    client: AsyncClient, owner: dict[str, str]
) -> None:
    response = await client.post("/sites", json=SITE, headers=owner)

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["url"] == "https://example.com/"
    assert body["latest_audit"] is None
    assert body["checks"] == []


async def test_track_site_rejects_private_urls(client: AsyncClient, owner: dict[str, str]) -> None:
    response = await client.post("/sites", json={"url": "http://10.0.0.1"}, headers=owner)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_tracking_the_same_url_twice_keeps_one_site(
    client: AsyncClient, owner: dict[str, str]
) -> None:
    first = (await client.post("/sites", json=SITE, headers=owner)).json()
    second = (
        await client.post("/sites", json={"url": "https://example.com/"}, headers=owner)
    ).json()

    assert second["id"] == first["id"]
    assert len((await client.get("/sites", headers=owner)).json()["sites"]) == 1


async def test_tracking_from_a_report_keeps_that_check(
    client: AsyncClient, session_factory: SessionFactory, owner: dict[str, str]
) -> None:
    audit_id = await completed_audit(client, session_factory)

    body = (await client.post("/sites", json={**SITE, "audit_id": audit_id}, headers=owner)).json()

    assert body["latest_audit"] == {"audit_id": audit_id, "status": "completed"}
    [check] = body["checks"]
    assert check["audit_id"] == audit_id
    assert check["platform"] == "wordpress"
    assert check["mobile_performance_score"] == MOBILE_SCORE
    assert check["desktop_performance_score"] == DESKTOP_SCORE


async def test_owners_only_see_their_own_sites(client: AsyncClient, owner: dict[str, str]) -> None:
    site = (await client.post("/sites", json=SITE, headers=owner)).json()
    stranger = owner_headers()

    assert (await client.get("/sites", headers=stranger)).json()["sites"] == []
    response = await client.get(f"/sites/{site['id']}", headers=stranger)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "site_not_found"}
    deleted = await client.delete(f"/sites/{site['id']}", headers=stranger)
    assert deleted.status_code == status.HTTP_404_NOT_FOUND


async def test_recheck_queues_a_tracked_audit(
    client: AsyncClient, owner: dict[str, str], job_queue: RecordingQueue
) -> None:
    site = (await client.post("/sites", json=SITE, headers=owner)).json()

    response = await client.post(
        f"/sites/{site['id']}/audits", json={"language": "bs"}, headers=owner
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    audit = response.json()
    assert audit["url"] == "https://example.com/"
    assert audit["language"] == "bs"
    assert job_queue.jobs == [(RUN_AUDIT_JOB, (audit["id"],))]
    refreshed = (await client.get(f"/sites/{site['id']}", headers=owner)).json()
    assert refreshed["latest_audit"] == {"audit_id": audit["id"], "status": "queued"}


async def test_recheck_requires_a_supported_language(
    client: AsyncClient, owner: dict[str, str]
) -> None:
    site = (await client.post("/sites", json=SITE, headers=owner)).json()

    response = await client.post(
        f"/sites/{site['id']}/audits", json={"language": "de"}, headers=owner
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_recheck_returns_503_when_queue_is_unavailable(
    app: FastAPI, client: AsyncClient, owner: dict[str, str]
) -> None:
    site = (await client.post("/sites", json=SITE, headers=owner)).json()
    app.dependency_overrides[get_job_queue] = UnavailableQueue

    response = await client.post(
        f"/sites/{site['id']}/audits", json={"language": "en"}, headers=owner
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "audit_queue_unavailable"}


async def test_untracking_keeps_the_reports(
    client: AsyncClient, session_factory: SessionFactory, owner: dict[str, str]
) -> None:
    audit_id = await completed_audit(client, session_factory)
    site = (await client.post("/sites", json={**SITE, "audit_id": audit_id}, headers=owner)).json()

    response = await client.delete(f"/sites/{site['id']}", headers=owner)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert (await client.get("/sites", headers=owner)).json()["sites"] == []
    assert (await client.get(f"/audits/{audit_id}")).status_code == status.HTTP_200_OK


async def test_list_reports_the_site_limit(
    client: AsyncClient, owner: dict[str, str], settings: Settings
) -> None:
    body = (await client.get("/sites", headers=owner)).json()

    assert body == {"sites": [], "site_limit": settings.max_sites_per_owner}


async def test_owners_can_track_up_to_the_site_limit(
    client: AsyncClient, owner: dict[str, str], settings: Settings
) -> None:
    for index in range(settings.max_sites_per_owner):
        response = await client.post(
            "/sites", json={"url": f"https://site-{index}.example.com"}, headers=owner
        )
        assert response.status_code == status.HTTP_201_CREATED

    blocked = await client.post(
        "/sites", json={"url": "https://one-more.example.com"}, headers=owner
    )

    assert blocked.status_code == status.HTTP_409_CONFLICT
    assert blocked.json() == {"detail": "site_limit_reached"}
    assert len((await client.get("/sites", headers=owner)).json()["sites"]) == (
        settings.max_sites_per_owner
    )


async def test_re_tracking_a_site_at_the_limit_still_works(
    client: AsyncClient, session_factory: SessionFactory, settings: Settings
) -> None:
    owner = owner_headers()
    for index in range(settings.max_sites_per_owner - 1):
        await client.post(
            "/sites", json={"url": f"https://site-{index}.example.com"}, headers=owner
        )
    await client.post("/sites", json=SITE, headers=owner)
    audit_id = await completed_audit(client, session_factory)

    response = await client.post("/sites", json={**SITE, "audit_id": audit_id}, headers=owner)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["latest_audit"]["audit_id"] == audit_id


async def test_site_limit_is_per_owner(client: AsyncClient, settings: Settings) -> None:
    owner = owner_headers()
    for index in range(settings.max_sites_per_owner):
        await client.post(
            "/sites", json={"url": f"https://site-{index}.example.com"}, headers=owner
        )

    response = await client.post("/sites", json=SITE, headers=owner_headers())

    assert response.status_code == status.HTTP_201_CREATED


async def test_marking_fixes_done_and_undoing_them(
    client: AsyncClient, session_factory: SessionFactory, owner: dict[str, str]
) -> None:
    audit_id = await completed_audit(client, session_factory)
    site = (await client.post("/sites", json={**SITE, "audit_id": audit_id}, headers=owner)).json()
    assert site["fix_progress"] == {"completed": 0, "total": 2, "confirmed": 0}
    path = f"/sites/{site['id']}/completed-fixes"

    marked = await client.put(
        path,
        json={"lighthouse_ids": ["render-blocking-resources"], "completed": True},
        headers=owner,
    )
    again = await client.put(
        path,
        json={"lighthouse_ids": ["render-blocking-resources"], "completed": True},
        headers=owner,
    )

    assert marked.status_code == status.HTTP_204_NO_CONTENT
    assert again.status_code == status.HTTP_204_NO_CONTENT
    body = (await client.get(f"/sites/{site['id']}", headers=owner)).json()
    assert [fix["lighthouse_id"] for fix in body["completed_fixes"]] == [
        "render-blocking-resources"
    ]
    assert body["fix_progress"] == {"completed": 1, "total": 2, "confirmed": 0}

    await client.put(
        path,
        json={"lighthouse_ids": ["render-blocking-resources"], "completed": False},
        headers=owner,
    )
    body = (await client.get(f"/sites/{site['id']}", headers=owner)).json()
    assert body["completed_fixes"] == []


@pytest.mark.parametrize(
    "payload",
    [
        {"lighthouse_ids": [], "completed": True},
        {"lighthouse_ids": ["Not A Valid Id!"], "completed": True},
        {"lighthouse_ids": ["unused-css"]},
        {"lighthouse_ids": [f"audit-{index}" for index in range(21)], "completed": True},
    ],
)
async def test_completed_fixes_validate_the_request(
    client: AsyncClient, owner: dict[str, str], payload: dict[str, object]
) -> None:
    site = (await client.post("/sites", json=SITE, headers=owner)).json()

    response = await client.put(f"/sites/{site['id']}/completed-fixes", json=payload, headers=owner)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_only_the_owner_can_mark_fixes(client: AsyncClient, owner: dict[str, str]) -> None:
    site = (await client.post("/sites", json=SITE, headers=owner)).json()

    response = await client.put(
        f"/sites/{site['id']}/completed-fixes",
        json={"lighthouse_ids": ["unused-css"], "completed": True},
        headers=owner_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_audits_report_the_site_they_belong_to(
    client: AsyncClient, session_factory: SessionFactory, owner: dict[str, str]
) -> None:
    audit_id = await completed_audit(client, session_factory)
    assert (await client.get(f"/audits/{audit_id}")).json()["tracked_site_id"] is None

    site = (await client.post("/sites", json={**SITE, "audit_id": audit_id}, headers=owner)).json()

    assert (await client.get(f"/audits/{audit_id}")).json()["tracked_site_id"] == site["id"]
