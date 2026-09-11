from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from myhub.modules.administration.bootstrap_service import BootstrapError
from myhub.modules.identity.auth_service import AuthError


def _error_content(request: Request, *, code: str, message: str) -> dict[str, object]:
    request_id = getattr(request.state, "request_id", "unknown")
    return {"error": {"code": code, "message": message, "request_id": request_id}}


def bootstrap_error_handler(request: Request, exc: BootstrapError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_content(request, code=exc.code, message=str(exc)),
    )


def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_content(request, code=exc.code, message=exc.public_message),
    )


def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_error_content(
            request,
            code="INTERNAL_ERROR",
            message="internal server error",
        ),
    )
