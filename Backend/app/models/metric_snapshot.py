from datetime import datetime, timezone

from pydantic import BaseModel, Field

class MetricSnapshot(BaseModel):

    #Identificador del nodo al que pertence la captura.
    node_id: str = Field(
        ...,
        description="Identifier of the node"
    )

    #Metricas registradas en el momento de la captura.
    metrics: dict[str, float] = Field(
        ...,
        description="Metrics values capture at a specific point in time."
    )

    #Momento exacto de la captura.
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the metric snapshot"
    )