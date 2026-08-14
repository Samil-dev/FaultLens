from app.analysis.impact_analyzer import ImpactAnalyzer
from app.analysis.recommendation_engine import RecommendationEngine
from app.analysis.recovery_analyzer import RecoveryAnalyzer
from app.models.experiment import Experiment
from app.models.metric_comparison import MetricComparison
from app.models.resilience_analysis import ResilienceAnalysis
from app.models.resilience_score import ResilienceScore
from app.models.simulation_run import SimulationRun
from app.models.risk_analysis import RiskAnalysis


class ResilienceAnalyzer:
    """
    Orchestrates the complete resilience analysis.
    """

    def __init__(self):
        self.impact_analyzer = ImpactAnalyzer()
        self.recovery_analyzer = RecoveryAnalyzer()
        self.recommendation_engine = RecommendationEngine()

    def analyze(
        self,
        experiment: Experiment,
        run: SimulationRun,
        comparisons: list[MetricComparison],
        score: ResilienceScore,
        total_nodes: int
    ) -> ResilienceAnalysis:
        """
        Produces the complete resilience analysis.
        """

        impact = self.impact_analyzer.analyze(
            experiment=experiment,
            run=run,
            comparisons=comparisons,
            total_nodes=total_nodes,
        )

        recovery = self.recovery_analyzer.analyze(run)

        risk_level, risk_reason = self._calculate_risk(
            impact=impact,
            recovery=recovery,
            score=score,
        )

        recommendations = self.recommendation_engine.generate(
            experiment=experiment,
            impact=impact,
            recovery=recovery,
            score=score,
        )

        risk = RiskAnalysis(
            level=risk_level,
            reason=risk_reason,
        )

        return ResilienceAnalysis(
            impact=impact,
            recovery=recovery,
            risk=risk,
            recommendations=recommendations,
        )

    def _calculate_risk(
        self,
        impact,
        recovery,
        score: ResilienceScore
    ) -> tuple[str, str]:
        """
        Calculates a deterministic risk classification.
        """

        if score.score < 20:
            return (
                "critical",
                "The system showed severe degradation and poor resilience."
            )

        if recovery.failed_recoveries:
            return (
                "critical",
                "One or more affected nodes failed to recover."
            )

        if impact.blast_radius >= 0.75:
            return (
                "critical",
                "A large majority of the system was affected."
            )

        if score.score < 40:
            return (
                "high",
                "The system showed significant resilience weaknesses."
            )

        if impact.blast_radius >= 0.5:
            return (
                "high",
                "Failure propagated across a significant portion of the system."
            )

        if recovery.max_recovery_seconds > 15:
            return (
                "high",
                "Recovery time exceeded the expected threshold."
            )

        if score.score < 60:
            return (
                "moderate",
                "The system experienced noticeable degradation."
            )

        return (
            "low",
            "The system maintained acceptable resilience during the experiment."
        )