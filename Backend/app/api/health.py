from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "succes": True,
        "data": {
            "status": "healthy",
            "services" : "codetwin-backend"
        },
        "error": None
    }
