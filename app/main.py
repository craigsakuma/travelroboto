"""
App entrypoint.

- Primary: expose create_app() for Uvicorn (--factory) in all environments.
- Convenience: allow `python -m app.main` for local runs, honoring $PORT.
"""
from app.interfaces.fastapi_web_ui import create_app

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:create_app", factory=True, host="0.0.0.0", port=port)