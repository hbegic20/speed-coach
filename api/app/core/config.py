from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    database_url: PostgresDsn
    redis_url: RedisDsn
    pagespeed_api_key: SecretStr
    pagespeed_timeout_seconds: float = Field(default=90, gt=0)
    pagespeed_cache_ttl_seconds: int = Field(default=900, gt=0)
    page_fetch_timeout_seconds: float = Field(default=10, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
