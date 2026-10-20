"""Application settings and configuration management."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ProcurePulse"
    APP_ENV: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # Database
    # Defaults to local async sqlite for immediate local testing if Postgres is not configured
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./procurepulse.db",
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Security
    SECRET_KEY: str = "procurepulse-super-secret-key-change-in-production-min32chars"

    # Chaos & Observability
    CHAOS_ENABLED: bool = True
    METRICS_ENABLED: bool = True
    SLO_TARGET_AVAILABILITY: float = 0.999
    SLO_TARGET_LATENCY_P95_MS: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
