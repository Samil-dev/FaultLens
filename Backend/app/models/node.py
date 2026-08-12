from typing import List, Optional

from pydantic import BaseModel, Field


class Node(BaseModel):
    # Identificador único del nodo.
    id: str = Field(
        ...,
        description="Unique identifier of the node"
    )

    # Nombre que verá el usuario.
    name: str = Field(
        ...,
        description="Human-readable node name"
    )

    # Tipo de componente del sistema.
    node_type: str = Field(
        ...,
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

        # IDs de los nodos de los que depende este nodo.
    depends_on: List[str] = Field(
        default_factory=list,
        description="IDs of nodes this node depends on"
    )