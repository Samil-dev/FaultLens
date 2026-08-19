# Punto de entrada de la aplicación backend (FastAPI).

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Routers de la API
from app.api.health import router as health_router
from app.api.system import router as system_router
from app.api.experiment import router as experiment_router
from app.api.mcp_status import router as mcp_status_router
from app.services.demo_system import build_demo_system
from app.services.persistence_service import PersistenceService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed the demo Digital Twin on first run so GET /api/systems is never
    # empty out of the box. Only seeds when no system has been persisted yet,
    # so it never overwrites real user data on subsequent restarts.
    persistence = PersistenceService()
    if not persistence.list_systems():
        persistence.save_system(build_demo_system())
    yield


# Instancia principal de FastAPI.
app = FastAPI(
    title="FaultLens API",
    description="Backend API for FaultLens — Chaos Engineering & Resilience Intelligence",
    version="0.2.0",
    lifespan=lifespan,
)


# ── Exception handlers ──────────────────────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": str(exc)},
            "data": None,
        },
    )


@app.exception_handler(NotImplementedError)
async def not_implemented_handler(request: Request, exc: NotImplementedError) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={
            "success": False,
            "error": {"code": "NOT_IMPLEMENTED", "message": str(exc)},
            "data": None,
        },
    )


# =========================
# API ROUTERS
# =========================

# Health Check
app.include_router(
    health_router,
    prefix="/api"
)

# System
app.include_router(
    system_router
)

app.include_router(
    experiment_router
)

app.include_router(
    mcp_status_router
)