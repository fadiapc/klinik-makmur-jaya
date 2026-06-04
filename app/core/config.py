"""
Application configuration — loaded from environment variables via Pydantic-Settings.

All settings are type-validated at startup.  Never hard-code secrets; provide
them through a .env file (development) or a secrets manager (production).
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Klinik Makmur Jaya backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Klinik Makmur Jaya E-Commerce API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "RESTful API for the Klinik Makmur Jaya drug e-commerce platform. "
        "Built with FastAPI, SQLAlchemy (async), and PostgreSQL."
    )
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "klinik_makmur_jaya"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"

    # Optional full URL override — if provided, the individual fields above
    # are ignored for connection purposes.
    DATABASE_URL: str | None = None

    # SQLAlchemy async connection pool settings
    DB_POOL_SIZE: int = Field(default=10, ge=1, le=50)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=5)
    DB_POOL_RECYCLE: int = Field(default=1800, ge=60)  # seconds

    # ── Security / JWT ────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32",
        min_length=32,
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # ── File Storage ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = Field(default=2, ge=1, le=10)

    # ── Email (FastAPI-Mail / Mailtrap) ───────────────────────────────────────
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@klinikmakmurjaya.id"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.mailtrap.io"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # ── Frontend ──────────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"
    # Base URL of the React frontend — used to build email-verification links.

    # ── Computed helpers ──────────────────────────────────────────────────────
    @property
    def async_database_url(self) -> str:
        """Return the async-compatible PostgreSQL DSN (asyncpg driver)."""
        if self.DATABASE_URL:
            # Allow full override from env, but ensure asyncpg driver prefix
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url

        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def sync_database_url(self) -> str:
        """Return the sync PostgreSQL DSN (psycopg2) — used by Alembic only."""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
            return url

        return (
            f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def redis_url(self) -> str:
        """Return a Redis connection URL."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached singleton of Settings.

    Using lru_cache ensures the .env file is read exactly once per process
    lifetime, which is efficient and safe for production.
    """
    return Settings()


# Module-level convenience alias
settings: Settings = get_settings()
