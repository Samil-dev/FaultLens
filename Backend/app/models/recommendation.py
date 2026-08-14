from typing import Literal

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    # Título corto de la recomendación.
    title: str = Field(
        ...,
        description="Recommendation title"
    )

    # Explicación de la recomendación.
    description: str = Field(
        ...,
        description="Recommendation description"
    )

    # Prioridad de implementación.
    priority: Literal[
        "low",
        "medium",
        "high"
    ] = Field(
        ...,
        description="Recommendation priority"
    )