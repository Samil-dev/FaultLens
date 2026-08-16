from typing import Literal, Optional

from pydantic import BaseModel, Field


class SuggestedExperiment(BaseModel):
    #Tipo de experimento sugerido.
    type: Literal[
        "service_down",
        "latency_spike",
        "resource_exhaustion",
        "traffic_spike",
    ] = Field(
        ...,
        description="Type of chaos experiment suggested"
    )

    #Nodo objetivo sugerido.
    target_node: str = Field(
        ...,
        description="Identifier of the node the suggested experiment should target"
    )

    #Duracion sugerida en segundos.
    duration_seconds: int = Field(
        ...,
        ge=0,
        description="Suggested duration of the experiment in seconds"
    )


class NextExperimentSuggestion(BaseModel):
    #Categoria de la recomendacion.
    recommendation_type: Literal[
        "recovery_validation",
        "critical_dependency",
        "high_risk_follow_up",
        "no_immediate_follow_up",
    ] = Field(
        ...,
        description="Category of the follow-up recommendation"
    )

    #Experimento sugerido, si existe uno concreto.
    suggested_experiment: Optional[SuggestedExperiment] = Field(
        default=None,
        description="Concrete follow-up experiment to run, if one could be determined"
    )

    #Motivo determinista de la recomendacion.
    reason: str = Field(
        ...,
        description="Deterministic explanation behind the recommendation"
    )

    #Nivel de riesgo observado en el analisis original.
    risk_level: str = Field(
        ...,
        description="Risk level from the resilience analysis that produced this suggestion"
    )
