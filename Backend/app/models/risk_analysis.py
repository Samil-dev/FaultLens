from typing import Literal

from pydantic import BaseModel, Field


class RiskAnalysis(BaseModel):
    # Nivel general de riesgo.
    level: Literal[
        "low",
        "moderate",
        "high",
        "critical"
    ] = Field(
        ...,
        description="Overall risk level"
    )

    # Explicación determinista del riesgo.
    reason: str = Field(
        ...,
        description="Reason behind the risk classification"
    )