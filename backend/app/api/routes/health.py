"""
Health-check API route for Quantum Market Intelligence.
"""

from fastapi import APIRouter

from app.core.settings import settings
from app.responses import success_response
from app.schemas.response_schema import (
    HealthApiResponse,
    HealthData,
)


router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthApiResponse,
    summary="Get API Health",
    description=(
        "Return the current health state and basic runtime information "
        "for the Quantum Market Intelligence backend."
    ),
)
def health() -> HealthApiResponse:
    """
    Return the current backend health status.
    """

    health_data = HealthData(
        status="ok",
        application=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    response = success_response(health_data)

    return HealthApiResponse.model_validate(
        response.model_dump()
    )