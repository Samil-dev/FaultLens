from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "services" : "codetwin-backend"
        },
        "error": None
    }
