import httpx
import pytest

from app.models.audit import Platform
from app.services.page_fetch import FetchedPage, PageFetchError
from app.services.platform_detection import PlatformDetector, detect_platform


def page(html: str = "<html></html>", headers: dict[str, str] | None = None) -> FetchedPage:
    return FetchedPage(url="https://example.com/", headers=httpx.Headers(headers), html=html)


@pytest.mark.parametrize(
    ("fetched", "platform"),
    [
        (
            page('<link rel="stylesheet" href="/wp-content/themes/astra/style.css">'),
            Platform.WORDPRESS,
        ),
        (page('<meta name="generator" content="WordPress 6.7.1">'), Platform.WORDPRESS),
        (
            page(headers={"Link": '<https://example.com/wp-json/>; rel="https://api.w.org/"'}),
            Platform.WORDPRESS,
        ),
        (page('<script src="//cdn.shopify.com/s/files/theme.js"></script>'), Platform.SHOPIFY),
        (page(headers={"Powered-By": "Shopify"}), Platform.SHOPIFY),
        (page(headers={"X-Wix-Request-Id": "1732012345.123"}), Platform.WIX),
        (page('<meta content="Wix.com Website Builder" name="generator">'), Platform.WIX),
        (page("<!-- This is Squarespace. --><html></html>"), Platform.SQUARESPACE),
        (page('<html data-wf-site="64a1f" data-wf-page="64a20">'), Platform.WEBFLOW),
        (
            page('<meta name="generator" content="Joomla! - Open Source Content Management">'),
            Platform.JOOMLA,
        ),
        (page(headers={"X-Generator": "Drupal 10 (https://www.drupal.org)"}), Platform.DRUPAL),
        (
            page('<script id="__NEXT_DATA__" type="application/json">{}</script>'),
            Platform.NEXTJS,
        ),
        (page(headers={"X-Powered-By": "Next.js"}), Platform.NEXTJS),
        (page('<script src="/_nuxt/entry.js"></script>'), Platform.NUXT),
        (page("<html><body>Plain hand-written site</body></html>"), Platform.UNKNOWN),
    ],
)
def test_recognizes_platform_signatures(fetched: FetchedPage, platform: Platform) -> None:
    assert detect_platform(fetched).platform is platform


def test_reports_which_signals_matched() -> None:
    detection = detect_platform(
        page(
            '<meta name="generator" content="WordPress 6.7">'
            '<script src="/wp-includes/js/jquery.min.js"></script>'
        )
    )

    assert detection.evidence == ("wp-includes path", "generator meta")


def test_prefers_the_platform_with_the_most_signals() -> None:
    detection = detect_platform(
        page(
            '<script src="/_next/static/chunks/main.js"></script>'
            '<script id="__NEXT_DATA__">{}</script>'
            '<script src="https://cdn.shopify.com/shopifycloud/buy-button.js"></script>'
        )
    )

    assert detection.platform is Platform.NEXTJS


class StaticPageSource:
    def __init__(self, fetched: FetchedPage) -> None:
        self.fetched = fetched

    async def fetch(self, url: str) -> FetchedPage:
        return self.fetched


class UnreachablePageSource:
    async def fetch(self, url: str) -> FetchedPage:
        raise PageFetchError("Connection refused")


async def test_detector_returns_the_detected_platform() -> None:
    detector = PlatformDetector(StaticPageSource(page(headers={"X-ShopId": "123"})))

    assert await detector.detect("https://example.com/") is Platform.SHOPIFY


async def test_detector_falls_back_to_unknown_when_page_cannot_be_fetched() -> None:
    detector = PlatformDetector(UnreachablePageSource())

    assert await detector.detect("https://example.com/") is Platform.UNKNOWN
