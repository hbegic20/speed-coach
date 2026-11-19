import logging
from collections.abc import Callable
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Protocol

from app.models.audit import Platform
from app.services.page_fetch import FetchedPage, PageFetchError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PageEvidence:
    html: str
    headers: dict[str, str]
    generators: tuple[str, ...]


@dataclass(frozen=True)
class Signature:
    platform: Platform
    name: str
    matches: Callable[[PageEvidence], bool]


@dataclass(frozen=True)
class PlatformDetection:
    platform: Platform
    evidence: tuple[str, ...]


class _GeneratorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.generators: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta":
            return
        attributes = {name.lower(): value or "" for name, value in attrs}
        if attributes.get("name", "").lower() == "generator":
            self.generators.append(attributes.get("content", "").lower())


def _html_contains(fragment: str) -> Callable[[PageEvidence], bool]:
    return lambda evidence: fragment in evidence.html


def _header_present(name: str) -> Callable[[PageEvidence], bool]:
    return lambda evidence: name in evidence.headers


def _header_contains(name: str, fragment: str) -> Callable[[PageEvidence], bool]:
    return lambda evidence: fragment in evidence.headers.get(name, "")


def _generator_contains(fragment: str) -> Callable[[PageEvidence], bool]:
    return lambda evidence: any(fragment in generator for generator in evidence.generators)


SIGNATURES: tuple[Signature, ...] = (
    Signature(Platform.WORDPRESS, "wp-content path", _html_contains("/wp-content/")),
    Signature(Platform.WORDPRESS, "wp-includes path", _html_contains("/wp-includes/")),
    Signature(Platform.WORDPRESS, "generator meta", _generator_contains("wordpress")),
    Signature(Platform.WORDPRESS, "REST API link header", _header_contains("link", "api.w.org")),
    Signature(Platform.SHOPIFY, "Shopify CDN", _html_contains("cdn.shopify.com")),
    Signature(Platform.SHOPIFY, "Shopify theme object", _html_contains("shopify.theme")),
    Signature(Platform.SHOPIFY, "shop id header", _header_present("x-shopid")),
    Signature(Platform.SHOPIFY, "powered-by header", _header_contains("powered-by", "shopify")),
    Signature(Platform.WIX, "request id header", _header_present("x-wix-request-id")),
    Signature(Platform.WIX, "Wix static assets", _html_contains("static.wixstatic.com")),
    Signature(Platform.WIX, "generator meta", _generator_contains("wix.com")),
    Signature(
        Platform.SQUARESPACE, "Squarespace assets", _html_contains("static1.squarespace.com")
    ),
    Signature(Platform.SQUARESPACE, "Squarespace banner", _html_contains("this is squarespace")),
    Signature(Platform.SQUARESPACE, "server header", _header_contains("server", "squarespace")),
    Signature(Platform.WEBFLOW, "site attribute", _html_contains("data-wf-site")),
    Signature(Platform.WEBFLOW, "Webflow assets", _html_contains("website-files.com")),
    Signature(Platform.WEBFLOW, "generator meta", _generator_contains("webflow")),
    Signature(Platform.JOOMLA, "generator meta", _generator_contains("joomla")),
    Signature(Platform.JOOMLA, "Joomla media path", _html_contains("/media/jui/")),
    Signature(Platform.JOOMLA, "Joomla system scripts", _html_contains("/media/system/js/")),
    Signature(Platform.DRUPAL, "generator meta", _generator_contains("drupal")),
    Signature(Platform.DRUPAL, "generator header", _header_contains("x-generator", "drupal")),
    Signature(Platform.DRUPAL, "Drupal cache header", _header_present("x-drupal-cache")),
    Signature(Platform.DRUPAL, "Drupal settings", _html_contains("drupal-settings-json")),
    Signature(Platform.DRUPAL, "Drupal files path", _html_contains("/sites/default/files/")),
    Signature(Platform.NEXTJS, "Next.js data script", _html_contains("__next_data__")),
    Signature(Platform.NEXTJS, "Next.js static assets", _html_contains("/_next/static/")),
    Signature(Platform.NEXTJS, "powered-by header", _header_contains("x-powered-by", "next.js")),
    Signature(Platform.NUXT, "Nuxt state", _html_contains("__nuxt__")),
    Signature(Platform.NUXT, "Nuxt assets", _html_contains("/_nuxt/")),
)

PLATFORM_PRIORITY = tuple(Platform)


def collect_evidence(page: FetchedPage) -> PageEvidence:
    parser = _GeneratorParser()
    parser.feed(page.html)
    return PageEvidence(
        html=page.html.lower(),
        headers={
            name.lower(): ", ".join(page.headers.get_list(name)).lower() for name in page.headers
        },
        generators=tuple(parser.generators),
    )


def detect_platform(page: FetchedPage) -> PlatformDetection:
    evidence = collect_evidence(page)
    matched: dict[Platform, list[str]] = {}
    for signature in SIGNATURES:
        if signature.matches(evidence):
            matched.setdefault(signature.platform, []).append(signature.name)
    if not matched:
        return PlatformDetection(Platform.UNKNOWN, ())

    platform = max(
        matched,
        key=lambda candidate: (len(matched[candidate]), -PLATFORM_PRIORITY.index(candidate)),
    )
    return PlatformDetection(platform, tuple(matched[platform]))


class PageSource(Protocol):
    async def fetch(self, url: str) -> FetchedPage: ...


class PlatformDetector:
    def __init__(self, page_source: PageSource) -> None:
        self._page_source = page_source

    async def detect(self, url: str) -> Platform:
        try:
            page = await self._page_source.fetch(url)
        except PageFetchError:
            logger.info("Could not fetch %s for platform detection", url, exc_info=True)
            return Platform.UNKNOWN
        detection = detect_platform(page)
        logger.info("Detected %s for %s from %s", detection.platform, url, detection.evidence)
        return detection.platform
