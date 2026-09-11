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

    auth_challenge_ttl_seconds: int = 300
    auth_session_ttl_seconds: int = 30 * 24 * 60 * 60

    password_argon2_memory_kib: int = 19_456
    password_argon2_time_cost: int = 2
    password_argon2_parallelism: int = 1

    android_package_name: str | None = None
    android_sha256_cert_fingerprints: str = ""

    @field_validator("bootstrap_token")
    @classmethod
    def validate_bootstrap_token(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("MYHUB_BOOTSTRAP_TOKEN must contain at least 32 characters")
        return value

    @field_validator("auth_challenge_ttl_seconds")
    @classmethod
    def validate_challenge_ttl(cls, value: int) -> int:
        if not 30 <= value <= 900:
            raise ValueError("MYHUB_AUTH_CHALLENGE_TTL_SECONDS must be between 30 and 900")
        return value

    @field_validator("auth_session_ttl_seconds")
    @classmethod
    def validate_session_ttl(cls, value: int) -> int:
        if not 300 <= value <= 365 * 24 * 60 * 60:
            raise ValueError("MYHUB_AUTH_SESSION_TTL_SECONDS must be between 300 seconds and 365 days")
        return value

    @field_validator("password_argon2_memory_kib")
    @classmethod
    def validate_argon2_memory(cls, value: int) -> int:
        if value < 19_456:
            raise ValueError("MYHUB_PASSWORD_ARGON2_MEMORY_KIB must be at least 19456")
        return value

    @field_validator("password_argon2_time_cost")
    @classmethod
    def validate_argon2_time_cost(cls, value: int) -> int:
        if value < 2:
            raise ValueError("MYHUB_PASSWORD_ARGON2_TIME_COST must be at least 2")
        return value

    @field_validator("password_argon2_parallelism")
    @classmethod
    def validate_argon2_parallelism(cls, value: int) -> int:
        if value < 1:
            raise ValueError("MYHUB_PASSWORD_ARGON2_PARALLELISM must be at least 1")
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
