import asyncio
from typing import Protocol

from app.models.device_report import Device
from app.schemas.report import DeviceReportData
from app.services.pagespeed import PageSpeedError
from app.services.report_cache import ReportCache


class ReportFetcher(Protocol):
    async def fetch_report(self, url: str, device: Device) -> DeviceReportData: ...


class DeviceReportCollector:
    def __init__(self, fetcher: ReportFetcher, cache: ReportCache) -> None:
        self._fetcher = fetcher
        self._cache = cache

    async def collect(self, url: str) -> list[DeviceReportData]:
        try:
            async with asyncio.TaskGroup() as task_group:
                tasks = [task_group.create_task(self._report_for(url, device)) for device in Device]
        except* PageSpeedError as errors:
            raise errors.exceptions[0] from None
        return [task.result() for task in tasks]

    async def _report_for(self, url: str, device: Device) -> DeviceReportData:
        cached = await self._cache.get(url, device)
        if cached is not None:
            return cached
        report = await self._fetcher.fetch_report(url, device)
        await self._cache.put(url, report)
        return report
