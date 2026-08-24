from fastapi import APIRouter


router = APIRouter(
    prefix="/api/ai",
    tags=["AI Intelligence"],
)


@router.get("/status")
def get_ai_status():
    """
    Estado básico del motor AI de QMI.

    Foundation endpoint: confirma que la capa AI está registrada
    y disponible. Más adelante podrá exponer modelos cargados,
    última predicción, versión del motor y métricas operativas.
    """
    return {
        "status": "operational",
        "engine": "QMI AI Engine",
        "version": "foundation",
        "models_loaded": False,
    }
