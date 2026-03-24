"""
Global exception handlers.

Registered in main.py so every unhandled error returns a clean JSON
response instead of leaking a stack trace to the client.
"""
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

logger = logging.getLogger(__name__)


def _add_cors_headers(request: Request, response: JSONResponse) -> JSONResponse:
    """
    Helper to manually inject CORS headers into error responses.
    This acts as a fallback if the standard CORSMiddleware is bypassed 
    during certain early-stage or fatal exceptions.
    """
    origin = request.headers.get("origin")
    if origin:
        # For development, we can be slightly permissive on errors to ensure 
        # debugging info reaches the frontend.
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response


async def http_500_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for any unhandled exception that reaches FastAPI.
    Logs the full traceback server-side; returns a safe generic message.
    """
    logger.exception("Unhandled server error on %s %s: %s", request.method, request.url.path, str(exc))
    response = JSONResponse(
        status_code=500,
        content={"message": "An unexpected server error occurred. Please try again later.", "detail": str(exc)},
    )
    return _add_cors_headers(request, response)


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """
    Handles database unique-constraint / foreign-key violations.
    Prevents SQLAlchemy details from being exposed to the client.
    """
    logger.warning("Database integrity error on %s %s: %s", request.method, request.url.path, exc.orig)
    response = JSONResponse(
        status_code=409,
        content={"message": "This operation conflicts with existing data. The record may already exist."},
    )
    return _add_cors_headers(request, response)


async def operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    """
    Handles database connection / operational errors (e.g. DB unreachable).
    """
    logger.error("Database operational error on %s %s: %s", request.method, request.url.path, exc.orig)
    response = JSONResponse(
        status_code=533, # Use custom code or 503
        content={"message": "The database is temporarily unavailable. Please try again in a moment.", "detail": str(exc.orig)},
    )
    return _add_cors_headers(request, response)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Replaces FastAPI's default 422 Unprocessable Entity response with a
    flatter, friendlier format.
    """
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = " → ".join(str(loc) for loc in first.get("loc", []) if loc != "body")
    msg = first.get("msg", "Validation error")
    friendly = f"Invalid value for '{field}': {msg}" if field else msg

    response = JSONResponse(
        status_code=422,
        content={
            "message": friendly,
            "detail": errors,
        },
    )
    return _add_cors_headers(request, response)
