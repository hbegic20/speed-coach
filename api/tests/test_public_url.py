import pytest
from pydantic import ValidationError

from app.schemas.audit import AuditCreate


@pytest.mark.parametrize(
    ("submitted", "normalized"),
    [
        ("https://example.com", "https://example.com/"),
        ("http://shop.example.ba/products?page=2", "http://shop.example.ba/products?page=2"),
        ("https://EXAMPLE.com/Path", "https://example.com/Path"),
        ("https://example.com:8443/", "https://example.com:8443/"),
    ],
)
def test_accepts_public_website_urls(submitted: str, normalized: str) -> None:
    assert str(AuditCreate.model_validate({"url": submitted, "language": "en"}).url) == normalized


@pytest.mark.parametrize(
    "submitted",
    [
        "",
        "example.com",
        "ftp://example.com",
        "javascript:alert(1)",
        "file:///etc/passwd",
        "http://localhost:3000",
        "http://app.localhost",
        "http://printer.local",
        "http://metadata.google.internal",
        "http://intranet",
        "http://127.0.0.1",
        "http://10.0.0.5",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]",
        "http://2130706433",
        "http://0x7f.0.0.1",
        "https://user:secret@example.com",
        "https://example.com/" + "a" * 2048,
    ],
)
def test_rejects_urls_that_are_not_public_websites(submitted: str) -> None:
    with pytest.raises(ValidationError):
        AuditCreate.model_validate({"url": submitted, "language": "en"})


def test_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AuditCreate.model_validate(
            {"url": "https://example.com", "language": "en", "device": "mobile"}
        )


@pytest.mark.parametrize("language", ["bs", "en"])
def test_accepts_supported_languages(language: str) -> None:
    payload = AuditCreate.model_validate({"url": "https://example.com", "language": language})

    assert payload.language == language


@pytest.mark.parametrize(
    "payload", [{"url": "https://example.com"}, {"url": "https://example.com", "language": "de"}]
)
def test_requires_a_supported_language(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        AuditCreate.model_validate(payload)
