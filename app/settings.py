"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # APP
    DEBUG: bool
    BFO_URL: str
    PROXY_URL: Optional[str] = None
    REPORT_AVAILABLE_DAYS: int = 7

    # REDIS
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_BFO_TIMEOUT_KEY: str = "bfo:timeout"
    REDIS_BFO_TIMEOUT_SECONDS: int = 180

    # DB
    SQL_DEBUG: bool
    DB_HOSTNAME: str
    DB_PORT: int
    DB_DATABASE: str
    DB_USERNAME: str
    DB_PASSWORD: str
    POSTGRES_DSN: str


settings = AppSettings()
