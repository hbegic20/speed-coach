from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import Settings


def create_redis_settings(settings: Settings) -> RedisSettings:
    return RedisSettings.from_dsn(str(settings.redis_url))


async def create_job_queue(settings: Settings) -> ArqRedis:
    return await create_pool(create_redis_settings(settings))
