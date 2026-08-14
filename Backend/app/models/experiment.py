from typing import Literal

from pydantic import BaseModel, Field


class Experiment(BaseModel):
    """
    Represents a chaos experiment to be executed against a system.
    """

    # Identificador único del experimento.
    id: str = Field(
        ...,
        description="Unique identifier of the experiment"
    )

    # Sistema sobre el cual se ejecutará.
    system_id: str = Field(
        ...,
        description="Identifier of the target system"
    )

    # Nodo que será afectado por el experimento.
    target_node: str = Field(
        ...,
        description="Identifier of the node affected by the experiment"
    )

    # Tipo de experimento de caos.
    type: Literal[
        "latency",
        "service_down",
        "traffic_spike"
    ] = Field(
        ...,
        description="Type of chaos experiment"
    )

    # Duración del experimento en segundos.
    duration_seconds: int = Field(
        ...,
        ge=0,
        description="Duration of the experiment in seconds"
    )