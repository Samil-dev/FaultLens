from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

class SimulationEvent(BaseModel):
    #Identificador unico del evento.
    id: str = Field(
        ...,
        description="Unique identifier of the simulation event"
    )

    #Ejecucion de simulacion a la que pertenece.
    run_id: str = Field(
        ...,
        description="Identifier of the simulation run"
    )

    #Nodo relacionado con el evento.
    node_id: str = Field(
        ...,
        description="Identifier of the affected node"
    )

    #Tipo de evento ocurrido.
    event_type: Literal[
        "failure_injected",
        "node_degraded",
        "node_failed",
        "node_recovered"
    ] = Field(
        ...,
        description="Type of simulation event"
    )

    #Severidad del evento.
    severity: float = Field(
        ...,
        ge=0,
        le=1,
        description="Event severity from 0.0 to 1.0"
    )

    #Momento en que ocurrio el evento.
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the event occurred"
    )  