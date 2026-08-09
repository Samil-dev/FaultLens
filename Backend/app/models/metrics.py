from datetime import datetime, timezone

from pydantic import BaseModel, Field

class Metrics(BaseModel):

    #Identificador del nodo al que pertenecen estas metricas.
    node_id: str = Field(
        ...,
        description="Identifier of the node being measured"
    )

    #Porcentaje de utilizacion de CPU.
    cpu_usage: float = Field(
        ...,
        ge=0,
        le=100,
        description="CPU usage percentage"
    )

    #Porcentaje de utilizacion de memoria.
    memory_usage: float = Field(
        ...,
        ge=0,
        le=100,
        description="CPU usage percentage"
    )

    #Latencia de respuesta del nodo en milisegundos.
    latency_ms: float = Field(
        ...,
        ge=0,
        description="Node response latency in milliseconds"
    )

    #Porcentaje de solicitudes que terminan en error.
    error_rate: float = Field(
        ...,
        ge=0,
        le=100,
        description="Request error rate percentage"
    )

    #Momento en que se registraron las metricas.
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the metrics were recorded"
    )

    