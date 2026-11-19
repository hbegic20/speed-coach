from fastapi import APIRouter, Response, status

from app.core.dependencies import DbSession
from app.schemas.health import HealthResponse, HealthStatus
from app.services.health import database_is_reachable

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def read_health(session: DbSession, response: Response) -> HealthResponse:
    if await database_is_reachable(session):
        return HealthResponse(status=HealthStatus.OK)
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status=HealthStatus.UNAVAILABLE)
