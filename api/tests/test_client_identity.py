from typing import Any

import pytest
from fastapi import Request

from app.core.client_identity import CLIENT_IP_HEADER, PROXY_SECRET_HEADER, client_id
from app.core.config import Settings
from tests.conftest import TEST_PROXY_SECRET

DIRECT_IP = "192.0.2.10"


def request_with(headers: dict[str, str]) -> Request:
    scope: dict[str, Any] = {
        "type": "http",
        "headers": [(name.lower().encode(), value.encode()) for name, value in headers.items()],
        "client": (DIRECT_IP, 51234),
    }
    return Request(scope)


def forwarded(ip: str, secret: str = TEST_PROXY_SECRET) -> dict[str, str]:
    return {CLIENT_IP_HEADER: ip, PROXY_SECRET_HEADER: secret}


def test_uses_the_connection_address_by_default(settings: Settings) -> None:
    assert client_id(request_with({}), settings) == DIRECT_IP


def test_trusts_the_forwarded_address_from_the_web_server(settings: Settings) -> None:
    assert client_id(request_with(forwarded("203.0.113.7")), settings) == "203.0.113.7"


def test_normalizes_forwarded_ipv6_addresses(settings: Settings) -> None:
    assert client_id(request_with(forwarded("2001:DB8::0:1")), settings) == "2001:db8::1"


@pytest.mark.parametrize(
    "headers",
    [
        {CLIENT_IP_HEADER: "203.0.113.7"},
        forwarded("203.0.113.7", secret="guessed-secret"),
        forwarded("not-an-ip"),
    ],
)
def test_ignores_forwarded_addresses_it_cannot_trust(
    settings: Settings, headers: dict[str, str]
) -> None:
    assert client_id(request_with(headers), settings) == DIRECT_IP


def test_never_trusts_forwarding_without_a_configured_secret(settings: Settings) -> None:
    unconfigured = settings.model_copy(update={"web_proxy_secret": None})

    assert client_id(request_with(forwarded("203.0.113.7")), unconfigured) == DIRECT_IP
