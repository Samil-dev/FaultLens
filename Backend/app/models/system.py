#Modelo Pydantic que representa un sistema completo.
from pydantic import BaseModel, Field,model_validator

#List se utiliza para representar los nodos del sistema.
from typing import List

#Importamos el modelo Node/
from app.models.node import Node


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

    #Valida la estructura de los nodos del sistema.
    @model_validator(mode="after")
    def validate_nodes(self):

        #Obtenemos todos los IDs de los nodos.
        node_ids = [node.id for node in self.nodes]

        #Verificamos que no existan IDs repetidos.
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Node Ids must be unique")
        
    #Verificamos que todas las dependencias existan.
        for node in self.nodes:
            for dependency in node.depends_on:
                if dependency not in node_ids:
                    raise ValueError(
                        f"Node '{node.id}' depends on unknown node '{dependency}'" 
                    )
        return self