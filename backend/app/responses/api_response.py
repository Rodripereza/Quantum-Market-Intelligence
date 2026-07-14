"""
Response factories for Quantum Market Intelligence.

These helpers centralize the creation of standard API responses.
"""

from __future__ import annotations

from typing import Any, TypeVar

from app.core.settings import settings
from app.schemas.response_schema import (
    ApiError,
    ApiMetadata,
    ApiResponse,
)


DataT = TypeVar("DataT")


def success_response(
    data: DataT,
    *,
    request_id: str | None = None,
    execution_time_ms: float | None = None,
) -> ApiResponse[DataT]:
    """
    Build a successful standard API response.

    Parameters
    ----------
    data:
        Endpoint payload.
    request_id:
        Optional request identifier.
    execution_time_ms:
        Optional total request execution time.

    Returns
    -------
    ApiResponse
        Standard successful API response.
    """

    return ApiResponse[DataT](
        success=True,
        data=data,
        metadata=ApiMetadata(
            api_version=settings.app_version,
            request_id=request_id,
            execution_time_ms=execution_time_ms,
        ),
        errors=None,
    )


def error_response(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
    execution_time_ms: float | None = None,
) -> ApiResponse[Any]:
    """
    Build a failed standard API response.
    """

    return ApiResponse[Any](
        success=False,
        data=None,
        metadata=ApiMetadata(
            api_version=settings.app_version,
            request_id=request_id,
            execution_time_ms=execution_time_ms,
        ),
        errors=[
            ApiError(
                code=code,
                message=message,
                details=details,
            )
        ],
    )