from app.analysis.resilience_analyzer import ResilienceAnalyzer
from app.models.experiment import Experiment
from app.models.metric_comparison import MetricComparison
from app.models.resilience_analysis import ResilienceAnalysis
from app.models.resilience_score import ResilienceScore
from app.models.simulation_run import SimulationRun


class ResilienceAnalysisService:
    """
    Service responsible for producing the complete resilience analysis.
    """

    def __init__(self):
        self.analyzer = ResilienceAnalyzer()

    def analyze(
        self,
        experiment: Experiment,
        run: SimulationRun,
        comparisons: list[MetricComparison],
        score: ResilienceScore,
        total_nodes: int
    ) -> ResilienceAnalysis:
        """
        Generates the complete resilience analysis.
        """

        return self.analyzer.analyze(
            experiment=experiment,
            run=run,
            comparisons=comparisons,
            score=score,
            total_nodes=total_nodes,
        )