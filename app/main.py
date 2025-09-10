"""
App entrypoint.

- Primary: expose create_app() for Uvicorn (--factory) in all environments.
- Convenience: allow `python -m app.main` for local runs, honoring $PORT.

This module also configures the root logger with:
- A formatter that includes %(request_id)s for correlation
- A RequestIdFilter that injects request_id on every record
- The log level sourced from settings.log_level
"""
from __future__ import annotations

import logging
import sys

from app.config import settings
from app.interfaces.fastapi_web_ui import create_app
from app.logging_utils import RequestIdFilter


def configure_logging() -> None:
    """
    Configure the root logger with a request_id-aware formatter and filter.

    The RequestIdFilter injects `request_id` into each LogRecord so the formatter
    can safely use %(request_id)s even if no request scope is active (defaults to "-").
    """
    # Resolve level from settings (fallback to INFO).
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Build a formatter that includes request_id.
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Stream logs to stdout (good for Railway and containerized runtimes).
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    # Install on the root logger.
    root = logging.getLogger()
    root.handlers.clear()          # avoid duplicate handlers in reloads
    root.setLevel(level)
    root.addHandler(handler)


# Configure logging at import time so it's ready for the factory `create_app`.
configure_logging()


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", "8000"))

    # Note: We still pass uvicorn's log_level to keep its own loggers consistent.
    # Your app's loggers are already configured by configure_logging().
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=port,
        log_level=settings.log_level.lower(),
    )
