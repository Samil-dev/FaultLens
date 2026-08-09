from fastapi import FastAPI

app = FastAPI(
    title ="CodeTwin API",
    description="Backend API fort CodeTwin + ChaosLab + AI",
    version="o.1.o"
)

from app.api.health import router as health_router

app.include_router(
    health_router,
    prefix="/api"
)

