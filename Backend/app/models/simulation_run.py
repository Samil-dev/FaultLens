from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.recovery import Recovery

class SimulationRun(BaseModel):
    #Identificador unico de esta ejecucion.
    id: str = Field(
        ...,
        description="Unique identifier of the simulation run"
    )

    #Experimento que origino esta ejecucion.
    experiment_id: str = Field(
        ...,
        description="Idenfier of the experiment"
    )

    #Tipo de experimento de caos ejecutado.
    type: Literal[
        "service_down",
        "latency_spike",
        "resource_exhaustion",
        "traffic_spike",
    ] = Field(
        ...,
        description="Type of chaos experiment that produced this run"
    )

    #Nodo objetivo del experimento.
    target_node: str = Field(
        ...,
        description="Identifier of the node the experiment targeted"
    )

    #Estado actual de la ejecucion.
    status: Literal[
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled"
    ] = Field(
        default="pending",
        description="Current simulation status"
    )

    #Momento en que comenzo la ejecucion.
    started_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the simulation started"
    )

    #Momento en que termino la ejecucion.
    finished_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the simulation finished"
    )

    #Nodos afectados durante la simulacion.
    affected_nodes: list[str] = Field(
        default_factory=list,
        description="IDs of nodes affected during the simulation"
    )

    #Momento en que se creo el registro de la ejecucion.
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the simulation run was created"
    )

    #Informacion sobre la recuperacion de los nodos afectados.
    recoveries: list[Recovery] =   Field(
        default_factory=list,
        description="Recovery information for affected nodes"
    )
    