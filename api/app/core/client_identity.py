import hmac
import ipaddress
import logging

from fastapi import Request

from app.core.config import Settings

logger = logging.getLogger(__name__)

CLIENT_IP_HEADER = "X-SpeedCoach-Client-IP"
PROXY_SECRET_HEADER = "X-SpeedCoach-Proxy-Secret"
UNKNOWN_CLIENT = "unknown"


def _is_trusted_proxy(request: Request, settings: Settings) -> bool:
    expected = settings.web_proxy_secret
    provided = request.headers.get(PROXY_SECRET_HEADER)
    if expected is None or provided is None:
        return False
    return hmac.compare_digest(provided.encode(), expected.get_secret_value().encode())


def _forwarded_ip(request: Request) -> str | None:
    forwarded = request.headers.get(CLIENT_IP_HEADER)
    if forwarded is None:
        return None
    try:
        return str(ipaddress.ip_address(forwarded.strip()))
    except ValueError:
        logger.warning("Ignoring malformed forwarded client IP")
        return None


def client_id(request: Request, settings: Settings) -> str:
    if _is_trusted_proxy(request, settings):
        forwarded = _forwarded_ip(request)
        if forwarded is not None:
            return forwarded
    return request.client.host if request.client else UNKNOWN_CLIENT
