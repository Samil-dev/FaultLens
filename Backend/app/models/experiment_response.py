from pydantic import BaseModel, Field

from app.models.simulation_event import SimulationEvent
from app.models.simulation_run import SimulationRun

class ExperimentRunData(BaseModel):
    #Resultado de la ejecucion.
    run: SimulationRun = Field(
        ...,
        description="Simulation run result"
    )

    #Eventos generados durante la simulacion.
    events: list[SimulationEvent] = Field(
        default_factory=list,
        description="Events generated during the simulation"
    )

    