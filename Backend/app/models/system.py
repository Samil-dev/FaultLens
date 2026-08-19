#Modelo Pydantic que representa un sistema completo.
from pydantic import BaseModel, Field,model_validator

#List se utiliza para representar los nodos del sistema.
from typing import List

#Importamos el modelo Node/
from app.models.node import Node

from app.models.dependency import Dependency

from app.graph.graph_validator import validate_no_cycles

class System(BaseModel):

    #Identificador unico del sistema.
    id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the system"
    )

    #Nombre legible del sistema.
    name: str = Field(
        ...,
        min_length=1,
        description="Human-readable system name"
    )

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

        #Rechazamos una arquitectura vacia: un Digital Twin sin nodos no es utilizable.
        if not self.nodes:
            raise ValueError("A system must have at least one node")

        #Obtenemos todos los IDs de los nodos.
        node_ids = {node.id for node in self.nodes}

        #Verificamos que no existan IDs repetidos.
        if len(node_ids) != len(self.nodes):
            raise ValueError("Node Ids must be unique")

        #Validamos las dependencias explicitas del sistema.
        for dependency in self.dependencies:

            #El nodo origen debe existir.
            if dependency.source not in node_ids:
                raise ValueError(
                    f"Dependency source '{dependency.source}' "
                    f"does not exist in the system"
                )

            #El nodo destino debe existir.
            if dependency.target not in node_ids:
                raise ValueError(
                    f"Dependency target '{dependency.target}' "
                    f"does not exist in the system"
                )

        dependency_pairs = [
            (dependency.source, dependency.target)
            for dependency in self.dependencies
        ]

        validate_no_cycles(
            list(node_ids),
            dependency_pairs
        )

        return self