from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base application error with a stable code + HTTP status."""

    def __init__(self, message: str, code: str = "APP_ERROR", http_status: int = 400, details: Any = None):
        self.message = message
        self.code = code
        self.http_status = http_status
        self.details = details
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND", details: Any = None):
        super().__init__(message, code, status.HTTP_404_NOT_FOUND, details)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", code: str = "CONFLICT", details: Any = None):
        super().__init__(message, code, status.HTTP_409_CONFLICT, details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required", code: str = "UNAUTHORIZED", details: Any = None):
        super().__init__(message, code, status.HTTP_401_UNAUTHORIZED, details)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", code: str = "FORBIDDEN", details: Any = None):
        super().__init__(message, code, status.HTTP_403_FORBIDDEN, details)


class BadRequestError(AppError):
    def __init__(self, message: str = "Bad request", code: str = "BAD_REQUEST", details: Any = None):
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST, details)


class RateLimitExceededError(AppError):
    def __init__(self, message: str = "Too many requests", code: str = "RATE_LIMITED", details: Any = None):
        super().__init__(message, code, status.HTTP_429_TOO_MANY_REQUESTS, details)


def _error_response(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    body: Dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.http_status, exc.code, exc.message, exc.details)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details: list[dict] = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
            details.append({"field": loc or "body", "message": err.get("msg"), "type": err.get("type")})
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Request validation failed",
            details,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        import logging

        logging.getLogger("app").exception("Unhandled exception: %s", exc)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR",
            "Internal server error",
        )
