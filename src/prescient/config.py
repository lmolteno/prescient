"""Application configuration, sourced from the environment."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Values come from environment variables (optionally an .env file), prefixed
    with ``PRESCIENT_``. e.g. ``PRESCIENT_DATABASE_URL=postgresql+asyncpg://...``.
    """

    model_config = SettingsConfigDict(
        env_prefix="PRESCIENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # postgresql+asyncpg://user:password@host:5432/prescient
    database_url: str = "postgresql+asyncpg://postgres@localhost:5432/prescient"

    api_host: str = "0.0.0.0"
    api_port: int = 8080

    log_level: str = "INFO"
    log_json: bool = Field(
        default=False,
        description="Emit logs as JSON (prod) rather than pretty console (dev).",
    )

    # --- Poller cadence ---
    swpc_poll_interval_seconds: float = 300.0  # 5 minutes
    hmi_poll_interval_seconds: float = 60.0  # idle poll when caught up
    # How far back to backfill HMI observations on a cold start.
    hmi_backfill_days: int = 7

    # --- Source endpoints (overridable for tests) ---
    swpc_base_url: str = "https://services.swpc.noaa.gov"
    hmi_times_url: str = "https://jsoc1.stanford.edu/data/hmi/images/image_times.json"
    hmi_image_base_url: str = "http://jsoc.stanford.edu/data/hmi/images"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
