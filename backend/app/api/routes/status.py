from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["Status"])


@router.get("/api/status")
def status():
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }