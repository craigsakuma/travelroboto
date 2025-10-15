"""Configuration for the Travel Roboto project.

Typed, 12-factor settings via Pydantic v2. Normalizes Postgres DSNs, derives an
async DSN, and surfaces SQLAlchemy pool options. No I/O or side effects at import.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import URL, make_url
from sqlalchemy.exc import ArgumentError

from app.utils.secrets import secret_to_str

BASE_DIR = Path(__file__).resolve().parent.parent


def coerce_to_psycopg_dsn(raw: str | SecretStr) -> str:
    """Normalize Postgres DSNs to `postgresql+psycopg://...`.

    Accepts common inputs:
      - postgresql://user:pass@host:5432/dbname
      - postgres://user:pass@host/dbname
      - postgresql+psycopg://user:pass@host/dbname?sslmode=prefer

    Returns:
        A DSN string suitable for SQLAlchemy’s psycopg v3 driver.

    Notes:
        - Preserves query params (e.g., sslmode, options, socket host).
        - Non-Postgres URLs are returned unchanged.
    """
    raw_str = secret_to_str(raw)
    if not raw_str:
        raise ValueError("DATABASE_URL must be a non-empty string")

    try:
        url = make_url(raw_str)
    except ArgumentError as exc:
        raise ValueError("Invalid database URL format") from exc

    # Skip normalization for non-Postgres or already psycopg URLs
    backend = url.get_backend_name()
    if not backend.startswith("postgres") or url.drivername == "postgresql+psycopg":
        return str(url)

    normalized = URL.create(
        drivername="postgresql+psycopg",
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database=url.database,
        query=dict(url.query),
    )
    return str(normalized)

class Settings(BaseSettings):
    # --- Pydantic model config  ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App / Logging ---
    app_env: Literal["development", "test", "production"] = Field(default="development")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="DEBUG", description="Python logging verbosity level."
    )

    @property
    def is_prod(self) -> bool:
        return self.app_env == "production"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @property
    def log_level_int(self) -> int:
        """Return stdlib logging level as int (e.g., logging.INFO)."""
        import logging

        return getattr(logging, self.log_level, logging.INFO)

    # --- PostgreSQL Database ---
    database_url: str = Field(
        description="PostgreSQL DSN normalized to postgresql+psycopg.",
    )
    db_pool_size: int = Field(
        default=5,
        ge=1,
        description="Number of persistent connections in the pool.",
    )
    db_max_overflow: int = Field(
        default=5,
        ge=0,
        description="Additional transient connections beyond the pool size.",
    )
    db_pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Seconds to wait for a connection before timing out.",
    )
    db_pool_recycle: int = Field(
        default=1800,
        ge=0,
        description="Seconds before recycling a connection to avoid stale connections.",
    )
    db_echo: bool = Field(
        default=False,
        description="If true, SQLAlchemy will log all SQL statements (useful for debugging).",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_pg_dsn(cls, v: str | SecretStr) -> str:
        # Accept str or SecretStr; let the coercer unwrap/validate/normalize.
        if isinstance(v, (str, SecretStr)):
            return coerce_to_psycopg_dsn(v)
        raise ValueError("DATABASE_URL must be str or SecretStr")

    @property
    def database_url_sync(self) -> str:
        """Canonical sync DSN (alias for database_url)."""
        return self.database_url

    @property
    def database_url_async(self) -> str:
        try:
            u = make_url(self.database_url)
        except ArgumentError as exc:
            raise ValueError("Invalid database URL format") from exc
        if u.get_backend_name() in {"postgres", "postgresql"}:
            return str(u.set(drivername="postgresql+asyncpg"))
        return self.database_url

    def sqlalchemy_engine_url(self) -> str:
        """Normalized SQLAlchemy engine URL (sync)."""
        return self.database_url_sync

    def sqlalchemy_engine_kwargs(self) -> dict[str, Any]:
        """Return engine keyword args derived from pool settings."""
        return {
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "pool_timeout": self.db_pool_timeout,
            "pool_recycle": self.db_pool_recycle,
            "pool_pre_ping": True,  # resilient to stale connections
            "echo": self.db_echo,
        }

    # --- LLM ---
    openai_api_key: SecretStr | None = Field(
        default=None,
        description="API key used for OpenAI LLM and embedding services.",
    )

    # --- Gmail OAuth ---
    travelbot_gmail_client_id: str = Field(
        default="",
        description="Google OAuth 2.0 client ID for the TravelBot Gmail integration.",
    )
    travelbot_gmail_client_secret: SecretStr | None = Field(
        default=None,
        description="Google OAuth 2.0 client secret used for Gmail authentication.",
    )
    credentials_dir: Path = Field(
        default=BASE_DIR / "credentials",
        description="Local directory where OAuth credentials are stored.",
    )
    gmail_token_file: Path = Field(
        default=BASE_DIR / "credentials" / "token.json",
        description="Path to the saved Gmail OAuth access token.",
    )
    scopes: tuple[str, ...] = Field(
        default=("https://www.googleapis.com/auth/gmail.readonly",),
        description="OAuth scopes requested for Gmail API access.",
    )

    # --- Twilio (SMS) / A2P 10DLC---
    twilio_account_sid: SecretStr | None = Field(
        default=None,
        description="Twilio Account SID identifying the messaging account.",
    )
    twilio_auth_token: SecretStr | None = Field(
        default=None,
        description="Twilio Auth Token used for authenticated API requests.",
    )
    twilio_phone_number: str | None = Field(
        default=None,
        description="E.164-formatted Twilio phone number used for sending SMS messages.",
    )

    # US A2P 10DLC (required for application-to-person messaging in the US)
    a2p_customer_profile: str | None = Field(
        default=None,
        description="Twilio A2P 10DLC customer profile ID (registered entity).",
    )
    a2p_brand: str | None = Field(
        default=None,
        description="Twilio A2P 10DLC brand ID representing the message sender brand.",
    )
    a2p_campaign: str | None = Field(
        default=None,
        description="Twilio A2P 10DLC campaign ID linked to approved message templates.",
    )

    # --- Web UI asset paths ---
    templates_dir: Path = Field(
        default=BASE_DIR / "app/interfaces/web/templates",
        description="Directory containing Jinja2 templates.",
    )
    static_dir: Path = Field(
        default=BASE_DIR / "app/interfaces/web/static",
        description="Directory containing static assets (CSS/JS/images).",
    )
    icons_dir: Path | None = Field(
        default=None,
        description="Optional override for the icons directory; defaults to <static_dir>/icons.",
    )
    favicon_filename: str = Field(
        default="favicon.ico",
        description="Filename of the favicon within the icons directory.",
    )
    web_manifest_filename: str = Field(
        default="site.webmanifest",
        description="Filename of the Web App Manifest within the icons directory.",
    )

    @property
    def resolved_icons_dir(self) -> Path:
        return self.icons_dir or (self.static_dir / "icons")

    @property
    def favicon_path(self) -> Path:
        return self.resolved_icons_dir / self.favicon_filename

    @property
    def webmanifest_path(self) -> Path:
        return self.resolved_icons_dir / self.web_manifest_filename

    # --- Trip context (dev shim) ---
    trip_context_path: str = Field(
        default="tests/test_data/test_itinerary.txt",
        description="Path to local test itinerary used for development/testing only.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide singleton Settings (FastAPI DI-friendly)."""
    return Settings()
