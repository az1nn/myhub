from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MYHUB_",
        env_file=".env",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str
    bootstrap_token: SecretStr = Field(
        description="One-time operator-controlled bootstrap authorization token."
    )

    @field_validator("bootstrap_token")
    @classmethod
    def validate_bootstrap_token(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("MYHUB_BOOTSTRAP_TOKEN must contain at least 32 characters")
        return value


def validate_canonical_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("canonical_url must be an absolute HTTP(S) URL")

    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and parsed.hostname not in local_hosts:
        raise ValueError("canonical_url must use HTTPS outside localhost")

    return value.rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
