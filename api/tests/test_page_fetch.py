import ipaddress
from collections.abc import Callable

import httpx
import pytest

from app.services.page_fetch import (
    MAX_BODY_BYTES,
    MAX_REDIRECTS,
    IPAddress,
    PageFetcher,
    PageFetchError,
    Resolver,
    UnsafeDestinationError,
    is_public_address,
)

PUBLIC_IP = "93.184.215.14"
OTHER_PUBLIC_IP = "151.101.1.69"

Handler = Callable[[httpx.Request], httpx.Response]


def resolver_for(table: dict[str, list[str]]) -> Resolver:
    async def resolve(host: str, port: int) -> list[IPAddress]:
        if host not in table:
            raise PageFetchError(f"Could not resolve {host}")
        return [ipaddress.ip_address(address) for address in table[host]]

    return resolve


def fetcher_for(table: dict[str, list[str]], handler: Handler) -> PageFetcher:
    return PageFetcher(
        timeout_seconds=5,
        resolver=resolver_for(table),
        transport=httpx.MockTransport(handler),
    )


def html_response(body: str = "<html></html>") -> Handler:
    return lambda _request: httpx.Response(200, html=body)


async def test_connects_to_the_checked_address_with_the_original_host() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, html="<html>hello</html>")

    page = await fetcher_for({"example.com": [PUBLIC_IP]}, handler).fetch(
        "https://example.com/shop?page=2"
    )

    [request] = requests
    assert request.url.host == PUBLIC_IP
    assert request.url.raw_path == b"/shop?page=2"
    assert request.headers["Host"] == "example.com"
    assert request.extensions["sni_hostname"] == "example.com"
    assert page.url == "https://example.com/shop?page=2"
    assert page.html == "<html>hello</html>"


@pytest.mark.parametrize(
    "addresses",
    [
        ["127.0.0.1"],
        ["10.1.2.3"],
        ["192.168.0.10"],
        ["169.254.169.254"],
        ["100.64.0.1"],
        ["::1"],
        ["fd00::1"],
        ["::ffff:127.0.0.1"],
        [PUBLIC_IP, "10.0.0.1"],
        [],
    ],
)
async def test_refuses_hosts_that_resolve_to_non_public_addresses(addresses: list[str]) -> None:
    fetcher = fetcher_for({"sneaky.example.com": addresses}, html_response())

    with pytest.raises(UnsafeDestinationError):
        await fetcher.fetch("https://sneaky.example.com/")


async def test_follows_redirects_and_checks_every_hop() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers["Host"] == "example.com":
            return httpx.Response(301, headers={"Location": "https://www.example.com/home"})
        return httpx.Response(200, html="<html>home</html>")

    table = {"example.com": [PUBLIC_IP], "www.example.com": [OTHER_PUBLIC_IP]}
    page = await fetcher_for(table, handler).fetch("http://example.com/")

    assert page.url == "https://www.example.com/home"
    assert page.html == "<html>home</html>"


async def test_refuses_redirects_to_internal_hosts() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "http://internal.example.com/admin"})

    table = {"example.com": [PUBLIC_IP], "internal.example.com": ["10.0.0.8"]}

    with pytest.raises(UnsafeDestinationError):
        await fetcher_for(table, handler).fetch("https://example.com/")


async def test_refuses_redirects_to_other_schemes() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "file:///etc/passwd"})

    with pytest.raises(UnsafeDestinationError):
        await fetcher_for({"example.com": [PUBLIC_IP]}, handler).fetch("https://example.com/")


async def test_gives_up_after_too_many_redirects() -> None:
    hops: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        hops.append(request)
        return httpx.Response(302, headers={"Location": f"/hop/{len(hops)}"})

    with pytest.raises(PageFetchError):
        await fetcher_for({"example.com": [PUBLIC_IP]}, handler).fetch("https://example.com/")

    assert len(hops) == MAX_REDIRECTS + 1


async def test_reads_at_most_the_body_limit() -> None:
    oversized = "a" * (MAX_BODY_BYTES * 2)

    page = await fetcher_for({"example.com": [PUBLIC_IP]}, html_response(oversized)).fetch(
        "https://example.com/"
    )

    assert len(page.html) == MAX_BODY_BYTES


async def test_reports_connection_failures() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    with pytest.raises(PageFetchError):
        await fetcher_for({"example.com": [PUBLIC_IP]}, handler).fetch("https://example.com/")


async def test_reports_unresolvable_hosts() -> None:
    with pytest.raises(PageFetchError):
        await fetcher_for({}, html_response()).fetch("https://missing.example.com/")


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("8.8.8.8", True),
        ("2606:4700:4700::1111", True),
        ("0.0.0.0", False),
        ("224.0.0.1", False),
        ("::ffff:10.0.0.1", False),
    ],
)
def test_classifies_public_addresses(address: str, expected: bool) -> None:
    assert is_public_address(ipaddress.ip_address(address)) is expected
