from pydantic import BaseModel, Field

from app.models.simulation_event import SimulationEvent
from app.models.simulation_run import SimulationRun
from app.models.metric_comparison import MetricComparison
from app.models.resilience_score import ResilienceScore

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

    #Impacto medido antes y despues del experimento.
    comparisons: list[MetricComparison] = Field(
        default_factory=list,
        description="Metric comparisons produced by the experiment"
    )

    resilience_score: ResilienceScore = Field(
        ...,
        description="Overall resilience score for the experiment"
    )

    