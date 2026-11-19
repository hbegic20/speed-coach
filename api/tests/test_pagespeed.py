from collections.abc import Callable
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.models.audit import AuditFailureReason
from app.models.device_report import Device
from app.services.pagespeed import PAGESPEED_ENDPOINT, PageSpeedClient, PageSpeedError
from tests.pagespeed_payloads import lighthouse_payload

API_KEY = "test-api-key"

Handler = Callable[[httpx.Request], httpx.Response]


def client_for(handler: Handler) -> PageSpeedClient:
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return PageSpeedClient(http_client, SecretStr(API_KEY))


def respond_with(status_code: int, body: Any) -> Handler:
    return lambda _request: httpx.Response(status_code, json=body)


async def test_requests_a_performance_audit_for_the_device() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=lighthouse_payload())

    await client_for(handler).fetch_report("https://example.com/", Device.DESKTOP)

    [request] = requests
    assert str(request.url).startswith(PAGESPEED_ENDPOINT)
    assert dict(request.url.params) == {
        "url": "https://example.com/",
        "strategy": "desktop",
        "category": "performance",
    }
    assert request.headers["X-goog-api-key"] == API_KEY


async def test_builds_report_with_score_and_metrics() -> None:
    client = client_for(respond_with(200, lighthouse_payload(score=0.42)))

    report = await client.fetch_report("https://example.com/", Device.MOBILE)

    assert report.model_dump(exclude={"findings"}) == {
        "device": Device.MOBILE,
        "performance_score": 42,
        "first_contentful_paint_ms": 1800.5,
        "largest_contentful_paint_ms": 4200.0,
        "total_blocking_time_ms": 350.0,
        "cumulative_layout_shift": 0.12,
        "speed_index_ms": 3900.0,
    }


async def test_lists_failing_audits_ordered_by_time_savings() -> None:
    client = client_for(respond_with(200, lighthouse_payload()))

    report = await client.fetch_report("https://example.com/", Device.MOBILE)

    assert [finding.lighthouse_id for finding in report.findings] == [
        "render-blocking-resources",
        "unused-javascript",
        "uses-long-cache-ttl",
    ]


async def test_finding_carries_savings_and_display_text() -> None:
    client = client_for(respond_with(200, lighthouse_payload()))

    report = await client.fetch_report("https://example.com/", Device.MOBILE)

    unused_javascript = next(
        finding for finding in report.findings if finding.lighthouse_id == "unused-javascript"
    )
    assert unused_javascript.model_dump() == {
        "lighthouse_id": "unused-javascript",
        "title": "Title for unused-javascript",
        "description": "Description for unused-javascript",
        "score": 0.5,
        "display_value": "Est savings of 180 KiB",
        "savings_ms": 300,
        "savings_bytes": 184320,
    }


def error_body(status_code: int, message: str) -> dict[str, Any]:
    return {"error": {"code": status_code, "message": message}}


async def test_reports_site_unreachable_when_lighthouse_cannot_load_the_page() -> None:
    message = "Lighthouse returned error: FAILED_DOCUMENT_REQUEST. Lighthouse was unable to load."
    client = client_for(respond_with(400, error_body(400, message)))

    with pytest.raises(PageSpeedError) as raised:
        await client.fetch_report("https://example.com/", Device.MOBILE)

    assert raised.value.reason is AuditFailureReason.SITE_UNREACHABLE


@pytest.mark.parametrize(
    ("status_code", "body", "reason"),
    [
        (
            400,
            error_body(400, "API key not valid. Please pass a valid API key."),
            AuditFailureReason.PAGESPEED_UNAVAILABLE,
        ),
        (
            429,
            error_body(429, "Quota exceeded for quota metric 'Queries'"),
            AuditFailureReason.PAGESPEED_QUOTA_EXCEEDED,
        ),
        (403, error_body(403, "Requests are blocked."), AuditFailureReason.PAGESPEED_UNAVAILABLE),
        (500, error_body(500, "Internal error"), AuditFailureReason.PAGESPEED_UNAVAILABLE),
        (502, "<html>Bad Gateway</html>", AuditFailureReason.PAGESPEED_UNAVAILABLE),
    ],
)
async def test_maps_service_errors_to_failure_reasons(
    status_code: int, body: Any, reason: AuditFailureReason
) -> None:
    client = client_for(respond_with(status_code, body))

    with pytest.raises(PageSpeedError) as raised:
        await client.fetch_report("https://example.com/", Device.MOBILE)

    assert raised.value.reason is reason


async def test_reports_unavailable_when_request_times_out() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(PageSpeedError) as raised:
        await client_for(handler).fetch_report("https://example.com/", Device.MOBILE)

    assert raised.value.reason is AuditFailureReason.PAGESPEED_UNAVAILABLE


@pytest.mark.parametrize("body", [{"unexpected": True}, {"lighthouseResult": {"audits": []}}])
async def test_reports_unavailable_when_payload_is_malformed(body: dict[str, Any]) -> None:
    client = client_for(respond_with(200, body))

    with pytest.raises(PageSpeedError) as raised:
        await client.fetch_report("https://example.com/", Device.MOBILE)

    assert raised.value.reason is AuditFailureReason.PAGESPEED_UNAVAILABLE


@pytest.mark.parametrize(
    "payload",
    [
        lighthouse_payload(score=None),
        lighthouse_payload(runtime_error={"code": "NO_FCP", "message": "No paint"}),
    ],
)
async def test_reports_site_unreachable_when_lighthouse_cannot_measure(
    payload: dict[str, Any],
) -> None:
    client = client_for(respond_with(200, payload))

    with pytest.raises(PageSpeedError) as raised:
        await client.fetch_report("https://example.com/", Device.MOBILE)

    assert raised.value.reason is AuditFailureReason.SITE_UNREACHABLE
