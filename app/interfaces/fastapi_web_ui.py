"""
FastAPI interface for TravelRoboto.

Provides the application factory used by Uvicorn's --factory mode and wires in
operational concerns required for production:

- Request correlation: propagate `X-Request-ID` via ContextVar so logs across
  async boundaries can be traced to a single request.
- Access timing: emit lightweight per-request logs (method/path/status/duration).
- Exception policy: standardized JSON envelopes for 422/500 with correlation IDs.
- Static assets + Jinja2 templates for the minimal chat UI.

Root logger configuration (handlers/formatters/levels) is owned by app/main.py.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import FastAPI, APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.status import (
    HTTP_200_OK,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.chatbot.conversation import get_chat_response
from app.logging_utils import (
    get_logger,
    new_request_id,
    set_request_id,
    get_request_id,
    log_with_id,
)

logger = get_logger(__name__)


class ChatRequest(BaseModel):
    """Request payload for the /chat endpoint."""
    message: str


# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------

def _register_middlewares(app: FastAPI) -> None:
    """Register request correlation and access-timing middleware."""
    
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        """Propagate a correlation ID for the lifetime of the request."""
        rid = request.headers.get("X-Request-ID") or new_request_id()
        set_request_id(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            set_request_id(None)  # prevent leakage across requests

    @app.middleware("http")
    async def access_timing_middleware(request: Request, call_next):
        """Emit a single, concise access log (method/path/status/elapsed_ms)."""
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


# -----------------------------------------------------------------------------
# Exception handlers
# -----------------------------------------------------------------------------

def _register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers for validation and unhandled errors.

    Standardizes client responses and ensures server logs include correlation
    metadata (request_id, path, opaque error_id) for production triage.
    """
    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request: Request, exc: RequestValidationError):
        """Return a concise 422 with structured validation details.

        Logs at WARNING (client error) with the request path and error count.
        Does not log raw request bodies to avoid leaking sensitive input.
        """
        rid = get_request_id()
        errors = exc.errors()  # structured list provided by FastAPI
        log_with_id(
            logger,
            logging.WARNING,
            "Request validation failed",
            path=request.url.path,
            errors=len(errors),
        )
        payload = {
            "error": "validation_error",
            "message": "Request validation failed.",
            "request_id": rid,
            "details": errors,
        }
        return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content=payload)

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception):
        """Convert unexpected exceptions to a safe 500 JSON response.

        - Logs at ERROR with stack trace (logger.exception).
        - Includes request_id and a short error_id to correlate client reports
          with server logs.
        - Hides internal details from clients.
        """
        rid = get_request_id()
        error_id = str(uuid.uuid4())[:8]  # short ID to find the matching log line

        # logger.exception captures stack trace automatically
        logger.exception(
            "Unhandled exception",
            extra={"request_id": rid, "error_id": error_id, "path": str(request.url.path)},
        )

        payload = {
            "error": "internal_server_error",
            "message": "An unexpected error occurred.",
            "request_id": rid,
            "error_id": error_id,
        }
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content=payload)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application for the web UI.

    Returns
    -------
    FastAPI
        App instance with correlation/timing middleware, global exception
        handlers, static/template mounts, and basic routes.
    """
    app = FastAPI(title="Chatbot Web Interface")


    # ----------------------------------------------------------------------
    # Static files, templates, and routes 
    # ----------------------------------------------------------------------
    app.mount("/static", StaticFiles(directory="app/interfaces/web/static"), name="static")
    templates = Jinja2Templates(directory="app/interfaces/web/templates")

    router = APIRouter()

    @router.get("/", response_class=HTMLResponse, status_code=HTTP_200_OK)
    async def home(request: Request) -> HTMLResponse:
        """Render the chat UI."""
        return templates.TemplateResponse("chat.html", {"request": request})

    @router.post("/chat")
    async def chat_endpoint(chat_request: ChatRequest) -> JSONResponse:
        """Minimal chat endpoint.

        Avoid logging raw payloads; prefer derived/aggregated fields.
        """
        response = get_chat_response(chat_request.message)
        return JSONResponse(content={"response": response})

    @router.get("/health")
    async def health() -> dict[str, str]:
        """Liveness probe for orchestration/monitoring."""
        return {"status": "ok"}
    
    _register_middlewares(app)
    _register_exception_handlers(app)

    app.include_router(router)
    return app
