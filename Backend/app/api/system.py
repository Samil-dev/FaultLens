
from app.services.system_service import create_system as create_system_service
# modelando/gemelo digital, compuesto por nodos).
from fastapi import APIRouter
# Modelo Pydantic que define la forma y validación de un "System".
from app.models.system import System

router = APIRouter(
    prefix="/api/systems",
    tags=["System"]
)


@router.post("/")
def create_system(system: System):
    system = create_system_service(system)

    return{
        "success": True,
        "data": system,
        "error": None
    }