from pydantic import BaseModel, Field


class ImpactAnalysis(BaseModel):
    # Proporción del sistema afectada por el experimento.
    blast_radius: float = Field(
        ...,
        ge=0,
        le=1,
        description="Proportion of the system affected"
    )

    # Cantidad de nodos afectados.
    affected_nodes: int = Field(
        ...,
        ge=0,
        description="Number of affected nodes"
    )

    # Cantidad total de nodos.
    total_nodes: int = Field(
        ...,
        ge=0,
        description="Total number of nodes"
    )

    # Nodos considerados críticos por el análisis.
    critical_nodes: list[str] = Field(
        default_factory=list,
        description="Nodes with the highest observed impact"
    )

    # Impacto promedio de las métricas.
    average_metric_impact: float = Field(
        ...,
        ge=0,
        le=1,
        description="Average normalized metric impact"
    )