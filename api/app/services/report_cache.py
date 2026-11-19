import hashlib
import logging
from typing import Protocol

from pydantic import ValidationError
from redis.exceptions import RedisError

from app.models.device_report import Device
from app.schemas.report import DeviceReportData

logger = logging.getLogger(__name__)


class KeyValueStore(Protocol):
    async def get(self, name: str) -> bytes | None: ...

    async def set(self, name: str, value: str, ex: int) -> object: ...


def cache_key(url: str, device: Device) -> str:
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    return f"pagespeed:v2:{device.value}:{url_hash}"


class ReportCache:
    def __init__(self, store: KeyValueStore, ttl_seconds: int) -> None:
        self._store = store
        self._ttl_seconds = ttl_seconds

    async def get(self, url: str, device: Device) -> DeviceReportData | None:
        try:
            cached = await self._store.get(cache_key(url, device))
        except RedisError:
            logger.warning("Report cache read failed, fetching fresh report", exc_info=True)
            return None
        if cached is None:
            return None
        try:
            return DeviceReportData.model_validate_json(cached)
        except ValidationError:
            logger.warning("Discarding malformed cached report for %s", device, exc_info=True)
            return None

    async def put(self, url: str, report: DeviceReportData) -> None:
        try:
            await self._store.set(
                cache_key(url, report.device), report.model_dump_json(), ex=self._ttl_seconds
            )
        except RedisError:
            logger.warning("Report cache write failed", exc_info=True)
