"""
Standard API response schemas for Quantum Market Intelligence.

All backend endpoints can use these models to return a consistent,
typed and documented response structure.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


DataT = TypeVar("DataT")


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""

    return datetime.now(timezone.utc)


class ApiMetadata(BaseModel):
    """Metadata included with every standard API response."""

    timestamp: datetime = Field(
        default_factory=utc_now,
        description="UTC timestamp when the API response was generated.",
    )
    api_version: str = Field(
        description="Current QMI backend API version.",
        examples=["1.0.0"],
    )
    request_id: str | None = Field(
        default=None,
        description="Unique request identifier when available.",
    )
    execution_time_ms: float | None = Field(
        default=None,
        ge=0,
        description="Total request execution time in milliseconds.",
    )


class ApiError(BaseModel):
    """Structured API error information."""

    code: str = Field(
        description="Stable machine-readable error code.",
        examples=["RESOURCE_NOT_FOUND"],
    )
    message: str = Field(
        description="Human-readable error description.",
    )
    details: dict[str, Any] | None = Field(
        default=None,
        description="Optional contextual error details.",
    )


class ApiResponse(BaseModel, Generic[DataT]):
    """Standard successful or failed API response."""

    success: bool = Field(
        description="Indicates whether the request completed successfully.",
    )
    data: DataT | None = Field(
        default=None,
        description="Payload returned by the endpoint.",
    )
    metadata: ApiMetadata
    errors: list[ApiError] | None = Field(
        default=None,
        description="Structured errors when the request fails.",
    )


class HealthData(BaseModel):
    """Health-check payload."""

    status: str = Field(
        description="Current backend health status.",
        examples=["ok"],
    )
    application: str = Field(
        description="Application name.",
        examples=["Quantum Market Intelligence"],
    )
    version: str = Field(
        description="Application version.",
        examples=["1.0.0"],
    )
    environment: str = Field(
        description="Active execution environment.",
        examples=["development"],
    )


class HealthApiResponse(ApiResponse[HealthData]):
    """Typed standard response for the health endpoint."""

    pass