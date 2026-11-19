import ipaddress
from typing import Annotated

from pydantic import AfterValidator, HttpUrl, UrlConstraints

from app.models.audit import MAX_URL_LENGTH

RESERVED_HOST_SUFFIXES = (".localhost", ".local", ".internal", ".home.arpa", ".lan")


def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return False
    return True


def _is_reserved_hostname(host: str) -> bool:
    return host == "localhost" or host.endswith(RESERVED_HOST_SUFFIXES)


def ensure_public_url(url: HttpUrl) -> HttpUrl:
    host = (url.host or "").lower().rstrip(".")
    if url.username or url.password:
        raise ValueError("URL must not contain credentials")
    if _is_ip_address(host):
        raise ValueError("URL must use a domain name, not an IP address")
    if "." not in host or _is_reserved_hostname(host):
        raise ValueError("URL must point to a public website")
    return url


PublicHttpUrl = Annotated[
    HttpUrl,
    UrlConstraints(max_length=MAX_URL_LENGTH, allowed_schemes=["http", "https"]),
    AfterValidator(ensure_public_url),
]
