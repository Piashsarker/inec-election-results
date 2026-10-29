"""Configuration management for INEC Election Results Agent.

This module provides centralized configuration using Pydantic Settings,
supporting environment variables and .env files for all application settings.

Requirements: 6.1, 6.5, 7.6
"""
from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env absolute path relative to this file so it works regardless of cwd
_ENV_FILE = str(Path(__file__).parent.parent / ".env")

# Load .env into os.environ BEFORE any sub-config class is instantiated.
# override=True ensures .env values win over any shell-level empty strings.
load_dotenv(_ENV_FILE, override=True)

# Shared dict used by every sub-config's SettingsConfigDict so they all
# read from the same .env and handle extras/case consistently.
_SUB_CONFIG: dict = dict(
    env_file=_ENV_FILE,
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore",
)


class LogLevel(StrEnum):
    """Supported log levels (Requirement 7.6)."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Environment(StrEnum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


# ── Sub-configs ────────────────────────────────────────────────────────────────

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(env_prefix="DB_", **_SUB_CONFIG)

    database_url: str | None = Field(
        default=None,
        alias="DATABASE_URL",
        description="Full database URL (overrides individual settings)",
    )
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="inec_elections")
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")

    @property
    def url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_url(self) -> str:
        if self.database_url:
            url = self.database_url
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    model_config = SettingsConfigDict(env_prefix="REDIS_", **_SUB_CONFIG)

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: str | None = Field(default=None)

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class ScrapingSettings(BaseSettings):
    """Scraping engine configuration (Requirements 6.1, 6.5)."""

    model_config = SettingsConfigDict(env_prefix="SCRAPING_", **_SUB_CONFIG)

    target_election_type: str | None = Field(default=None)
    target_state: str | None = Field(default=None)
    target_lga: str | None = Field(default=None)
    target_ward: str | None = Field(default=None)

    max_concurrent_requests: int = Field(default=5, ge=1, le=20)
    request_delay_seconds: float = Field(default=1.0, ge=0.1)
    max_retries: int = Field(default=5, ge=1)
    backoff_factor: float = Field(default=2.0, ge=1.0)
    download_timeout_seconds: int = Field(default=30, ge=10)
    storage_path: str = Field(default="./data/result_sheets")


class StorageSettings(BaseSettings):
    """Cloud storage configuration (Cloudflare R2 / AWS S3 / compatible).

    Set S3_BUCKET + credentials to enable cloud upload.
    Leave S3_BUCKET empty to fall back to local filesystem.
    """

    model_config = SettingsConfigDict(env_prefix="S3_", **_SUB_CONFIG)

    bucket: str = Field(default="", description="S3 / R2 bucket name")
    endpoint_url: str = Field(
        default="",
        description="Custom S3-compatible endpoint (Cloudflare R2, MinIO, B2…)",
    )
    access_key_id: str = Field(default="", description="AWS / R2 access key ID")
    secret_access_key: str = Field(default="", description="AWS / R2 secret access key")
    region: str = Field(default="auto", description="AWS region or 'auto' for R2")
    public_url_base: str = Field(
        default="",
        description="Optional public CDN base URL (e.g. https://images.yourdomain.com)",
    )


class OCRSettings(BaseSettings):
    """OCR engine configuration."""

    model_config = SettingsConfigDict(env_prefix="OCR_", **_SUB_CONFIG)

    tesseract_lang: str = Field(default="eng", description="Tesseract language (compat only)")
    tesseract_config: str = Field(default="--psm 6", description="Tesseract config (compat only)")
    quality_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="Image quality threshold (metadata only — GPT-4 Vision ignores this)",
    )
    confidence_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0,
        description="Minimum confidence score for valid extraction",
    )


class OpenAISettings(BaseSettings):
    """OpenAI API configuration."""

    model_config = SettingsConfigDict(env_prefix="OPENAI_", **_SUB_CONFIG)

    api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-4o", description="OpenAI model for vision tasks")
    max_tokens: int = Field(default=1000, ge=100)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class CelerySettings(BaseSettings):
    """Celery task queue configuration."""

    model_config = SettingsConfigDict(env_prefix="CELERY_", **_SUB_CONFIG)

    broker_url: str | None = Field(default=None)
    result_backend: str | None = Field(default=None)
    task_default_queue: str = Field(default="inec_tasks")
    worker_concurrency: int = Field(default=4, ge=1)


class LoggingSettings(BaseSettings):
    """Logging configuration (Requirement 7.6)."""

    model_config = SettingsConfigDict(env_prefix="LOG_", **_SUB_CONFIG)

    level: LogLevel = Field(default=LogLevel.INFO)
    format: str = Field(default="json")
    file_path: str | None = Field(default="./logs/app.log")
    max_file_size_mb: int = Field(default=10, ge=1)
    backup_count: int = Field(default=5, ge=1)


# ── Root settings ──────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    """Main application settings aggregating all configuration sections."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="INEC Election Results Agent")
    app_version: str = Field(default="0.1.0")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    api_prefix: str = Field(default="/api/v1")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "https://*.vercel.app"],
    )

    inec_portal_url: str = Field(
        default="https://www.inecelectionresults.ng/elections/types",
    )

    # Sub-configurations — each factory re-reads from os.environ
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    scraping: ScrapingSettings = Field(default_factory=ScrapingSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    ocr: OCRSettings = Field(default_factory=OCRSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        """Parse CORS origins from comma-separated string, JSON array, or list."""
        if v is None:
            return ["http://localhost:3000", "https://*.vercel.app"]
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [o.strip() for o in v.split(",") if o.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:3000", "https://*.vercel.app"]

    def get_celery_broker_url(self) -> str:
        return self.celery.broker_url or self.redis.url

    def get_celery_result_backend(self) -> str:
        return self.celery.result_backend or self.redis.url


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance."""
    return Settings()


# Convenience export for direct import
settings = get_settings()
