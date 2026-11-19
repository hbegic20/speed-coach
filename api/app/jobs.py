import uuid
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.services.audits import AuditServices, process_audit
from app.services.device_reports import DeviceReportCollector
from app.services.gemini import GeminiClient
from app.services.page_fetch import PageFetcher
from app.services.pagespeed import PageSpeedClient
from app.services.platform_detection import PlatformDetector
from app.services.recommendations import RecommendationWriter
from app.services.report_cache import ReportCache


def build_audit_services(context: dict[str, Any]) -> AuditServices:
    settings: Settings = context["settings"]
    http_client: httpx.AsyncClient = context["http_client"]
    page_fetcher: PageFetcher = context["page_fetcher"]
    return AuditServices(
        collector=DeviceReportCollector(
            fetcher=PageSpeedClient(http_client, settings.pagespeed_api_key),
            cache=ReportCache(context["redis"], settings.pagespeed_cache_ttl_seconds),
        ),
        detector=PlatformDetector(page_fetcher),
        writer=RecommendationWriter(
            GeminiClient(
                http_client,
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                timeout_seconds=settings.gemini_timeout_seconds,
            )
        ),
    )


async def run_audit(context: dict[str, Any], audit_id: str) -> None:
    session_factory: async_sessionmaker[AsyncSession] = context["session_factory"]
    async with session_factory() as session:
        await process_audit(session, uuid.UUID(audit_id), build_audit_services(context))
