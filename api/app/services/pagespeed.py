import logging

import httpx
from pydantic import SecretStr, ValidationError

from app.models.audit import AuditFailureReason
from app.models.device_report import Device
from app.schemas.pagespeed_api import (
    LighthouseAudit,
    LighthouseResult,
    PageSpeedErrorResponse,
    PageSpeedResponse,
)
from app.schemas.report import DeviceReportData, Finding

logger = logging.getLogger(__name__)

PAGESPEED_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
LIGHTHOUSE_PAGE_ERROR_PREFIX = "Lighthouse returned error"
PASSING_SCORE = 0.9
MEASURED_SCORE_MODES = frozenset({"numeric", "binary", "metricSavings"})
TIME_SAVINGS_METRICS = ("LCP", "FCP", "TBT", "INP")
METRIC_AUDIT_IDS = frozenset(
    {
        "first-contentful-paint",
        "largest-contentful-paint",
        "total-blocking-time",
        "cumulative-layout-shift",
        "speed-index",
        "interactive",
        "max-potential-fid",
    }
)


class PageSpeedError(Exception):
    def __init__(self, reason: AuditFailureReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


class PageSpeedClient:
    def __init__(self, http_client: httpx.AsyncClient, api_key: SecretStr) -> None:
        self._http_client = http_client
        self._api_key = api_key

    async def fetch_report(self, url: str, device: Device) -> DeviceReportData:
        response = await self._request(url, device)
        _raise_for_status(response)
        try:
            payload = PageSpeedResponse.model_validate_json(response.content)
        except ValidationError as error:
            logger.exception("PageSpeed returned an unexpected payload for %s", device)
            raise PageSpeedError(AuditFailureReason.PAGESPEED_UNAVAILABLE) from error
        return build_device_report(payload.lighthouse_result, device)

    async def _request(self, url: str, device: Device) -> httpx.Response:
        try:
            return await self._http_client.get(
                PAGESPEED_ENDPOINT,
                params={"url": url, "strategy": device.value, "category": "performance"},
                headers={"X-goog-api-key": self._api_key.get_secret_value()},
            )
        except httpx.HTTPError as error:
            logger.warning("PageSpeed request failed for %s", device, exc_info=True)
            raise PageSpeedError(AuditFailureReason.PAGESPEED_UNAVAILABLE) from error


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    if _is_page_load_failure(response):
        logger.info("Lighthouse could not load the page: %s", _error_message(response))
        raise PageSpeedError(AuditFailureReason.SITE_UNREACHABLE)
    if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
        logger.warning("PageSpeed quota exceeded: %s", _error_message(response))
        raise PageSpeedError(AuditFailureReason.PAGESPEED_QUOTA_EXCEEDED)
    logger.error("PageSpeed responded %s: %s", response.status_code, _error_message(response))
    raise PageSpeedError(AuditFailureReason.PAGESPEED_UNAVAILABLE)


def _is_page_load_failure(response: httpx.Response) -> bool:
    return response.status_code == httpx.codes.BAD_REQUEST and _error_message(response).startswith(
        LIGHTHOUSE_PAGE_ERROR_PREFIX
    )


def _error_message(response: httpx.Response) -> str:
    try:
        return PageSpeedErrorResponse.model_validate_json(response.content).error.message
    except ValidationError:
        return response.text[:500]


def build_device_report(result: LighthouseResult, device: Device) -> DeviceReportData:
    score = result.categories.performance.score
    if result.runtime_error is not None or score is None:
        logger.warning("Lighthouse could not measure the page: %s", result.runtime_error)
        raise PageSpeedError(AuditFailureReason.SITE_UNREACHABLE)

    return DeviceReportData(
        device=device,
        performance_score=round(score * 100),
        first_contentful_paint_ms=_metric(result, "first-contentful-paint"),
        largest_contentful_paint_ms=_metric(result, "largest-contentful-paint"),
        total_blocking_time_ms=_metric(result, "total-blocking-time"),
        cumulative_layout_shift=_metric(result, "cumulative-layout-shift"),
        speed_index_ms=_metric(result, "speed-index"),
        findings=_findings(result),
    )


def _metric(result: LighthouseResult, audit_id: str) -> float | None:
    audit = result.audits.get(audit_id)
    return audit.numeric_value if audit else None


def _findings(result: LighthouseResult) -> list[Finding]:
    findings = [_to_finding(audit) for audit in result.audits.values() if _needs_work(audit)]
    return sorted(findings, key=lambda finding: (-(finding.savings_ms or 0), finding.score))


def _needs_work(audit: LighthouseAudit) -> bool:
    return (
        audit.id not in METRIC_AUDIT_IDS
        and audit.score_display_mode in MEASURED_SCORE_MODES
        and audit.score is not None
        and audit.score < PASSING_SCORE
    )


def _to_finding(audit: LighthouseAudit) -> Finding:
    return Finding(
        lighthouse_id=audit.id,
        title=audit.title,
        description=audit.description,
        score=audit.score or 0,
        display_value=audit.display_value,
        savings_ms=_time_savings(audit),
        savings_bytes=audit.details.overall_savings_bytes if audit.details else None,
    )


def _time_savings(audit: LighthouseAudit) -> float | None:
    savings = [
        audit.metric_savings[metric]
        for metric in TIME_SAVINGS_METRICS
        if audit.metric_savings and metric in audit.metric_savings
    ]
    if savings:
        return max(savings)
    return audit.details.overall_savings_ms if audit.details else None
