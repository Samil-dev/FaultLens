from pydantic import BaseModel, Field

from app.models.experiment import Experiment
from app.models.system import System

class ExperimentRequest(BaseModel):
    #Sistema sobre el que se ejecutara el experimento.
    system: System = Field(
        ...,
        description="System to simulate"
    )

    #Experimento que se ejecutara sobre el sistema.
    experiment: Experiment = Field(
        ...,
        description="Chaos experiment to execute"
    )
