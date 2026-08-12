from typing import Any, Optional

from pydantic import BaseModel, Field

class ApiError(BaseModel):
    #Codigo interno del error.
    code: str = Field(
        ...,
        description="Machine-readable error code"
    )

    #Descripcion legible del error.
    message: str = Field(
        ...,
        description="Human-readable error message"
    )

class ApiResponse(BaseModel):
    #Indica si la operacion termino correctamente.
    succes: bool = Field(
        ...,
        description="Wether the operation was successful"
    )

    #Datos devueltos por la operacion.
    data: Optional[Any] = Field(
        default=None,
        description="Response data"
    )

    #Informacion del error, si existe.
    error: Optional[ApiError] = Field(
        default=None,
        description="Error information"
    )

    