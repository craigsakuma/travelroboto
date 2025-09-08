"""
App entrypoint.

- Primary: expose create_app() for Uvicorn (--factory) in all environments.
- Convenience: allow `python -m app.main` for local runs, honoring $PORT.
"""
import logging, sys

from app.config import settings
from app.interfaces.fastapi_web_ui import create_app

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app.main:create_app", 
        factory=True, 
        host="0.0.0.0", 
        port=port,
        log_level=settings.log_level.lower(),
    )