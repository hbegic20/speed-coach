from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.client_identity import client_id
from app.core.config import Settings, get_settings
from app.schemas.errors import ErrorCode
from app.services.rate_limit import (
    RateLimiter,
    RateLimitExceededError,
    RateLimitRule,
    RedisCounterStore,
)

SECONDS_PER_DAY = 24 * 60 * 60
SECONDS_PER_HOUR = 60 * 60

SettingsDependency = Annotated[Settings, Depends(get_settings)]


def get_rate_limiter(request: Request) -> RateLimiter:
    return RateLimiter(RedisCounterStore(request.app.state.job_queue))


Limiter = Annotated[RateLimiter, Depends(get_rate_limiter)]


def _too_many_requests(error: RateLimitExceededError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=ErrorCode.RATE_LIMITED,
        headers={"Retry-After": str(error.retry_after_seconds)},
    )


async def limit_audit_creation(
    request: Request, settings: SettingsDependency, limiter: Limiter
) -> None:
    try:
        await limiter.enforce(
            client_id(request, settings),
            client_rules=(
                RateLimitRule(
                    "audits-burst", settings.audit_burst_limit, settings.audit_burst_window_seconds
                ),
                RateLimitRule("audits-daily", settings.audit_daily_limit, SECONDS_PER_DAY),
            ),
            shared_rules=(
                RateLimitRule(
                    "audits-global-daily", settings.audit_global_daily_limit, SECONDS_PER_DAY
                ),
            ),
        )
    except RateLimitExceededError as error:
        raise _too_many_requests(error) from error


async def limit_site_tracking(
    request: Request, settings: SettingsDependency, limiter: Limiter
) -> None:
    try:
        await limiter.enforce(
            client_id(request, settings),
            client_rules=(
                RateLimitRule("sites-hourly", settings.site_hourly_limit, SECONDS_PER_HOUR),
            ),
        )
    except RateLimitExceededError as error:
        raise _too_many_requests(error) from error
