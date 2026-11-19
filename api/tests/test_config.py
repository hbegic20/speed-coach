import pytest

from app.core.config import Settings

REQUIRED = {
    "redis_url": "redis://localhost:6379/0",
    "pagespeed_api_key": "test-pagespeed-key",
    "gemini_api_key": "test-gemini-key",
}


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql://user:secret@db.railway.internal:5432/railway",
        "postgres://user:secret@db.railway.internal:5432/railway",
        "postgresql+asyncpg://user:secret@db.railway.internal:5432/railway",
    ],
)
def test_database_urls_always_use_the_async_driver(database_url: str) -> None:
    settings = Settings.model_validate({**REQUIRED, "database_url": database_url})

    assert str(settings.database_url) == (
        "postgresql+asyncpg://user:secret@db.railway.internal:5432/railway"
    )


def test_rejects_non_postgres_database_urls() -> None:
    with pytest.raises(ValueError, match="database_url"):
        Settings.model_validate({**REQUIRED, "database_url": "mysql://user@localhost/db"})
