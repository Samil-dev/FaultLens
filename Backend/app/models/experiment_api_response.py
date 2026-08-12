from typing import Optional

from pydantic import BaseModel, Field

from app.models.experiment_response import ExperimentRunData
from app.models.api_response import ApiError

class ExperimentApiResponse(BaseModel):
    #Indica si la ejecucion fue exitosa.
    succes: bool = Field(
        ...,
        description="Wether the experiment execution was successful"
    )

    #Resultado de la ejecucion.
    data: Optional[ExperimentRunData] = Field(
        default=None,
        description="Experiment execution result"
    )

    #Informacion del error, si ocurrio.
    error: Optional[ApiError] = Field(
        default=None,
        description="Error information"
    )

    