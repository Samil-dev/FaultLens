from typing import Literal

from pydantic import BaseModel, Field

class Recovery(BaseModel):
    #Nodo que fue afectado por el experimento.
    node_id: str = Field(
        ...,
        description="Identifier of the node being recovered"
    )

    #Estado actual de la recuperacion.
    recovery_status: Literal[
        "pending",
        "recovering",
        "recovered",
        "failed"
    ] = Field(
        default="pending",
        description="Current recovery status"
    )

    #Tiempo que tardo el nodo en recuperarse.
    recovery_time_seconds: float | None = Field(
        default=None,
        ge=0,
        description="Time required for the node to recover in seconds"
    )