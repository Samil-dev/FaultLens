from pydantic import BaseModel, Field

from app.models.metric_comparison import MetricComparison
from app.models.resilience_analysis import ResilienceAnalysis
from app.models.resilience_score import ResilienceScore
from app.models.simulation_event import SimulationEvent
from app.models.simulation_run import SimulationRun
from app.models.ai_analysis import AIAnalysis


class ExperimentRunData(BaseModel):
    # Resultado de la ejecución.
    run: SimulationRun = Field(
        ...,
        description="Simulation run result"
    )

    # Eventos generados durante la simulación.
    events: list[SimulationEvent] = Field(
        default_factory=list,
        description="Events generated during the simulation"
    )

    # Impacto medido antes y después del experimento.
    comparisons: list[MetricComparison] = Field(
        default_factory=list,
        description="Metric comparisons produced by the experiment"
    )

    # Puntuación global de resiliencia.
    resilience_score: ResilienceScore = Field(
        ...,
        description="Overall resilience score for the experiment"
    )

    # Análisis completo de resiliencia.
    analysis: ResilienceAnalysis = Field(
        ...,
        description="Complete resilience analysis"
    )

    ai_analysis: AIAnalysis = Field(
        ...,
        description="AI-assisted interpretation of the resilience analysis"
    )