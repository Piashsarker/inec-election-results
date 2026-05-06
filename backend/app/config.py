"""Configuration management for INEC Election Results Agent.

This module provides centralized configuration using Pydantic Settings,
supporting environment variables and .env files for all application settings.

Requirements: 6.1, 6.5, 7.6
"""
from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    # Support DATABASE_URL for cloud deployments (Render, Railway, etc.)
    database_url: str | None = Field(
        default=None,
        alias="DATABASE_URL",
        description="Full database URL (overrides individual settings)"
    )

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="inec_elections", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="postgres", description="Database password")

    @property
    def url(self) -> str:
        """Generate database connection URL."""
        # Use DATABASE_URL if provided (for cloud deployments)
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_url(self) -> str:
        """Generate async database connection URL."""
        # Use DATABASE_URL if provided, converting to asyncpg
        if self.database_url:
            url = self.database_url
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: str | None = Field(default=None, description="Redis password")

    @property
    def url(self) -> str:
        """Generate Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class ScrapingSettings(BaseSettings):
    """Scraping engine configuration (Requirements 6.1, 6.5)."""

    model_config = SettingsConfigDict(env_prefix="SCRAPING_")

    # Target scope configuration (Requirement 6.1)
    target_election_type: str | None = Field(
        default=None,
        description="Target election type to scrape (None = all)"
    )
    target_state: str | None = Field(
        default=None,
        description="Target state to scrape (None = all)"
    )
    target_lga: str | None = Field(
        default=None,
        description="Target LGA to scrape (None = all)"
    )
    target_ward: str | None = Field(
        default=None,
        description="Target ward to scrape (None = all)"
    )

    # Rate limiting (Requirement 6.5)
    max_concurrent_requests: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent browser requests"
    )
    request_delay_seconds: float = Field(
        default=1.0,
        ge=0.1,
        description="Delay between requests in seconds"
    )

    # Retry configuration
    max_retries: int = Field(
        default=5,
        ge=1,
        description="Maximum retry attempts for failed requests"
    )
    backoff_factor: float = Field(
        default=2.0,
        ge=1.0,
        description="Exponential backoff multiplier"
    )

    # Download settings
    download_timeout_seconds: int = Field(
        default=30,
        ge=10,
        description="Timeout for downloading result sheets"
    )
    storage_path: str = Field(
        default="./data/result_sheets",
        description="Path to store downloaded result sheets"
    )


class OCRSettings(BaseSettings):
    """OCR engine configuration."""

    model_config = SettingsConfigDict(env_prefix="OCR_")

    tesseract_lang: str = Field(
        default="eng",
        description="Tesseract language code"
    )
    tesseract_config: str = Field(
        default="--psm 6",
        description="Tesseract configuration options"
    )
    quality_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Image quality threshold for OCR engine selection"
    )
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score for valid extraction"
    )


class OpenAISettings(BaseSettings):
    """OpenAI API configuration."""

    model_config = SettingsConfigDict(env_prefix="OPENAI_")

    api_key: str = Field(
        default="",
        description="OpenAI API key"
    )
    model: str = Field(
        default="gpt-4-vision-preview",
        description="OpenAI model for vision tasks"
    )
    max_tokens: int = Field(
        default=1000,
        ge=100,
        description="Maximum tokens for API response"
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Model temperature for response generation"
    )


class CelerySettings(BaseSettings):
    """Celery task queue configuration."""

    model_config = SettingsConfigDict(env_prefix="CELERY_")

    broker_url: str | None = Field(
        default=None,
        description="Celery broker URL (defaults to Redis URL)"
    )
    result_backend: str | None = Field(
        default=None,
        description="Celery result backend URL (defaults to Redis URL)"
    )
    task_default_queue: str = Field(
        default="inec_tasks",
        description="Default task queue name"
    )
    worker_concurrency: int = Field(
        default=4,
        ge=1,
        description="Number of concurrent worker processes"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration (Requirement 7.6)."""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    format: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    file_path: str | None = Field(
        default="./logs/app.log",
        description="Log file path"
    )
    max_file_size_mb: int = Field(
        default=10,
        ge=1,
        description="Maximum log file size in MB before rotation"
    )
    backup_count: int = Field(
        default=5,
        ge=1,
        description="Number of backup log files to keep"
    )


class Settings(BaseSettings):
    """Main application settings aggregating all configuration sections."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    app_name: str = Field(
        default="INEC Election Results Agent",
        description="Application name"
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version"
    )
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    # API settings
    api_prefix: str = Field(
        default="/api/v1",
        description="API route prefix"
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "https://*.vercel.app"],
        description="Allowed CORS origins"
    )

    # INEC Portal
    inec_portal_url: str = Field(
        default="https://www.inecelectionresults.ng/elections/types",
        description="INEC IREV portal base URL"
    )

    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    scraping: ScrapingSettings = Field(default_factory=ScrapingSettings)
    ocr: OCRSettings = Field(default_factory=OCRSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string, JSON array, or list."""
        if v is None:
            return ["http://localhost:3000", "https://*.vercel.app"]
        if isinstance(v, str):
            # Try to parse as JSON first
            v = v.strip()
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:3000", "https://*.vercel.app"]

    def get_celery_broker_url(self) -> str:
        """Get Celery broker URL, defaulting to Redis URL."""
        return self.celery.broker_url or self.redis.url

    def get_celery_result_backend(self) -> str:
        """Get Celery result backend URL, defaulting to Redis URL."""
        return self.celery.result_backend or self.redis.url


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance.

    Uses LRU cache to ensure settings are loaded only once
    and reused across the application.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Convenience export for direct import
settings = get_settings()
