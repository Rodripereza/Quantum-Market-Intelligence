from fastapi import APIRouter

from app.exceptions import QMIException

router = APIRouter(tags=["Testing"])


@router.get("/api/test/error")
def test_error():
    raise QMIException(
        code="TEST_ERROR",
        message="Global Exception Handler is working.",
        status_code=400,
    )