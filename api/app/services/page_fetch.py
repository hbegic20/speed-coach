import asyncio
import ipaddress
import logging
import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
Resolver = Callable[[str, int], Awaitable[list[IPAddress]]]

ALLOWED_SCHEMES = frozenset({"http", "https"})
MAX_REDIRECTS = 5
MAX_BODY_BYTES = 1_000_000
USER_AGENT = "Mozilla/5.0 (compatible; SpeedCoach/1.0)"


class PageFetchError(Exception):
    pass


class UnsafeDestinationError(PageFetchError):
    pass


@dataclass(frozen=True)
class FetchedPage:
    url: str
    headers: httpx.Headers
    html: str


async def resolve_host(host: str, port: int) -> list[IPAddress]:
    loop = asyncio.get_running_loop()
    try:
        address_info = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as error:
        raise PageFetchError(f"Could not resolve {host}") from error
    return list(dict.fromkeys(ipaddress.ip_address(info[4][0]) for info in address_info))


def is_public_address(address: IPAddress) -> bool:
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        return is_public_address(address.ipv4_mapped)
    return address.is_global and not address.is_multicast


class PageFetcher:
    def __init__(
        self,
        timeout_seconds: float,
        resolver: Resolver = resolve_host,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._resolver = resolver
        self._transport = transport

    async def fetch(self, url: str) -> FetchedPage:
        current_url = httpx.URL(url)
        for _ in range(MAX_REDIRECTS + 1):
            outcome = await self._fetch_once(current_url)
            if isinstance(outcome, FetchedPage):
                return outcome
            current_url = outcome
        raise PageFetchError(f"More than {MAX_REDIRECTS} redirects")

    async def _fetch_once(self, url: httpx.URL) -> FetchedPage | httpx.URL:
        address = await self._public_address_for(url)
        try:
            async with self._client() as client:
                request = self._pinned_request(client, url, address)
                response = await client.send(request, stream=True)
                try:
                    if response.is_redirect:
                        return url.join(response.headers["location"])
                    html = await _read_limited_text(response)
                    return FetchedPage(url=str(url), headers=response.headers, html=html)
                finally:
                    await response.aclose()
        except (httpx.HTTPError, httpx.InvalidURL) as error:
            raise PageFetchError(f"Fetching {url.host} failed") from error

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=self._transport,
            timeout=self._timeout_seconds,
            follow_redirects=False,
            trust_env=False,
        )

    async def _public_address_for(self, url: httpx.URL) -> IPAddress:
        if url.scheme not in ALLOWED_SCHEMES or not url.host:
            raise UnsafeDestinationError(f"Refusing to fetch {url.scheme} URL")
        addresses = await self._resolver(url.host, url.port or _default_port(url))
        if not addresses or not all(is_public_address(address) for address in addresses):
            raise UnsafeDestinationError(f"{url.host} does not resolve to a public address")
        return addresses[0]

    def _pinned_request(
        self, client: httpx.AsyncClient, url: httpx.URL, address: IPAddress
    ) -> httpx.Request:
        extensions = {"sni_hostname": url.host} if url.scheme == "https" else {}
        return client.build_request(
            "GET",
            url.copy_with(host=str(address)),
            headers={
                "Host": url.netloc.decode("ascii"),
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
            },
            extensions=extensions,
        )


def _default_port(url: httpx.URL) -> int:
    return 443 if url.scheme == "https" else 80


async def _read_limited_text(response: httpx.Response) -> str:
    body = bytearray()
    async for chunk in response.aiter_bytes():
        body.extend(chunk[: MAX_BODY_BYTES - len(body)])
        if len(body) >= MAX_BODY_BYTES:
            break
    try:
        return bytes(body).decode(response.encoding or "utf-8", errors="replace")
    except LookupError:
        return bytes(body).decode("utf-8", errors="replace")
