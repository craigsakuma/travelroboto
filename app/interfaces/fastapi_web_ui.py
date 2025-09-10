"""
FastAPI web UI.

This module exposes the application factory used by Uvicorn's --factory mode
and wires in cross-cutting concerns needed in production:

- Correlation IDs: per-request `X-Request-ID` propagated via ContextVar so logs
  can be traced end-to-end across async boundaries.
- Access timing: lightweight request access logs with duration, status, and path.
- Static assets and Jinja2 templates for the minimal HTML chat interface.
- Minimal JSON endpoints for health and chat.

Notes:
- Logging formatters may rely on `%(request_id)s)`; the Request-ID middleware
  ensures the ContextVar is set for the duration of the request and cleared after.
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.chatbot.conversation import get_chat_response
from app.logging_utils import (
    get_logger,
    new_request_id,
    set_request_id,
    log_with_id,
)

logger = get_logger(__name__)


class ChatRequest(BaseModel):
    """Request schema for the chat endpoint.

    Attributes
    ----------
    message : str
        Free-form user input forwarded to the chatbot pipeline.
    """
    message: str


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        A fully configured application instance, including middleware for
        correlation IDs and access timing, static/template mounts, and routes.

    Design
    ------
    - Keeps logging/correlation concerns in middleware to avoid polluting
      endpoint code with boilerplate.
    - Mounts static/template paths relative to the repository layout
      (app/interfaces/web/{static,templates}).
    """
    app = FastAPI(title="Chatbot Web Interface")

    # -------------------------------
    # Request-ID middleware
    # -------------------------------
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        """Attach a correlation ID to the request lifecycle.

        Behavior
        --------
        - If the client supplies `X-Request-ID`, use it; otherwise generate a
          UUID4.
        - Set the value in a ContextVar so downstream logs include the same ID.
        - Echo `X-Request-ID` on the response for client/server correlation.
        - Always clear the ContextVar in a `finally` block to prevent leakage
          across requests in long-lived workers.

        Parameters
        ----------
        request : fastapi.Request
            Incoming HTTP request.
        call_next : Callable[[Request], Awaitable[Response]]
            FastAPI-provided callable that advances to the next middleware/route.

        Returns
        -------
        starlette.responses.Response
            The downstream response with `X-Request-ID` header attached.
        """
        rid = request.headers.get("X-Request-ID") or new_request_id()
        set_request_id(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            # Clear for safety in long-lived worker contexts
            set_request_id(None)

    # -------------------------------
    # Access-timing middleware
    # -------------------------------
    @app.middleware("http")
    async def access_timing_middleware(request: Request, call_next):
        """Emit a concise access log for each request (method, path, status, ms).

        This middleware is intentionally lightweight and independent of any
        access-log middleware that a server (e.g., Uvicorn) may provide so that
        application-layer logs always include the same correlation ID and fields.

        Parameters
        ----------
        request : fastapi.Request
            Incoming HTTP request.
        call_next : Callable[[Request], Awaitable[Response]]
            FastAPI-provided callable that advances to the next middleware/route.

        Returns
        -------
        starlette.responses.Response
            The downstream response (re-raised if an exception occurs).
        """
        start = time.perf_counter()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
            status = response.status_code
            elapsed_ms = (time.perf_counter() - start) * 1000.0

            log_with_id(
                logger,
                logging.INFO,
                f"{method} {path}",
                status_code=status,
                elapsed_ms=round(elapsed_ms, 2),
            )
            return response
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            log_with_id(
                logger,
                logging.ERROR,
                f"{method} {path} raised",
                elapsed_ms=round(elapsed_ms, 2),
                exc_type=type(exc).__name__,
            )
            raise

    # Static files & templates
    # (Paths match your repo: app/interfaces/web/{static,templates})
    app.mount(
        "/static", 
        StaticFiles(directory="app/interfaces/web/static"), 
        name="static"
    )
    templates = Jinja2Templates(directory="app/interfaces/web/templates")

    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        """Render the HTML chat UI."""
        return templates.TemplateResponse("chat.html", {"request": request})

    @router.post("/chat")
    async def chat_endpoint(chat_request: ChatRequest):
        """Chat API endpoint.

        Parameters
        ----------
        chat_request : ChatRequest
            Pydantic model containing the user message.

        Returns
        -------
        fastapi.responses.JSONResponse
            JSON payload with the chatbot's response, e.g.:
            `{ "response": "<string>" }`.
        """
        response = get_chat_response(chat_request.message)
        return JSONResponse(content={"response": response})

    @router.get("/health")
    async def health():
        """Liveness probe endpoint for orchestration/health checks."""
        return {"status": "ok"}

    app.include_router(router)
    return app
