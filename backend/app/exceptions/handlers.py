"""
Global exception handlers for Quantum Market Intelligence.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.base_exception import QMIException
from app.responses import error_response


async def qmi_exception_handler(
    request: Request,
    exc: QMIException,
) -> JSONResponse:
    """Handle controlled QMI application exceptions."""

    response = error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected application exceptions."""

    response = error_response(
        code="INTERNAL_SERVER_ERROR",
        message="Unexpected server error.",
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump(mode="json"),
    )