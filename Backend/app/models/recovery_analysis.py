from pydantic import BaseModel, Field


class RecoveryAnalysis(BaseModel):
    # Número de nodos que terminaron recuperándose.
    recovered_nodes: int = Field(
        ...,
        ge=0,
        description="Number of nodes that recovered"
    )

    # Total de registros de recuperación.
    total_recovery_nodes: int = Field(
        ...,
        ge=0,
        description="Total number of recovery records"
    )

    # Tiempo promedio de recuperación.
    average_recovery_seconds: float = Field(
        ...,
        ge=0,
        description="Average recovery time in seconds"
    )

    # Tiempo máximo de recuperación.
    max_recovery_seconds: float = Field(
        ...,
        ge=0,
        description="Maximum recovery time in seconds"
    )

    # Nodos que no pudieron recuperarse.
    failed_recoveries: list[str] = Field(
        default_factory=list,
        description="Nodes that failed to recover"
    )