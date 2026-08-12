#Modelo Pydantic que representa un sistema completo.
from pydantic import BaseModel, Field,model_validator

#List se utiliza para representar los nodos del sistema.
from typing import List

#Importamos el modelo Node/
from app.models.node import Node

from app.models.dependency import Dependency


class System(BaseModel):

    #Identificador unico del sistema.
    id: str = Field(
        ...,
        description="Unique identifier of the system"
    )

    #Nombre legible del sistema.
    name: str = Field(
        ...,
        description="Human-readable system name"
    )

    #Lista de nopos que componen el sistema.
    nodes: List[Node] = Field(
        default_factory=list,
        description="Nodes that compose the system"
    )

    dependencies: List[Dependency] = Field(
        default_factory=list,
        description="Dependencies between nodes in the system"
    )

    #Valida la estructura de los nodos del sistema.
    @model_validator(mode="after")
    def validate_nodes(self):

        #Obtenemos todos los IDs de los nodos.
        node_ids = {node.id for node in self.nodes}

        #Verificamos que no existan IDs repetidos.
        if len(node_ids) != len(self.nodes):
            raise ValueError("Node Ids must be unique")

        #Validamos las dependencias explicitas del sistema.
        for dependency in self.dependencies:

            if dependency.source not in node_ids:
                raise ValueError(
                    f"Dependency source '{dependency.source}'"
                    f"does not exist in the system"
                )

            #El nodo origen debe existir.
            if dependency.source not in node_ids:
                raise ValueError(
                f"Dependecy target '{dependency.target}'"
                f"does not exist in the system"
                )

        return self