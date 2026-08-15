
from app.services.system_service import create_system as create_system_service
# modelando/gemelo digital, compuesto por nodos).
from fastapi import APIRouter
# Modelo Pydantic que define la forma y validación de un "System".
from app.models.system import System
from app.services.persistence_service import PersistenceService

router = APIRouter(
    prefix="/api/systems",
    tags=["System"]
)


@router.post("/")
def create_system(system: System):
    system = create_system_service(system)
    PersistenceService().save_system(system)

    return{
        "success": True,
        "data": system,
        "error": None
    }


@router.get("/", response_model=list[System])
def list_systems():
    return PersistenceService().list_systems()
