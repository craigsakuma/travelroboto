from __future__ import annotations

from functools import lru_cache
from typing import Final

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import get_settings

_ENGINE: Final[Engine] = create_engine(
    get_settings().sqlalchemy_engine_url(),
    **get_settings().sqlalchemy_engine_kwargs(),
)

@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return a lazily constructed process-wide Engine (sync)."""
    return _ENGINE


def healthcheck_db() -> bool:
    """Run a trivial 'SELECT 1' to validate connectivity and credentials."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar_one()
        return result == 1
