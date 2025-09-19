"""
Configuration settings for the TravelBot project.

"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # --- App ---
    app_env: Literal["development", "test", "production"] = Field(default="development")

    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="DEBUG", description="Logging level for the application"
    )

    # --- Web UI asset paths ---
    templates_dir: Path = Field(
        default=BASE_DIR / "app/interfaces/web/templates",
        description="Directory containing Jinja2 templates",
    )
    static_dir: Path = Field(
        default=BASE_DIR / "app/interfaces/web/static",
        description="Directory containing static assets",
    )

    icons_dir: Path | None = None
    favicon_filename: str = "favicon.ico"
    manifest_filename: str = "site.webmanifest"

    @property
    def resolved_icons_dir(self) -> Path:
        return self.icons_dir or (self.static_dir / "icons")

    @property
    def favicon_path(self) -> Path:
        return self.resolved_icons_dir / self.favicon_filename

    @property
    def webmanifest_path(self) -> Path:
        return self.resolved_icons_dir / self.manifest_filename

    # --- LLM ---
    openai_api_key: SecretStr | None = None

    # --- Trip context (dev shim) ---
    trip_context_path: str = "tests/test_data/test_itinerary.txt"

    # --- Twilio (SMS) ---
    twilio_account_sid: SecretStr | None = None
    twilio_auth_token: SecretStr | None = None

    # --- Gmail OAuth ---
    travelbot_gmail_client_id: str = Field(default="", description="Google API client ID")
    travelbot_gmail_client_secret: SecretStr | None = None

    # --- Gmail local files ---
    credentials_dir: Path = BASE_DIR / "credentials"
    gmail_token_file: Path = credentials_dir / "token.json"
    scopes: tuple[str, ...] = ("https://www.googleapis.com/auth/gmail.readonly",)

    # --- Database (minimal: two URLs + a toggle) ---
    database_url_external: str | None = None  # public URL for local dev
    database_url_internal: str | None = None  # internal URL for Railway
    use_internal_db: bool = False  # set to true on Railway

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Convenience flags / mappings ---
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

    @property
    def database_url_sync(self) -> str | None:
        """Return the chosen sync URL (psycopg2)."""
        if self.use_internal_db and self.database_url_internal:
            return self.database_url_internal
        return self.database_url_external

    @property
    def database_url_async(self) -> str | None:
        """Return the chosen async URL (asyncpg), derived from the sync URL."""
        url = self.database_url_sync
        if not url:
            return None
        # naive but effective swap to asyncpg
        if "+psycopg2" in url:
            return url.replace("+psycopg2", "+asyncpg")
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        return url  # already async or custom


# Create a single importable instance
try:
    settings = Settings()
except ValidationError:
    # Keep startup resilient; fail later where the value is required.
    settings = Settings.model_construct()
