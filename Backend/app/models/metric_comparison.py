from pydantic import BaseModel, Field

class MetricComparison(BaseModel):
    #Nodo al que pertenece la comparacion.
    node_id: str = Field(
        ...,
        description="Identifier of the node being compared"
    )

    #Diferencia absoluta de utilizacion de CPU.
    cpu_usage_delta: float = Field(
        ...,
        description="Absolute change in CPU usage"
    )

    #Diferencia absoluta de utilizacion de memoria.
    memory_usage_delta: float = Field(
        ...,
        description="Absolute change in memory usage"
    )

    #Diferencia absoluta de latencia.
    latency_delta_ms: float = Field(
        ...,
        description="Absolute change in latency in miliseconds"
    )

    #Diferencia absoluta de tasa de errores.
    error_rate_delta: float = Field(
        ...,
        description="Absolute change in error rate"
    )

