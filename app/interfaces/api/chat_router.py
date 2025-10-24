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

import inspect
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.responses import FileResponse, Response
from starlette.status import (
    HTTP_200_OK,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.chatbot.conversation import get_chat_response
from app.config import settings
from app.logging_utils import (
    get_logger,
    get_request_id,
    log_context,
    log_with_id,
    new_request_id,
    set_request_id,
    truncate_msg,
)

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

logger = get_logger(__name__)

# Routers: HTML under "/", JSON under "/api".
web_router = APIRouter()
api_router = APIRouter(prefix="/api")

FAVICON_PATH: Path = settings.favicon_path
WEBMANIFEST_PATH: Path = settings.webmanifest_path

IS_PROD = settings.app_env == "production"

CACHE_ONE_YEAR = "public, max-age=31536000, immutable"
CACHE_ONE_DAY = "public, max-age=86400"
NO_STORE = "no-store"

FAVICON_HEADERS: dict[str, str] = (
    {"Cache-Control": CACHE_ONE_YEAR} if IS_PROD else {"Cache-Control": NO_STORE}
)
MANIFEST_HEADERS: dict[str, str] = (
    {"Cache-Control": CACHE_ONE_DAY} if IS_PROD else {"Cache-Control": NO_STORE}
)

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Request payload for the /chat endpoint."""

    message: str


# -----------------------------------------------------------------------------
# Web (HTML) routes
# -----------------------------------------------------------------------------


@web_router.get("/", response_class=HTMLResponse, status_code=HTTP_200_OK)
async def home(request: Request) -> HTMLResponse:
    """Render the chat UI; client JS hits `/api/chat` for responses."""
    with log_context(logger, "render_home"):
        templates: Jinja2Templates = request.app.state.templates  # app-scoped
        return templates.TemplateResponse("chat.html", {"request": request})


@web_router.get("/favicon.ico", include_in_schema=False)
async def favicon_ico() -> Response:
    """Serve /favicon.ico or 204 if missing."""
    if FAVICON_PATH.exists():
        # Optional caching:
        # return FileResponse(FAVICON_PATH, headers={"Cache-Control": "public, max-age=31536000"})
        return FileResponse(FAVICON_PATH, headers=FAVICON_HEADERS)
    return Response(status_code=204)


@web_router.get("/site.webmanifest", include_in_schema=False)
async def site_webmanifest() -> Response:
    """Serve PWA manifest from configured path."""
    if WEBMANIFEST_PATH.exists():
        return FileResponse(
            WEBMANIFEST_PATH, media_type="application/manifest+json", headers=MANIFEST_HEADERS
        )
    return Response(status_code=204)


# -----------------------------------------------------------------------------
# API (JSON) routes
# -----------------------------------------------------------------------------


@api_router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe: trivial and side-effect free."""
    return {"status": "ok"}


@api_router.get("/readiness")
async def readiness() -> dict[str, str]:
    """Readiness probe: tailor to dependencies (DB/caches) as needed."""
    log_with_id(logger, logging.DEBUG, "readiness_check")
    return {"status": "ready"}


@api_router.post("/chat")
async def chat_endpoint(payload: ChatRequest) -> dict[str, Any]:
    """Thin adapter over `get_chat_response`."""
    message = payload.message.strip()
    with log_context(logger, "chat_api", input_len=len(message)):
        # Avoid logging full payloads at higher levels; short preview in DEBUG only.
        log_with_id(
            logger,
            logging.DEBUG,
            "chat_input_preview",
            preview=truncate_msg(message, 300),
        )
        result = get_chat_response(message)
        reply = await _maybe_await(result)
        log_with_id(
            logger,
            logging.DEBUG,
            "chat_reply_preview",
            preview=truncate_msg(str(reply), 300),
        )
        return {"reply": reply}


@api_router.post("/sms")
async def sms_webhook(request: Request) -> dict[str, Any]:
    """Vendor-agnostic SMS webhook: accepts JSON or form data, returns JSON."""
    with log_context(logger, "sms_webhook"):
        message = await _extract_message(request)
        log_with_id(
            logger,
            logging.DEBUG,
            "sms_input_preview",
            preview=truncate_msg(message, 300),
        )
        result = get_chat_response(message)
        reply = await _maybe_await(result)
        log_with_id(
            logger,
            logging.DEBUG,
            "sms_reply_preview",
            preview=truncate_msg(str(reply), 300),
        )
        return {"reply": reply}


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
        rid = get_request_id() or new_request_id()
        errors = exc.errors()
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
        rid = get_request_id() or new_request_id()
        error_id = str(uuid.uuid4())[:8]  # short ID to find the matching log line

        # logger.exception captures stack trace automatically
        logger.exception(
            "Unhandled exception",
            extra={"error_id": error_id, "path": str(request.url.path)},
        )

        payload = {
            "error": "internal_server_error",
            "message": "An unexpected error occurred.",
            "request_id": rid,
            "error_id": error_id,
        }
        resp = JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
        resp.headers["X-Request-ID"] = rid
        return resp


# -----------------------------------------------------------------------------
# Lifespan
# -----------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Emit consistent startup/shutdown logs; keep work here lightweight."""
    with log_context(logger, "app_startup"):
        pass
    try:
        yield
    finally:
        with log_context(logger, "app_shutdown"):
            pass


# -----------------------------------------------------------------------------
# App factory
# -----------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application for the web UI.

    Returns
    -------
    FastAPI
        App instance with correlation/timing middleware, global exception
        handlers, static/template mounts, and basic routes.
    """
    app = FastAPI(
        title="Chatbot Web Interface",
        version="0.1.0",
        lifespan=lifespan,
    )

    # App-scoped Jinja environment (config-driven; easy to override in tests/sub-apps).
    app.state.templates = Jinja2Templates(directory=str(settings.templates_dir))

    # Mount static assets via configuration (supports env/test overrides).
    app.mount(
        "/static", StaticFiles(directory=str(settings.static_dir), check_dir=True), name="static"
    )

    _register_middlewares(app)
    _register_exception_handlers(app)

    # Attach routers (HTML at "/", JSON under "/api").
    app.include_router(web_router)
    app.include_router(api_router)

    return app


# -----------------------------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------------------------


async def _extract_message(request: Request) -> str:
    """Extract a text message from JSON or form-encoded requests."""
    ctype = request.headers.get("content-type", "").lower()

    # JSON body
    if "application/json" in ctype:
        data = await request.json()
        msg = (data.get("message") or data.get("body") or "").strip()
        if msg:
            return msg

    # Form body (e.g., application/x-www-form-urlencoded, multipart/form-data)
    if "application/x-www-form-urlencoded" in ctype or "multipart/form-data" in ctype:
        form = await request.form()
        value = form.get("message") or form.get("body") or form.get("Body") or ""
        if isinstance(value, UploadFile):
            content = await value.read()
            msg = content.decode('utf-8').strip()
        else:
            msg = str(value).strip()
        if msg:
            return msg

    raise HTTPException(status_code=400, detail="No message found in request payload")


async def _maybe_await(value: Any) -> Any:
    """Await `value` if awaitable; otherwise return it unchanged."""
    if inspect.isawaitable(value):
        return await value
    return value
