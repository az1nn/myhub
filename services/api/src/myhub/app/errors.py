from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from myhub.modules.administration.bootstrap_service import BootstrapError


def bootstrap_error_handler(request: Request, exc: BootstrapError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": str(exc), "request_id": request_id}})


def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "internal server error", "request_id": request_id}})
