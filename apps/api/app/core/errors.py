import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("api.error")


class AppError(Exception):
    def __init__(self, *, status: int, title: str, detail: str, error_type: str) -> None:
        self.status = status
        self.title = title
        self.detail = detail
        self.error_type = error_type


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return problem_response(
        request=request,
        status=exc.status,
        title=exc.title,
        detail=exc.detail,
        error_type=exc.error_type,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = [
        {
            "field": ".".join(str(part) for part in error["loc"] if part != "body"),
            "message": error["msg"],
            "code": error["type"],
        }
        for error in exc.errors()
    ]
    return problem_response(
        request=request,
        status=422,
        title="Validation failed",
        detail="One or more fields are invalid.",
        error_type="validation-error",
        extra={"errors": fields},
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unexpected_error")
    return problem_response(
        request=request,
        status=500,
        title="Unexpected error",
        detail="The service could not complete the request.",
        error_type="internal-error",
    )


def problem_response(
    *,
    request: Request,
    status: int,
    title: str,
    detail: str,
    error_type: str,
    extra: dict | None = None,
) -> JSONResponse:
    trace_id = getattr(request.state, "request_id", None) or str(uuid4())
    content = {
        "type": f"https://errors.finanzas.local/{error_type}",
        "title": title,
        "status": status,
        "detail": detail,
        "trace_id": trace_id,
    }
    if extra:
        content.update(extra)
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content=content,
        headers={"X-Request-ID": trace_id},
    )


def register_exception_handlers(application: FastAPI) -> None:
    application.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(Exception, unexpected_error_handler)
