import logging
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            details=details,
        )


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationError(AppException):
    def __init__(
        self, message: str = "Authentication required", details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            details=details,
        )


class RateLimitExceededError(AppException):
    def __init__(self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
            details=details,
        )


class AIProviderError(AppException):
    def __init__(
        self, message: str = "AI inference provider failed", details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="AI_PROVIDER_ERROR",
            details=details,
        )


async def app_exception_handler(request: Request, exc: Any) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
    code = getattr(exc, "code", "INTERNAL_ERROR")
    message = getattr(exc, "message", str(exc))
    details = getattr(exc, "details", {})
    logger.warning(f"[{request_id}] AppException: {code} - {message} (status: {status_code})")
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id,
            },
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please try again later.",
                "request_id": request_id,
            },
        },
    )
