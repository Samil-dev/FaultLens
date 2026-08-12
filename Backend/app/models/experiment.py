from typing import Literal

from pydantic import BaseModel, Field

class Experiment(BaseModel):
    #Identificador unico del experimento.
    id: str = Field(
        ...,
        description="Unique identifier of the experiment"
    )

    #Sistema sobre el que se ejecutara el experimento.
    system_id: str = Field(
        ...,
        description="Identiffier of the target system"
    )

    #Nodo que recibira la falla simulada.
    target_node: str = Field(
        ...,
        description="Identifier of the node affected by the experiment"
    )

    #Tipo de fallo que se quiere simular.
    type: Literal[
        "latency",
        "service_down",
        "traffic_spike",
        "resource_stress"
    ] = Field(
        ...,
        description="Type of chaos experiment"
    )

    #Duracion de la simulacion en segundos.
    duration_seconds: int = Field(
        ...,
        gt=0,
        description="Duration of the experiment in seconds"
    )

    