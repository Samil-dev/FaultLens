# Punto de entrada de la aplicación backend (FastAPI).

from fastapi import FastAPI

# Routers de la API
from app.api.health import router as health_router
from app.api.system import router as system_router
from app.api.experiment import router as experiment_router


# Instancia principal de FastAPI.
app = FastAPI(
    title="CodeTwin API",
    description="Backend API for CodeTwin + ChaosLab + AI",
    version="0.1.0"
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