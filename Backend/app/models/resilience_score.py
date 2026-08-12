from pydantic import BaseModel, Field


class ResilienceScore(BaseModel):
    # Puntuación global de resiliencia.
    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall resilience score from 0 to 100"
    )

    # Clasificación legible del resultado.
    rating: str = Field(
        ...,
        description="Human-readable resilience rating"
    )

    # Cantidad de nodos afectados.
    affected_nodes: int = Field(
        ...,
        ge=0,
        description="Number of affected nodes"
    )

    # Cantidad total de nodos del sistema.
    total_nodes: int = Field(
        ...,
        ge=0,
        description="Total number of nodes in the system"
    )