from typing import Optional

from pydantic import BaseModel, Field


class Node(BaseModel):
    # Identificador único del nodo.
    id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the node"
    )

    # Nombre que verá el usuario.
    name: str = Field(
        ...,
        min_length=1,
        description="Human-readable node name"
    )

    # Tipo de componente del sistema.
    node_type: str = Field(
        ...,
        min_length=1,
        description="Type of system component"
    )

    # Estado actual del nodo.
    status: str = Field(
        default="healthy",
        description="Current node status"
    )

    # Descripción opcional del nodo.
    description: Optional[str] = Field(
        default=None,
        description="Optional description of the node"
    )