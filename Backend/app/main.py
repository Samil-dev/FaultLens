# Punto de entrada de la aplicación backend (FastAPI).

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Routers de la API
from app.api.health import router as health_router
from app.api.system import router as system_router
from app.api.experiment import router as experiment_router


# Instancia principal de FastAPI.
app = FastAPI(
    title="FaultLens API",
    description="Backend API for FaultLens — Chaos Engineering & Resilience Intelligence",
    version="0.2.0"
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