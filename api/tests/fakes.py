from typing import Any

from arq.jobs import Job
from redis.exceptions import ConnectionError as RedisConnectionError


class RecordingQueue:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, tuple[Any, ...]]] = []

    async def enqueue_job(self, function: str, *args: Any) -> Job | None:
        self.jobs.append((function, args))
        return None


class UnavailableQueue:
    async def enqueue_job(self, function: str, *args: Any) -> Job | None:
        raise RedisConnectionError("Redis is unreachable")
