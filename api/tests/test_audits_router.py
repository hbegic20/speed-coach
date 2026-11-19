import uuid

from fastapi import FastAPI, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.dependencies import get_job_queue
from app.models.device_report import Device
from app.services.audits import RUN_AUDIT_JOB, process_audit
from tests.fakes import RecordingQueue, UnavailableQueue, sample_report, stub_services
from tests.gemini_payloads import sample_recommendation_set

EXAMPLE_AUDIT = {"url": "https://example.com", "language": "bs"}


async def test_submit_audit_queues_the_url(client: AsyncClient, job_queue: RecordingQueue) -> None:
    response = await client.post("/audits", json=EXAMPLE_AUDIT)

    assert response.status_code == status.HTTP_202_ACCEPTED
    body = response.json()
    assert body["url"] == "https://example.com/"
    assert body["language"] == "bs"
    assert body["status"] == "queued"
    assert body["failure_reason"] is None
    assert body["reports"] == []
    assert body["platform"] is None
    assert body["summary"] is None
    assert body["recommendations"] == []
    assert job_queue.jobs == [(RUN_AUDIT_JOB, (body["id"],))]


async def test_submit_audit_rejects_private_urls(
    client: AsyncClient, job_queue: RecordingQueue
) -> None:
    response = await client.post("/audits", json={"url": "http://192.168.1.1", "language": "en"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert job_queue.jobs == []


async def test_submit_audit_rejects_unsupported_languages(client: AsyncClient) -> None:
    response = await client.post("/audits", json={"url": "https://example.com", "language": "de"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_submit_audit_requires_a_url(client: AsyncClient) -> None:
    response = await client.post("/audits", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_submit_audit_returns_503_when_queue_is_unavailable(
    app: FastAPI, client: AsyncClient
) -> None:
    app.dependency_overrides[get_job_queue] = UnavailableQueue

    response = await client.post("/audits", json=EXAMPLE_AUDIT)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "audit_queue_unavailable"}


async def test_read_audit_returns_the_submitted_audit(client: AsyncClient) -> None:
    submitted = (await client.post("/audits", json=EXAMPLE_AUDIT)).json()

    response = await client.get(f"/audits/{submitted['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == submitted


async def test_read_audit_returns_404_for_unknown_id(client: AsyncClient) -> None:
    response = await client.get(f"/audits/{uuid.uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "audit_not_found"}


async def test_read_audit_rejects_malformed_id(client: AsyncClient) -> None:
    response = await client.get("/audits/not-a-uuid")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_read_audit_includes_reports_and_recommendations(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    submitted = (await client.post("/audits", json=EXAMPLE_AUDIT)).json()
    reports = [sample_report(Device.MOBILE, 41), sample_report(Device.DESKTOP, 88)]
    async with session_factory() as session:
        await process_audit(session, uuid.UUID(submitted["id"]), stub_services(reports))

    response = await client.get(f"/audits/{submitted['id']}")

    body = response.json()
    expected = sample_recommendation_set()
    assert body["status"] == "completed"
    assert body["platform"] == "wordpress"
    assert body["summary"] == expected.summary
    assert body["reports"] == [report.model_dump(mode="json") for report in reports]
    assert [item["rank"] for item in body["recommendations"]] == [1, 2]
    assert body["recommendations"][0] == {
        "rank": 1,
        **expected.recommendations[0].model_dump(mode="json"),
    }
