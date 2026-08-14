from app.models.experiment import Experiment
from app.models.impact_analysis import ImpactAnalysis
from app.models.recommendation import Recommendation
from app.models.recovery_analysis import RecoveryAnalysis
from app.models.resilience_score import ResilienceScore


class RecommendationEngine:
    """
    Generates deterministic resilience recommendations.
    """

    def generate(
        self,
        experiment: Experiment,
        impact: ImpactAnalysis,
        recovery: RecoveryAnalysis,
        score: ResilienceScore
    ) -> list[Recommendation]:
        """
        Generates recommendations based on the observed results.
        """

        recommendations: list[Recommendation] = []

        if impact.blast_radius >= 0.5:
            recommendations.append(
                Recommendation(
                    title="Reduce failure blast radius",
                    description=(
                        "A large portion of the system was affected by "
                        "a single node failure. Introduce isolation, "
                        "redundancy, or fallback mechanisms."
                    ),
                    priority="high",
                )
            )

        if experiment.target_node in impact.critical_nodes:
            recommendations.append(
                Recommendation(
                    title="Strengthen target node resilience",
                    description=(
                        f"The target node '{experiment.target_node}' "
                        "produced significant impact during the experiment. "
                        "Consider redundancy and failover strategies."
                    ),
                    priority="high",
                )
            )

        if impact.average_metric_impact >= 0.5:
            recommendations.append(
                Recommendation(
                    title="Reduce metric degradation",
                    description=(
                        "The experiment produced significant changes in "
                        "system performance metrics. Review capacity, "
                        "timeouts, and fallback behavior."
                    ),
                    priority="high",
                )
            )

        if recovery.max_recovery_seconds > 15:
            recommendations.append(
                Recommendation(
                    title="Improve recovery time",
                    description=(
                        "At least one affected node required significant "
                        "time to recover. Improve automated recovery and "
                        "failover procedures."
                    ),
                    priority="medium",
                )
            )

        if recovery.failed_recoveries:
            recommendations.append(
                Recommendation(
                    title="Fix failed recovery paths",
                    description=(
                        "Some affected nodes did not recover successfully. "
                        "Review recovery workflows and redundancy."
                    ),
                    priority="high",
                )
            )

        if score.score < 40:
            recommendations.append(
                Recommendation(
                    title="Prioritize resilience improvements",
                    description=(
                        "The overall resilience score is poor. "
                        "The system should receive immediate resilience "
                        "hardening before production use."
                    ),
                    priority="high",
                )
            )

        if not recommendations:
            recommendations.append(
                Recommendation(
                    title="Maintain current resilience controls",
                    description=(
                        "The experiment produced limited impact and "
                        "acceptable recovery behavior."
                    ),
                    priority="low",
                )
            )

        return recommendations