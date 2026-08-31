from fastapi import APIRouter, HTTPException
from app.company_intelligence.nio.service import NioDeliveryService

router = APIRouter(
    prefix="/api/company-intelligence/nio",
    tags=["Company Intelligence"],
)
delivery_service = NioDeliveryService()

@router.get("/deliveries")
def get_nio_deliveries():
    """DE-CI-NIO-001.0 — NIO Delivery Intelligence."""
    try:
        return delivery_service.analyze().model_dump()
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build NIO Delivery Intelligence. {type(exc).__name__}: {exc}",
        ) from exc
